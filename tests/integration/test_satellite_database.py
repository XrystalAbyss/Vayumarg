"""Integration tests for satellite data models, foreign keys, and associations."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from vayumarg.database.schema import (
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteProduct,
    SatelliteTrackAssociation,
    SourceAsset,
    Storm,
    TrackObservation,
)


@pytest.mark.integration
def test_satellite_schema_hierarchy_and_associations(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
):
    """Verify end-to-end insertion of product, granule, crop, and association records."""
    now = datetime.now(UTC)

    # 1. Product
    prod = SatelliteProduct(
        id=uuid.uuid4(),
        product_code=f"TEST_PROD_{uuid.uuid4().hex[:8]}",
        satellite_name="TEST_SAT",
        sensor_name="TEST_IMAGER",
        processing_level="L1B",
        spatial_resolution_km=4.0,
        spectral_channels=[{"name": "IR1"}, {"name": "WV"}],
        created_at_utc=now,
    )
    db_session.add(prod)
    db_session.flush()

    # 2. Granule
    granule = SatelliteGranule(
        id=uuid.uuid4(),
        product_id=prod.id,
        granule_name=f"TEST_GRANULE_{uuid.uuid4().hex[:8]}",
        acquisition_start_utc=now,
        file_format="HDF5",
        storage_uri="file:///test/granule.h5",
        sha256_checksum="a" * 64,
        file_size_bytes=1048576,
        created_at_utc=now,
    )
    db_session.add(granule)
    db_session.flush()

    # 3. Processed Crop
    crop = SatelliteProcessedCrop(
        id=uuid.uuid4(),
        granule_id=granule.id,
        storm_id=synthetic_storm.id,
        crop_time_utc=now,
        center_latitude=15.0,
        center_longitude=85.0,
        pixel_height=201,
        pixel_width=201,
        channels=["IR1", "WV"],
        spatial_resolution_km=4.0,
        storage_uri="file:///test/crop.h5",
        sha256_checksum="b" * 64,
        created_at_utc=now,
    )
    db_session.add(crop)
    db_session.flush()

    # 4. Track observation for association
    from vayumarg.contracts.enums import Agency

    obs = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id=f"TEST_OBS_{uuid.uuid4().hex[:8]}",
        observation_time_utc=now,
        latitude=15.1,
        longitude=85.1,
        wind_speed_knots=50.0,
        averaging_period="3-min",
        quality_flag="VALID",
    )
    db_session.add(obs)
    db_session.flush()

    # 5. Association
    assoc = SatelliteTrackAssociation(
        id=uuid.uuid4(),
        crop_id=crop.id,
        track_observation_id=obs.id,
        temporal_offset_minutes=0.0,
        spatial_offset_km=15.0,
        association_confidence=0.95,
        validation_status="VALIDATED",
        created_at_utc=now,
    )
    db_session.add(assoc)
    db_session.flush()

    # Verify query and relationships
    retrieved_crop = db_session.execute(
        select(SatelliteProcessedCrop).where(SatelliteProcessedCrop.id == crop.id)
    ).scalar_one()

    assert retrieved_crop is not None
    assert retrieved_crop.granule.product.product_code == prod.product_code
    assert len(retrieved_crop.associations) == 1
    assert retrieved_crop.associations[0].track_observation_id == obs.id
