"""Tests for Module A multi-channel export contract, deduplication, and eligibility governance."""

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from vayumarg.contracts.enums import Agency, ModelEligibility, ProvenanceStatus
from vayumarg.contracts.export import export_module_a_multichannel_dataset
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


def test_frozen_snapshot_preservation() -> None:
    """Verify that the immutable F1.1 historical dataset freeze manifest is unaltered."""
    snap_path = Path("data/manifests/vayumarg_f1_1_freeze_manifest.json")
    assert snap_path.is_file()
    hasher = hashlib.sha256()
    with open(snap_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    manifest_sha = hasher.hexdigest()
    assert manifest_sha == "441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107", (
        f"F1.1 frozen manifest mutated! SHA: {manifest_sha}"
    )


def test_export_module_a_multichannel_deduplication(
    db_session: Session,
    synthetic_storm: Storm,
    synthetic_source_asset: SourceAsset,
) -> None:
    """Verify that export_module_a_multichannel_dataset outputs exactly 1 atomic sample per image."""
    now = datetime(2024, 5, 26, 18, 0, 0, tzinfo=UTC)

    # 1. IBTrACS Storm Alias
    alias = StormAlias(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_agency=Agency.IBTRACS.value,
        agency_storm_id=f"TEST_SID_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(alias)

    # 2. Add 2 observations for the same timestamp: IMD (3-min) and JTWC (1-min)
    obs_imd = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.IMD.value,
        source_record_id=f"REC_IMD_{uuid.uuid4().hex[:8]}",
        observation_time_utc=now,
        latitude=15.0,
        longitude=88.0,
        wind_speed_knots=60.0,
        averaging_period="3-min",
        imd_category="SCS",
        central_pressure_hpa=980.0,
        is_retrospective_best_track=True,
    )
    obs_jtwc = TrackObservation(
        id=uuid.uuid4(),
        storm_id=synthetic_storm.id,
        source_asset_id=synthetic_source_asset.id,
        source_agency=Agency.JTWC.value,
        source_record_id=f"REC_JTWC_{uuid.uuid4().hex[:8]}",
        observation_time_utc=now,
        latitude=15.2,
        longitude=88.1,
        wind_speed_knots=55.0,
        averaging_period="1-min",
        is_retrospective_best_track=True,
    )
    db_session.add_all([obs_imd, obs_jtwc])
    db_session.flush()

    # 3. Satellite Product, Granule, and Processed Crop (REAL_VERIFIED)
    prod = SatelliteProduct(
        id=uuid.uuid4(),
        product_code=f"3RIMG_TEST_{uuid.uuid4().hex[:6]}",
        satellite_name="INSAT-3DR",
        sensor_name="IMAGER",
        processing_level="L1B",
        spatial_resolution_km=4.0,
        spectral_channels=[{"name": "TIR-1"}, {"name": "WV"}],
    )
    db_session.add(prod)
    db_session.flush()

    granule = SatelliteGranule(
        id=uuid.uuid4(),
        product_id=prod.id,
        granule_name=f"3RIMG_TEST_{uuid.uuid4().hex[:8]}.h5",
        acquisition_start_utc=now,
        file_format="HDF5",
        storage_uri="data/raw/satellite/test.h5",
        sha256_checksum="a" * 64,
        file_size_bytes=280000000,
        verification_status=ProvenanceStatus.REAL_VERIFIED.value,
    )
    db_session.add(granule)
    db_session.flush()

    crop = SatelliteProcessedCrop(
        id=uuid.uuid4(),
        granule_id=granule.id,
        storm_id=synthetic_storm.id,
        crop_time_utc=now,
        center_latitude=15.0,
        center_longitude=88.0,
        pixel_height=201,
        pixel_width=201,
        channels=["TIR-1", "WV"],
        spatial_resolution_km=4.0,
        storage_uri="data/processed/satellite/test_crop.h5",
        sha256_checksum="b" * 64,
        verification_status=ProvenanceStatus.REAL_VERIFIED.value,
    )
    db_session.add(crop)
    db_session.flush()

    # 4. Associate the single crop with BOTH IMD and JTWC observations
    assoc_imd = SatelliteTrackAssociation(
        id=uuid.uuid4(),
        crop_id=crop.id,
        track_observation_id=obs_imd.id,
        temporal_offset_minutes=2.0,
        spatial_offset_km=1.0,
        association_confidence=0.96,
        verification_status=ProvenanceStatus.REAL_VERIFIED.value,
    )
    assoc_jtwc = SatelliteTrackAssociation(
        id=uuid.uuid4(),
        crop_id=crop.id,
        track_observation_id=obs_jtwc.id,
        temporal_offset_minutes=2.0,
        spatial_offset_km=25.0,
        association_confidence=0.75,
        verification_status=ProvenanceStatus.REAL_VERIFIED.value,
    )
    db_session.add_all([assoc_imd, assoc_jtwc])
    db_session.flush()

    # 5. Export and verify deduplication
    recs = export_module_a_multichannel_dataset(
        db_session,
        sid=alias.agency_storm_id,
        min_model_eligibility=ModelEligibility.MODEL_ELIGIBLE.value,
    )

    # Exactly 1 atomic record must be exported despite 2 distinct agency associations!
    assert len(recs) == 1
    sample = recs[0]

    assert sample.crop_id == crop.id
    assert sample.canonical_name == synthetic_storm.canonical_name
    assert sample.primary_agency == "IMD"
    assert sample.primary_wind_speed_knots == 60.0
    assert sample.primary_imd_category == "SCS"

    # Secondary agency label is attached to the same record
    assert sample.secondary_agency == "JTWC"
    assert sample.secondary_wind_speed_knots == 55.0

    assert sample.model_eligibility == ModelEligibility.MODEL_ELIGIBLE.value
    assert sample.provenance_status == ProvenanceStatus.REAL_VERIFIED.value
