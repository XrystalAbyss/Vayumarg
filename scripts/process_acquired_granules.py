"""Automated processing and registration pipeline for authentic MOSDAC satellite granules."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import h5py
import numpy as np
from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from vayumarg.contracts.enums import (
    Agency,
)
from vayumarg.core.logging import get_logger
from vayumarg.database.engine import get_db_session
from vayumarg.database.schema import (
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteProduct,
    SatelliteTrackAssociation,
    Storm,
    TrackObservation,
)
from vayumarg.satellite.crop_engine import MultiChannelCropEngine
from vayumarg.satellite.mosdac_adapter import MOSDACAdapter

logger = get_logger("vayumarg.process_acquired_granules")

RAW_DIR = Path("data/raw/satellite/insat_real")
PROCESSED_DIR = Path("data/processed/satellite/crops")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def parse_insat_iso_time(s: str) -> datetime:
    """Parse INSAT timestamp string e.g. '26-MAY-2024T18:02:58'."""
    s_clean = s.strip().replace("b'", "").replace("'", "")
    # Format: 26-MAY-2024T18:02:58
    dt = datetime.strptime(s_clean, "%d-%b-%YT%H:%M:%S")
    return dt.replace(tzinfo=UTC)


def identify_storm(obs_time: datetime, filename: str) -> str:
    """Identify which cyclone corresponds to the observation time / filename."""
    if "MAY2024" in filename or (obs_time.year == 2024 and obs_time.month == 5):
        return "REMAL"
    if "OCT2024" in filename or (obs_time.year == 2024 and obs_time.month == 10):
        return "DANA"
    if "MAY2020" in filename or (obs_time.year == 2020 and obs_time.month == 5):
        return "AMPHAN"
    if "JUN2023" in filename or (obs_time.year == 2023 and obs_time.month == 6):
        return "BIPARJOY"
    raise ValueError(f"Cannot identify storm for granule {filename} ({obs_time})")


def process_all_raw_granules() -> list[dict]:
    """Scan RAW_DIR for authentic granules, process multi-channel crops, and register in DB."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    crop_engine = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)

    raw_files = sorted(
        [
            f
            for f in RAW_DIR.glob("*.h5")
            if not f.name.endswith(".part") and f.stat().st_size > 100 * 1024 * 1024
        ]
    )

    results = []

    with get_db_session() as session:
        # Ensure standard products are registered
        MOSDACAdapter.register_supported_products_in_db(session)

        for raw_file in raw_files:
            file_name = raw_file.name
            file_size = raw_file.stat().st_size
            sha256 = compute_sha256(raw_file)

            print(f"\nProcessing raw granule: {file_name} ({file_size / (1024 * 1024):.2f} MB)...")

            with h5py.File(raw_file, "r") as h5:
                # Read timing metadata
                t_start_raw = h5.attrs.get("Acquisition_Start_Time", b"").decode("utf-8")
                t_end_raw = h5.attrs.get("Acquisition_End_Time", b"").decode("utf-8")
                sat_name = h5.attrs.get("Satellite_Name", b"INSAT-3DR").decode("utf-8")
                sensor_name = h5.attrs.get("Sensor_Name", b"IMAGER").decode("utf-8")

            t_start = parse_insat_iso_time(t_start_raw)
            t_end = parse_insat_iso_time(t_end_raw)
            obs_approx_time = t_start + (t_end - t_start) / 2

            storm_name = identify_storm(obs_approx_time, file_name)
            print(
                f" -> Granule {file_name}: Satellite={sat_name}, Time={obs_approx_time.isoformat()}, Storm={storm_name}"
            )

            # 1. Product mapping
            prod_code = (
                "3SIMG_L1B_STD" if "3SIMG" in file_name or "3DS" in sat_name else "3RIMG_L1B_STD"
            )
            product = session.execute(
                select(SatelliteProduct).where(SatelliteProduct.product_code == prod_code)
            ).scalar_one()

            # 2. Granule registration (idempotent)
            granule = session.execute(
                select(SatelliteGranule).where(SatelliteGranule.granule_name == file_name)
            ).scalar_one_or_none()

            if not granule:
                granule = SatelliteGranule(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    granule_name=file_name,
                    acquisition_start_utc=t_start,
                    acquisition_end_utc=t_end,
                    file_format="HDF5",
                    storage_uri=str(raw_file.as_posix()),
                    sha256_checksum=sha256,
                    file_size_bytes=file_size,
                    granule_metadata={
                        "satellite": sat_name,
                        "sensor": sensor_name,
                        "nominal_sub_satellite_lon": 74.0,
                        "raw_sha256": sha256,
                    },
                    verification_status="REAL_VERIFIED",
                )
                session.add(granule)
                session.flush()
                print(f" -> Created SatelliteGranule: {granule.id}")
            else:
                print(f" -> Existing SatelliteGranule: {granule.id}")

            # 3. Find Storm in DB
            storm = (
                session.execute(select(Storm).where(Storm.canonical_name == storm_name))
                .scalars()
                .first()
            )

            if not storm:
                raise ValueError(f"Storm {storm_name} not found in database!")

            # 4. Find Nearest Synoptic Observations (IMD primary, JTWC secondary)
            window = timedelta(minutes=60)
            observations = (
                session.execute(
                    select(TrackObservation)
                    .where(
                        TrackObservation.storm_id == storm.id,
                        TrackObservation.observation_time_utc >= obs_approx_time - window,
                        TrackObservation.observation_time_utc <= obs_approx_time + window,
                    )
                    .order_by(TrackObservation.observation_time_utc)
                )
                .scalars()
                .all()
            )

            imd_obs = [o for o in observations if o.source_agency == Agency.IMD.value]
            jtwc_obs = [o for o in observations if o.source_agency == Agency.JTWC.value]

            if not imd_obs:
                # If no IMD observation in +/- 60 min, search wider (+/- 180 min)
                imd_obs = (
                    session.execute(
                        select(TrackObservation)
                        .where(
                            TrackObservation.storm_id == storm.id,
                            TrackObservation.source_agency == Agency.IMD.value,
                        )
                        .order_by(TrackObservation.observation_time_utc.desc())
                    )
                    .scalars()
                    .all()
                )
                # Find closest in time
                imd_obs = sorted(
                    imd_obs,
                    key=lambda o: abs((o.observation_time_utc - obs_approx_time).total_seconds()),
                )

            best_imd = imd_obs[0] if imd_obs else None
            best_jtwc = (
                sorted(
                    jtwc_obs,
                    key=lambda o: abs((o.observation_time_utc - obs_approx_time).total_seconds()),
                )[0]
                if jtwc_obs
                else None
            )

            center_lat = (
                best_imd.latitude if best_imd else (best_jtwc.latitude if best_jtwc else 20.0)
            )
            center_lon = (
                best_imd.longitude if best_imd else (best_jtwc.longitude if best_jtwc else 88.0)
            )

            print(
                f" -> Storm center for crop: ({center_lat:.2f}N, {center_lon:.2f}E) from {best_imd.source_agency if best_imd else 'fallback'}"
            )

            # 5. Extract Multi-Channel Crop
            time_tag = obs_approx_time.strftime("%Y%m%d_%H%M")
            crop_filename = f"{storm_name}_{time_tag}_MULTICHANNEL.h5"
            crop_path = PROCESSED_DIR / crop_filename

            if crop_path.is_file() and crop_path.stat().st_size > 100 * 1024:
                print(
                    f" -> Processed crop already exists: {crop_path} ({crop_path.stat().st_size} bytes)"
                )
                crop_sha = compute_sha256(crop_path)
            else:
                print(" -> Extracting 800 km multi-channel crop...")
                crop_result = crop_engine.extract_crop(
                    hdf5_path=raw_file,
                    center_lat=center_lat,
                    center_lon=center_lon,
                    channels=["TIR-1", "WV"],
                )
                crop_sha = crop_engine.save_to_hdf5(crop_result, crop_path)
                print(f" -> Saved crop to {crop_path} (SHA: {crop_sha[:16]}...)")

            # 6. Register SatelliteProcessedCrop
            crop_rec = session.execute(
                select(SatelliteProcessedCrop).where(
                    SatelliteProcessedCrop.file_path == str(crop_path.as_posix())
                )
            ).scalar_one_or_none()

            if not crop_rec:
                crop_rec = SatelliteProcessedCrop(
                    id=uuid.uuid4(),
                    granule_id=granule.id,
                    center_latitude=center_lat,
                    center_longitude=center_lon,
                    geom=WKTElement(f"POINT({center_lon} {center_lat})", srid=4326),
                    crop_box_km=800.0,
                    grid_dimensions=[201, 201],
                    channels=["TIR1", "WV"],
                    file_path=str(crop_path.as_posix()),
                    sha256_checksum=crop_sha,
                    verification_status="REAL_VERIFIED",
                )
                session.add(crop_rec)
                session.flush()
                print(f" -> Created SatelliteProcessedCrop: {crop_rec.id}")
            else:
                print(f" -> Existing SatelliteProcessedCrop: {crop_rec.id}")

            # 7. Create Track Associations
            for agency_obs, _role in [(best_imd, "PRIMARY"), (best_jtwc, "SECONDARY")]:
                if not agency_obs:
                    continue
                assoc = session.execute(
                    select(SatelliteTrackAssociation).where(
                        SatelliteTrackAssociation.crop_id == crop_rec.id,
                        SatelliteTrackAssociation.track_observation_id == agency_obs.id,
                    )
                ).scalar_one_or_none()

                if not assoc:
                    t_diff = int(
                        abs((obs_approx_time - agency_obs.observation_time_utc).total_seconds())
                    )
                    d_lat = center_lat - agency_obs.latitude
                    d_lon = center_lon - agency_obs.longitude
                    d_km = float(
                        np.sqrt(
                            (d_lat * 111.0) ** 2
                            + (d_lon * 111.0 * np.cos(np.radians(center_lat))) ** 2
                        )
                    )

                    assoc = SatelliteTrackAssociation(
                        id=uuid.uuid4(),
                        crop_id=crop_rec.id,
                        track_observation_id=agency_obs.id,
                        temporal_offset_seconds=t_diff,
                        spatial_offset_km=d_km,
                        is_interpolated=False,
                        verification_status="REAL_VERIFIED",
                    )
                    session.add(assoc)
                    session.flush()
                    print(
                        f" -> Created Association ({agency_obs.source_agency}): dt={t_diff}s, dist={d_km:.1f}km"
                    )

            results.append(
                {
                    "granule_file": file_name,
                    "granule_sha256": sha256,
                    "satellite": sat_name,
                    "storm": storm_name,
                    "crop_file": crop_filename,
                    "crop_sha256": crop_sha,
                    "center_lat": center_lat,
                    "center_lon": center_lon,
                    "best_imd_wind": best_imd.wind_speed_knots if best_imd else None,
                    "best_jtwc_wind": best_jtwc.wind_speed_knots if best_jtwc else None,
                }
            )

        session.commit()

    print(f"\nProcessing completed successfully for {len(results)} granules.")
    return results


if __name__ == "__main__":
    process_all_raw_granules()
