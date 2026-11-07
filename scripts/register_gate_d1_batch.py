"""Register Gate D1 Batch (TAUKTAE, FANI, FENGAL), extract multichannel crops, and align with tracks."""

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import (
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteProduct,
    SatelliteTrackAssociation,
    Storm,
    TrackObservation,
)
from vayumarg.satellite.alignment import calculate_haversine_distance_km
from vayumarg.satellite.crop_engine import MultiChannelCropEngine


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


BATCH_CONFIG = [
    {
        "name": "TAUKTAE",
        "season": 2021,
        "basin": "NI",
        "gid": "9293840",
        "filename": "3RIMG_16MAY2021_2358_L1B_STD_V01R00.h5",
        "product_code": "3RIMG_L1B_STD",
        "satellite": "INSAT-3DR",
        "expected_size": 301621093,
        "acq_start_utc": datetime(2021, 5, 16, 23, 58, tzinfo=UTC),
        "acq_end_utc": datetime(2021, 5, 17, 0, 27, tzinfo=UTC),
        "center_lat": 18.50,
        "center_lon": 71.50,
        "crop_filename": "TAUKTAE_20210516_2358_MULTICHANNEL.h5",
        "obs_time_utc": datetime(2021, 5, 17, 0, 0, tzinfo=UTC),
        "temporal_offset_minutes": 2.0,
        "synoptic_role": "Highest-intensity Arabian Sea anchor in Vayumarg (ESCS peak intensity)",
        "model_eligibility": {
            "general_atmospheric_research": True,
            "primary_imd_category_classification": True,
            "primary_imd_wind_intensity_regression": True,
            "agency_conditioned_jtwc_intensity": True,
            "post_landfall_weakening_analysis": False,
            "ineligibility_reasons": [],
        },
    },
    {
        "name": "FANI",
        "season": 2019,
        "basin": "NI",
        "gid": "7206464",
        "filename": "3RIMG_02MAY2019_2358_L1B_STD_V01R00.h5",
        "product_code": "3RIMG_L1B_STD",
        "satellite": "INSAT-3DR",
        "expected_size": 303911822,
        "acq_start_utc": datetime(2019, 5, 2, 23, 58, tzinfo=UTC),
        "acq_end_utc": datetime(2019, 5, 3, 0, 27, tzinfo=UTC),
        "center_lat": 19.10,
        "center_lon": 85.50,
        "crop_filename": "FANI_20190502_2358_MULTICHANNEL.h5",
        "obs_time_utc": datetime(2019, 5, 3, 0, 0, tzinfo=UTC),
        "temporal_offset_minutes": 2.0,
        "synoptic_role": "Extreme Bay of Bengal peak anchor (ESCS peak prior to Odisha landfall)",
        "model_eligibility": {
            "general_atmospheric_research": True,
            "primary_imd_category_classification": True,
            "primary_imd_wind_intensity_regression": True,
            "agency_conditioned_jtwc_intensity": True,
            "post_landfall_weakening_analysis": False,
            "ineligibility_reasons": [],
        },
    },
    {
        "name": "FENGAL",
        "season": 2024,
        "basin": "NI",
        "gid": "14687507",
        "filename": "3SIMG_29NOV2024_2330_L1B_STD_V01R00.h5",
        "product_code": "3SIMG_L1B_STD",
        "satellite": "INSAT-3DS",
        "expected_size": 429759238,
        "acq_start_utc": datetime(2024, 11, 29, 23, 30, tzinfo=UTC),
        "acq_end_utc": datetime(2024, 11, 29, 23, 59, tzinfo=UTC),
        "center_lat": 12.20,
        "center_lon": 81.20,
        "crop_filename": "FENGAL_20241129_2330_MULTICHANNEL.h5",
        "obs_time_utc": datetime(2024, 11, 30, 0, 0, tzinfo=UTC),
        "temporal_offset_minutes": 27.75,
        "synoptic_role": "Modern INSAT-3DS Cyclonic Storm anchor filling lower intensity gap (CS active stage)",
        "model_eligibility": {
            "general_atmospheric_research": True,
            "primary_imd_category_classification": True,
            "primary_imd_wind_intensity_regression": True,
            "agency_conditioned_jtwc_intensity": True,
            "post_landfall_weakening_analysis": False,
            "ineligibility_reasons": [],
        },
    },
]


