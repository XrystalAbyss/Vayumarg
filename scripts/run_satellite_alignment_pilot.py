"""Demonstrate and verify the end-to-end satellite-track alignment pipeline on authentic cyclones."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from vayumarg.core.logging import get_logger
from vayumarg.database.engine import get_db_session
from vayumarg.database.schema import (
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteProduct,
    Storm,
    StormAlias,
)
from vayumarg.satellite.alignment import SatelliteTrackAligner
from vayumarg.satellite.tcir_adapter import TCIRAdapter

logger = get_logger("vayumarg.satellite_alignment_pilot")


def run_alignment_pilot() -> dict[str, Any]:
    pilot_h5 = Path("data/interim/tcir_nio_pilot.h5")
    if not pilot_h5.is_file():
        raise FileNotFoundError(f"Pilot file missing: {pilot_h5}")

    adapter = TCIRAdapter(pilot_h5)
    df_info = adapter.load_metadata_table()

    with get_db_session() as session:
        from sqlalchemy import text

        session.execute(text("DELETE FROM satellite_track_associations;"))
        session.execute(text("DELETE FROM satellite_processed_crops;"))
        # 1. Register Satellite Product
        prod = session.execute(
            select(SatelliteProduct).where(SatelliteProduct.product_code == "TCIR_NIO_PILOT")
        ).scalar_one_or_none()

        if not prod:
            prod = SatelliteProduct(
                id=uuid.uuid4(),
                product_code="TCIR_NIO_PILOT",
                satellite_name="GridSat_B1_CMORPH",
                sensor_name="AVHRR_HIRS_SSMI",
                processing_level="L3",
                spatial_resolution_km=4.0,
                spectral_channels=[
                    {"name": "IR1", "type": "Infrared Window", "resolution_km": 4.0},
                    {"name": "WV", "type": "Water Vapor", "resolution_km": 4.0},
                    {"name": "VIS", "type": "Visible", "resolution_km": 4.0},
                    {"name": "PMW", "type": "Passive Microwave", "resolution_km": 4.0},
                ],
                calibration_info={"unit": "Kelvin / mm_per_hr", "norm": "Physical Units"},
                created_at_utc=datetime.now(UTC),
            )
            session.add(prod)
            session.flush()

        # 2. Register Granule
        granule = session.execute(
            select(SatelliteGranule).where(
                SatelliteGranule.granule_name == "TCIR_NIO_PILOT_2020_2023"
            )
        ).scalar_one_or_none()

        if not granule:
            granule = SatelliteGranule(
                id=uuid.uuid4(),
                product_id=prod.id,
                granule_name="TCIR_NIO_PILOT_2020_2023",
                acquisition_start_utc=datetime(2020, 5, 16, 0, 0, tzinfo=UTC),
                acquisition_end_utc=datetime(2023, 6, 9, 0, 0, tzinfo=UTC),
                file_format="HDF5",
                storage_uri=str(pilot_h5.as_posix()),
                sha256_checksum=adapter.sha256,
                file_size_bytes=pilot_h5.stat().st_size,
                granule_metadata={"total_frames": len(df_info)},
                verification_status="SYNTHETIC_FIXTURE",
                created_at_utc=datetime.now(UTC),
            )
            session.add(granule)
            session.flush()

        # 3. Create Crops and Align to Best Tracks
        aligner = SatelliteTrackAligner(
            max_temporal_offset_minutes=60.0, max_spatial_offset_km=150.0
        )
        total_created_crops = 0
        total_associations = 0
        alignment_summary = []

        for idx in range(len(df_info)):
            meta = adapter.get_frame_metadata(idx)

            # Match storm by authoritative SID
            storm = (
                session.execute(
                    select(Storm)
                    .join(StormAlias, Storm.id == StormAlias.storm_id)
                    .where(StormAlias.agency_storm_id == meta.storm_id)
                )
                .scalars()
                .first()
            )

            if not storm:
                logger.warning("Storm %s not found in DB", meta.storm_id)
                continue

            # Check or create crop
            crop = session.execute(
                select(SatelliteProcessedCrop).where(
                    SatelliteProcessedCrop.granule_id == granule.id,
                    SatelliteProcessedCrop.storm_id == storm.id,
                    SatelliteProcessedCrop.crop_time_utc == meta.timestamp_utc,
                )
            ).scalar_one_or_none()

            if not crop:
                crop = SatelliteProcessedCrop(
                    id=uuid.uuid4(),
                    granule_id=granule.id,
                    storm_id=storm.id,
                    crop_time_utc=meta.timestamp_utc,
                    center_latitude=meta.latitude,
                    center_longitude=meta.longitude,
                    pixel_height=201,
                    pixel_width=201,
                    channels=["IR1", "WV", "VIS", "PMW"],
                    spatial_resolution_km=4.0,
                    storage_uri=f"{pilot_h5.as_posix()}#frame={idx}",
                    sha256_checksum=adapter.sha256,
                    quality_control_flags={"is_nio": meta.is_north_indian_ocean},
                    verification_status="SYNTHETIC_FIXTURE",
                    created_at_utc=datetime.now(UTC),
                )
                session.add(crop)
                session.flush()
                total_created_crops += 1

            # Run spatiotemporal alignment
            assocs = aligner.persist_best_associations(session, crop)
            total_associations += len(assocs)

            for a in assocs:
                alignment_summary.append(
                    {
                        "storm_name": storm.canonical_name,
                        "crop_time": crop.crop_time_utc.isoformat(),
                        "track_time": a.track_observation.observation_time_utc.isoformat(),
                        "agency": a.track_observation.source_agency,
                        "wind_speed_kts": a.track_observation.wind_speed_knots,
                        "averaging": a.track_observation.averaging_period,
                        "temporal_offset_min": a.temporal_offset_minutes,
                        "spatial_offset_km": a.spatial_offset_km,
                        "confidence": a.association_confidence,
                    }
                )

        report_file = Path("reports/F2_IMAGE_ALIGNMENT_AUDIT.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at_utc": datetime.now(UTC).isoformat(),
                    "total_crops": total_created_crops,
                    "total_associations": total_associations,
                    "sample_associations": alignment_summary,
                },
                f,
                indent=2,
            )

        print(
            f"Alignment complete: {total_created_crops} crops, {total_associations} track associations"
        )
        print(f"Audit log written to: {report_file}")
        return {"total_crops": total_created_crops, "total_associations": total_associations}


if __name__ == "__main__":
    run_alignment_pilot()
