"""Unit tests for authentic satellite provenance, lineage, and ground-truth label policies."""

from vayumarg.satellite.provenance import (
    AUTHENTIC_SATELLITE_REGISTRY,
    DANA_IMD_INELIGIBILITY_NOTICE,
    get_provenance_by_identifier,
)


def test_four_authentic_storms_registered():
    """Verify REMAL, DANA, AMPHAN, and BIPARJOY are registered with REAL_VERIFIED status."""
    required = ["REMAL", "DANA", "AMPHAN", "BIPARJOY"]
    for storm in required:
        assert storm in AUTHENTIC_SATELLITE_REGISTRY
        rec = AUTHENTIC_SATELLITE_REGISTRY[storm]
        assert rec.verification_status == "REAL_VERIFIED"
        assert rec.storm_name == storm
        assert len(rec.source_sha256) == 64
        assert len(rec.crop_sha256) == 64
        assert rec.crop_extent_km == 800.0
        assert rec.target_grid_spacing_km == 4.0
        assert len(rec.available_channels) == 4


def test_dana_imd_ineligibility_policy():
    """Verify Cyclone DANA task-specific IMD ineligibility is strictly enforced."""
    dana = AUTHENTIC_SATELLITE_REGISTRY["DANA"]
    assert dana.primary_imd_eligible is False
    assert dana.primary_imd_observation is None
    assert dana.dana_ineligibility_notice == DANA_IMD_INELIGIBILITY_NOTICE
    assert "unavailable under this study's eligibility policy" in dana.dana_ineligibility_notice
    # Secondary JTWC label must remain available
    assert dana.secondary_jtwc_observation is not None
    assert dana.secondary_jtwc_observation.agency == "JTWC"
    assert dana.secondary_jtwc_observation.averaging_period == "1-minute sustained"


def test_primary_imd_labels_for_remal_amphan_biparjoy():
    """Verify primary IMD 3-minute sustained wind and retrospective categories for eligible storms."""
    remal = AUTHENTIC_SATELLITE_REGISTRY["REMAL"]
    assert remal.primary_imd_eligible is True
    assert remal.primary_imd_observation.cyclone_category == "SCS"
    assert remal.primary_imd_observation.wind_speed_knots == 60.0
    assert remal.primary_imd_observation.central_pressure_hpa == 978.0

    amphan = AUTHENTIC_SATELLITE_REGISTRY["AMPHAN"]
    assert amphan.primary_imd_eligible is True
    assert amphan.primary_imd_observation.cyclone_category == "ESCS"
    assert amphan.primary_imd_observation.wind_speed_knots == 95.0
    assert amphan.primary_imd_observation.central_pressure_hpa == 952.0

    biparjoy = AUTHENTIC_SATELLITE_REGISTRY["BIPARJOY"]
    assert biparjoy.primary_imd_eligible is True
    assert biparjoy.primary_imd_observation.cyclone_category == "VSCS"
    assert biparjoy.primary_imd_observation.wind_speed_knots == 85.0
    assert biparjoy.primary_imd_observation.central_pressure_hpa == 962.0


def test_retrieval_by_various_identifiers():
    """Verify provenance retrieval by lowercase name, uppercase name, or crop UUID."""
    assert get_provenance_by_identifier("remal") is not None
    assert get_provenance_by_identifier("REMAL") is not None
    assert get_provenance_by_identifier("e93002d6-a5e2-4ae2-8adf-fa7a50d0da36") is not None
    assert get_provenance_by_identifier("non_existent_storm") is None


def test_no_synthetic_fixtures_in_registry():
    """Verify that synthetic pilot fixtures are never registered as authentic."""
    for _storm_name, rec in AUTHENTIC_SATELLITE_REGISTRY.items():
        assert "tcir" not in rec.source_filename.lower()
        assert "pilot" not in rec.source_filename.lower()
        assert "synthetic" not in rec.source_filename.lower()
        assert rec.verification_status == "REAL_VERIFIED"