def main():
    print("=" * 80)
    print("VAYUMARG MILESTONE F2.4 — GATE D1 REGISTRATION & CROP GENERATION")
    print("=" * 80)

    engine_crop = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)
    db_engine = create_engine(settings.DATABASE_URL)

    with Session(db_engine) as session:
        for cfg in BATCH_CONFIG:
            name = cfg["name"]
            granule_path = Path("data/raw/satellite/insat_real") / cfg["filename"]
            assert granule_path.is_file(), f"Granule file missing: {granule_path}"
            size = granule_path.stat().st_size
            assert size == cfg["expected_size"], (
                f"Size mismatch for {name}: {size} != {cfg['expected_size']}"
            )
            sha256 = compute_sha256(granule_path)

            print(f"\n--- Processing {name} ({cfg['filename']}) ---")
            print(f"  Granule Size: {size:,} bytes")
            print(f"  Granule SHA-256: {sha256}")

            # 1. MultiChannel Crop
            crop_res = engine_crop.extract_crop(
                granule_path,
                center_lat=cfg["center_lat"],
                center_lon=cfg["center_lon"],
                channels=["TIR-1", "WV", "TIR-2", "MIR"],
            )

            crop_dest = Path("data/processed/satellite/crops") / cfg["crop_filename"]
            crop_dest.parent.mkdir(parents=True, exist_ok=True)
            crop_sha256 = engine_crop.save_to_hdf5(crop_res, crop_dest)
            crop_size = crop_dest.stat().st_size

            print(f"  Generated Crop: {crop_dest.name}")
            print(f"    Size: {crop_size:,} bytes | SHA-256: {crop_sha256}")
            print(
                f"    Target Shape: {crop_res.target_shape} | Valid Ratio: {crop_res.qc_flags['combined_valid_ratio']:.6f}"
            )

            # 2. Database Entities
            product = session.execute(
                select(SatelliteProduct).where(SatelliteProduct.product_code == cfg["product_code"])
            ).scalar_one()

            storm = session.execute(
                select(Storm).where(
                    Storm.canonical_name.ilike(f"%{name}%"), Storm.season_year == cfg["season"]
                )
            ).scalar_one()

            existing_granule = session.execute(
                select(SatelliteGranule).where(SatelliteGranule.granule_name == cfg["filename"])
            ).scalar_one_or_none()

            if existing_granule is None:
                granule_obj = SatelliteGranule(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    granule_name=cfg["filename"],
                    acquisition_start_utc=cfg["acq_start_utc"],
                    acquisition_end_utc=cfg["acq_end_utc"],
                    file_format="HDF5",
                    storage_uri=str(granule_path).replace("\\", "/"),
                    sha256_checksum=sha256,
                    file_size_bytes=size,
                    granule_metadata={
                        "satellite": cfg["satellite"],
                        "sensor": "IMAGER",
                        "product": cfg["product_code"],
                        "channels": ["TIR-1", "WV", "TIR-2", "MIR", "VIS"],
                        "recovery_method": "FAULT_TOLERANT_HTTP_RANGE_RESUMPTION",
                        "mosdac_gid": int(cfg["gid"]),
                        "synoptic_role": cfg["synoptic_role"],
                    },
                    verification_status="REAL_VERIFIED",
                )
                session.add(granule_obj)
                session.flush()
                print(f"  Registered SatelliteGranule: {granule_obj.id}")
            else:
                granule_obj = existing_granule
                print(f"  Found existing SatelliteGranule: {granule_obj.id}")

            existing_crop = session.execute(
                select(SatelliteProcessedCrop).where(
                    SatelliteProcessedCrop.storage_uri == str(crop_dest).replace("\\", "/")
                )
            ).scalar_one_or_none()

            qc = dict(crop_res.qc_flags)
            qc["model_eligibility"] = cfg["model_eligibility"]
            qc["sensor_resolution_audit"] = {
                "TIR-1": {"native_res_km": 4.0, "delivered_res_km": 4.0, "effective_res_km": 4.0},
                "WV": {
                    "native_res_km": 8.0,
                    "delivered_res_km": 8.0,
                    "effective_res_km": 8.0,
                    "resampling_method": "bilinear",
                },
                "TIR-2": {"native_res_km": 4.0, "delivered_res_km": 4.0, "effective_res_km": 4.0},
                "MIR": {"native_res_km": 4.0, "delivered_res_km": 4.0, "effective_res_km": 4.0},
            }

            if existing_crop is None:
                crop_obj = SatelliteProcessedCrop(
                    id=uuid.uuid4(),
                    granule_id=granule_obj.id,
                    storm_id=storm.id,
                    crop_time_utc=cfg["acq_start_utc"],
                    center_latitude=cfg["center_lat"],
                    center_longitude=cfg["center_lon"],
                    pixel_height=crop_res.target_shape[0],
                    pixel_width=crop_res.target_shape[1],
                    channels=list(crop_res.channels.keys()),
                    spatial_resolution_km=4.0,
                    storage_uri=str(crop_dest).replace("\\", "/"),
                    sha256_checksum=crop_sha256,
                    quality_control_flags=qc,
                    verification_status="REAL_VERIFIED",
                )
                session.add(crop_obj)
                session.flush()
                print(f"  Registered SatelliteProcessedCrop: {crop_obj.id}")
            else:
                crop_obj = existing_crop
                crop_obj.quality_control_flags = qc
                print(f"  Found existing SatelliteProcessedCrop: {crop_obj.id}")

            # 3. Associations at obs_time_utc
            obs_list = (
                session.execute(
                    select(TrackObservation).where(
                        TrackObservation.storm_id == storm.id,
                        TrackObservation.observation_time_utc == cfg["obs_time_utc"],
                    )
                )
                .scalars()
                .all()
            )

            print(f"  Matching Track Observations at {cfg['obs_time_utc']}: {len(obs_list)}")
            for obs in obs_list:
                existing_assoc = session.execute(
                    select(SatelliteTrackAssociation).where(
                        SatelliteTrackAssociation.crop_id == crop_obj.id,
                        SatelliteTrackAssociation.track_observation_id == obs.id,
                    )
                ).scalar_one_or_none()

                if existing_assoc is None:
                    dist_km = calculate_haversine_distance_km(
                        cfg["center_lat"], cfg["center_lon"], obs.latitude, obs.longitude
                    )
                    assoc_obj = SatelliteTrackAssociation(
                        id=uuid.uuid4(),
                        crop_id=crop_obj.id,
                        track_observation_id=obs.id,
                        temporal_offset_minutes=cfg["temporal_offset_minutes"],
                        spatial_offset_km=dist_km,
                        association_confidence=0.95,
                        validation_status="VALIDATED",
                        verification_status="REAL_VERIFIED",
                        is_interpolated_track=False,
                    )
                    session.add(assoc_obj)
                    print(
                        f"    Created Association: {assoc_obj.id} -> Agency: {obs.source_agency}, Wind: {obs.wind_speed_knots} kt, dt: {cfg['temporal_offset_minutes']}m, dist: {dist_km:.2f}km"
                    )
                else:
                    print(
                        f"    Existing Association: {existing_assoc.id} -> Agency: {obs.source_agency}"
                    )

        session.commit()
        print("\nAll Gate D1 entities successfully committed to PostgreSQL database 'vayumarg'!")


if __name__ == "__main__":
    main()
