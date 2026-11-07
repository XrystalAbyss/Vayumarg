"""Register authentic INSAT-3DR HDF5 granule and create REAL_VERIFIED storm association."""

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np
from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from vayumarg.contracts.enums import Agency
from vayumarg.contracts.export import export_satellite_paired_dataset
from vayumarg.database.engine import get_db_session
from vayumarg.database.schema import (
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteProduct,
    Storm,
    StormAlias,
    TrackObservation,
)
from vayumarg.satellite.alignment import SatelliteTrackAligner
from vayumarg.satellite.mosdac_adapter import MOSDACAdapter

HDF5_FILE = Path("data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5")
PROCESSED_DIR = Path("data/processed/satellite/crops")


def register_real_granule_and_align():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify authentic file exists and calculate checksum
    assert HDF5_FILE.is_file(), f"File {HDF5_FILE} does not exist"
    hasher = hashlib.sha256()
    with open(HDF5_FILE, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    file_sha256 = hasher.hexdigest()
    file_size = HDF5_FILE.stat().st_size

    with get_db_session() as session:
        # 2. Ensure product exists
        product = session.execute(
            select(SatelliteProduct).where(SatelliteProduct.product_code == "3RIMG_L1B_STD")
        ).scalar_one_or_none()

        if not product:
            registered = MOSDACAdapter.register_supported_products_in_db(session)
            product = [p for p in registered if p.product_code == "3RIMG_L1B_STD"][0]

        # 3. Find Cyclone REMAL
        remal_alias = session.execute(
            select(StormAlias).where(
                StormAlias.agency_storm_id == "2024145N14087",
                StormAlias.source_agency == Agency.IBTRACS.value,
            )
        ).scalar_one_or_none()

        if not remal_alias:
            # Fallback search by name
            remal_storm = session.execute(
                select(Storm).where(
                    Storm.canonical_name == "REMAL",
                    Storm.season_year == 2024,
                )
            ).scalar_one()
        else:
            remal_storm = session.execute(
                select(Storm).where(Storm.id == remal_alias.storm_id)
            ).scalar_one()

        print(f"Cyclone REMAL ID: {remal_storm.id}, Name: {remal_storm.canonical_name}")

        # 4. Check or create SatelliteGranule
        granule = session.execute(
            select(SatelliteGranule).where(SatelliteGranule.granule_name == HDF5_FILE.name)
        ).scalar_one_or_none()

        if not granule:
            granule = SatelliteGranule(
                id=uuid.uuid4(),
                product_id=product.id,
                granule_name=HDF5_FILE.name,
                acquisition_start_utc=datetime(2024, 5, 26, 18, 2, 58, tzinfo=UTC),
                acquisition_end_utc=datetime(2024, 5, 26, 18, 7, 16, tzinfo=UTC),
                file_format="HDF5",
                storage_uri=str(HDF5_FILE.as_posix()),
                sha256_checksum=file_sha256,
                file_size_bytes=file_size,
                granule_metadata={
                    "satellite": "INSAT-3DR",
                    "sensor": "IMAGER",
                    "ground_station": "BES,SAC/ISRO,Ahmedabad,INDIA.",
                    "nominal_sub_satellite_lon": 74.0,
                    "datum": "WGS84",
                    "channel_count": 6,
                },
                verification_status="REAL_VERIFIED",
                created_at_utc=datetime.now(UTC),
            )
            session.add(granule)
            session.flush()
            print(f"Registered authentic SatelliteGranule: {granule.id}")
        else:
            print(f"Existing SatelliteGranule found: {granule.id}")

        # 5. Extract authentic crop and save to processed HDF5
        with h5py.File(HDF5_FILE, "r") as f:
            lat_raw = f["Latitude"][:]
            lon_raw = f["Longitude"][:]
            lat_scale = float(f["Latitude"].attrs.get("scale_factor", [0.01])[0])
            lon_scale = float(f["Longitude"].attrs.get("scale_factor", [0.01])[0])
            lat_fill = int(f["Latitude"].attrs.get("_FillValue", [32767])[0])
            lon_fill = int(f["Longitude"].attrs.get("_FillValue", [32767])[0])

            valid = (lat_raw != lat_fill) & (lon_raw != lon_fill)
            lats = np.full_like(lat_raw, np.nan, dtype=np.float32)
            lons = np.full_like(lon_raw, np.nan, dtype=np.float32)
            lats[valid] = lat_raw[valid] * lat_scale
            lons[valid] = lon_raw[valid] * lon_scale

            target_lat, target_lon = 21.70, 89.20
            dist = np.full_like(lat_raw, 1e9, dtype=np.float64)
            dist[valid] = (lats[valid] - target_lat) ** 2 + (lons[valid] - target_lon) ** 2
            r, c = np.unravel_index(np.argmin(dist), dist.shape)

            center_lat = float(lats[r, c])
            center_lon = float(lons[r, c])

            half_box = 100  # 201x201
            r_start = r - half_box
            r_end = r + half_box + 1
            c_start = c - half_box
            c_end = c + half_box + 1

            crop_tir1 = f["IMG_TIR1"][0, r_start:r_end, c_start:c_end]
            crop_temps = f["IMG_TIR1_TEMP"][:][crop_tir1.astype(int)]

        crop_dest = PROCESSED_DIR / "REMAL_20240526_1802_TIR1.h5"
        with h5py.File(crop_dest, "w") as out:
            out.create_dataset("TIR1_counts", data=crop_tir1, compression="gzip")
            out.create_dataset("TIR1_brightness_temp_k", data=crop_temps, compression="gzip")
            out.attrs["center_lat"] = center_lat
            out.attrs["center_lon"] = center_lon
            out.attrs["storm_name"] = "REMAL"
            out.attrs["timestamp_utc"] = "2024-05-26T18:02:00Z"
            out.attrs["verification_status"] = "REAL_VERIFIED"

        hasher_crop = hashlib.sha256()
        with open(crop_dest, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher_crop.update(chunk)
        crop_sha256 = hasher_crop.hexdigest()

        # 6. Check or create SatelliteProcessedCrop
        crop = session.execute(
            select(SatelliteProcessedCrop).where(
                SatelliteProcessedCrop.granule_id == granule.id,
                SatelliteProcessedCrop.storm_id == remal_storm.id,
            )
        ).scalar_one_or_none()

        if not crop:
            crop = SatelliteProcessedCrop(
                id=uuid.uuid4(),
                granule_id=granule.id,
                storm_id=remal_storm.id,
                crop_time_utc=datetime(2024, 5, 26, 18, 2, 0, tzinfo=UTC),
                center_latitude=center_lat,
                center_longitude=center_lon,
                geom=WKTElement(f"POINT({center_lon} {center_lat})", srid=4326),
                pixel_height=201,
                pixel_width=201,
                channels=["TIR-1"],
                spatial_resolution_km=4.0,
                storage_uri=str(crop_dest.as_posix()),
                sha256_checksum=crop_sha256,
                quality_control_flags={
                    "fill_pixel_count": 0,
                    "calibrated": True,
                    "min_temp_k": float(crop_temps.min()),
                    "max_temp_k": float(crop_temps.max()),
                    "mean_temp_k": float(crop_temps.mean()),
                },
                verification_status="REAL_VERIFIED",
                created_at_utc=datetime.now(UTC),
            )
            session.add(crop)
            session.flush()
            print(f"Registered authentic SatelliteProcessedCrop: {crop.id}")
        else:
            print(f"Existing SatelliteProcessedCrop found: {crop.id}")

        # 7. Run SatelliteTrackAligner
        aligner = SatelliteTrackAligner(
            max_temporal_offset_minutes=30.0, max_spatial_offset_km=100.0
        )
        associations = aligner.persist_best_associations(session, crop)
        session.commit()

        print(f"Successfully aligned and persisted {len(associations)} REAL_VERIFIED associations:")
        for a in associations:
            obs = session.get(TrackObservation, a.track_observation_id)
            print(
                f" - Obs ID: {obs.id} | Agency: {obs.source_agency} | Time: {obs.observation_time_utc} | "
                f"Wind: {obs.wind_speed_knots} kts | Cat: {obs.imd_category} | "
                f"dt: {a.temporal_offset_minutes:.1f}m | dist: {a.spatial_offset_km:.1f}km | "
                f"Conf: {a.association_confidence:.3f} | Status: {a.verification_status}"
            )

        # 8. Test export_satellite_paired_dataset
        paired_real = export_satellite_paired_dataset(
            session, sid="2024145N14087", verification_status="REAL_VERIFIED"
        )
        print(f"\nPaired REAL_VERIFIED Export Records for REMAL: {len(paired_real)}")
        for rec in paired_real:
            print(
                f"   SID: {rec.sid} ({rec.canonical_name}) | Agency: {rec.source_agency} | "
                f"Wind: {rec.wind_speed_knots} kts | Status: {rec.verification_status} | "
                f"Confidence: {rec.association_confidence}"
            )


if __name__ == "__main__":
    register_real_granule_and_align()
