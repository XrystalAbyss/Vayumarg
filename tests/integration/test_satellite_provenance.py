"""Integration tests for satellite dataset provenance segregation and export safety."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.contracts.export import export_satellite_paired_dataset
from vayumarg.database.schema import (
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteProduct,
    SatelliteTrackAssociation,
    SourceAsset,
    Storm,
    StormAlias,
    TrackObservation,
)
from vayumarg.satellite.alignment import SatelliteTrackAligner


@pytest.mark.integration
def test_provenance_propagation_and_export_isolation(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
) -> None:
    """Ensure aligner propagates verification status and export strictly isolates real from synthetic."""
    now = datetime.now(UTC)

    # 1. Storm Alias & Observation
    alias = StormAlias(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_agency="IBTRACS",
        agency_storm_id=f"TEST_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(alias)

    obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_record_id=f"REC_{uuid.uuid4().hex[:8]}",
        observation_time_utc=now,
        latitude=15.0,
        longitude=88.0,
        source_agency="IMD",
        averaging_period="3-min",
        wind_speed_knots=65.0,
        is_retrospective_best_track=True,
    )
    db_session.add(obs)
    db_session.flush()

    # 2. Product
    prod = SatelliteProduct(
        id=uuid.uuid4(),
        product_code=f"PROV_PROD_{uuid.uuid4().hex[:8]}",
        satellite_name="INSAT-3DR",
        sensor_name="IMAGER",
        processing_level="L1B",
        spatial_resolution_km=4.0,
        spectral_channels=[{"name": "TIR-1"}],
    )
    db_session.add(prod)
    db_session.flush()

    # 3. Real Granule & Crop
    real_granule = SatelliteGranule(
        id=uuid.uuid4(),
        product_id=prod.id,
        granule_name=f"REAL_INSAT_{uuid.uuid4().hex[:8]}",
        acquisition_start_utc=now,
        file_format="HDF5",
        storage_uri="data/raw/real.h5",
        sha256_checksum="b" * 64,
        file_size_bytes=300000000,
        verification_status="REAL_VERIFIED",
    )
    db_session.add(real_granule)
    db_session.flush()

    real_crop = SatelliteProcessedCrop(
        id=uuid.uuid4(),
        granule_id=real_granule.id,
        storm_id=synthetic_storm.id,
        crop_time_utc=now,
        center_latitude=15.0,
        center_longitude=88.0,
        pixel_height=201,
        pixel_width=201,
        channels=["TIR-1"],
        spatial_resolution_km=4.0,
        storage_uri="data/raw/real.h5#crop=0",
        sha256_checksum="b" * 64,
        verification_status="REAL_VERIFIED",
    )
    db_session.add(real_crop)
    db_session.flush()

    # 4. Synthetic Granule & Crop
    synth_granule = SatelliteGranule(
        id=uuid.uuid4(),
        product_id=prod.id,
        granule_name=f"SYNTH_PILOT_{uuid.uuid4().hex[:8]}",
        acquisition_start_utc=now,
        file_format="HDF5",
        storage_uri="data/interim/synth.h5",
        sha256_checksum="c" * 64,
        file_size_bytes=1000000,
        verification_status="SYNTHETIC_FIXTURE",
    )
    db_session.add(synth_granule)
    db_session.flush()

    synth_crop = SatelliteProcessedCrop(
        id=uuid.uuid4(),
        granule_id=synth_granule.id,
        storm_id=synthetic_storm.id,
        crop_time_utc=now,
        center_latitude=15.0,
        center_longitude=88.0,
        pixel_height=201,
        pixel_width=201,
        channels=["TIR-1"],
        spatial_resolution_km=4.0,
        storage_uri="data/interim/synth.h5#crop=0",
        sha256_checksum="c" * 64,
        verification_status="SYNTHETIC_FIXTURE",
    )
    db_session.add(synth_crop)
    db_session.flush()

    # 5. Align both crops
    aligner = SatelliteTrackAligner()
    aligner.persist_best_associations(db_session, real_crop)
    aligner.persist_best_associations(db_session, synth_crop)

    # 6. Check association statuses
    real_assoc = db_session.execute(
        select(SatelliteTrackAssociation).where(SatelliteTrackAssociation.crop_id == real_crop.id)
    ).scalar_one()
    assert real_assoc.verification_status == "REAL_VERIFIED"

    synth_assoc = db_session.execute(
        select(SatelliteTrackAssociation).where(SatelliteTrackAssociation.crop_id == synth_crop.id)
    ).scalar_one()
    assert synth_assoc.verification_status == "SYNTHETIC_FIXTURE"

    # 7. Check export contract isolation
    real_export = export_satellite_paired_dataset(
        db_session, sid=alias.agency_storm_id, verification_status="REAL_VERIFIED"
    )
    assert len(real_export) == 1
    assert real_export[0].verification_status == "REAL_VERIFIED"

    synth_export = export_satellite_paired_dataset(
        db_session, sid=alias.agency_storm_id, verification_status="SYNTHETIC_FIXTURE"
    )
    assert len(synth_export) == 1
    assert synth_export[0].verification_status == "SYNTHETIC_FIXTURE"
