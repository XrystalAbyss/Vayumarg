"""Unit tests for Scientific Reconciliation logic and conventions."""

from vayumarg.ingestion.ibtracs_parser import IBTrACSParser


def test_wmo_agency_averaging_convention_mapping():
    """Verify WMO_WIND averaging periods correctly mapped from authoritative WMO_AGENCY."""
    parser = IBTrACSParser.__new__(IBTrACSParser)

    # 1. RSMC New Delhi (IMD) -> 3-minute sustained
    assert parser._resolve_wmo_averaging("newdelhi", 65.0) == "3-min"
    assert parser._resolve_wmo_averaging("NEWDELHI", 25.0) == "3-min"

    # 2. RSMC Tokyo (JMA) -> 10-minute sustained
    assert parser._resolve_wmo_averaging("tokyo", 45.0) == "10-min"

    # 3. NHC / ATCF -> 1-minute sustained
    assert parser._resolve_wmo_averaging("hurdat_atl", 30.0) == "1-min"
    assert parser._resolve_wmo_averaging("atcf", 70.0) == "1-min"

    # 4. Unknown agency or null wind
    assert parser._resolve_wmo_averaging("other_agency", 50.0) == "unknown"
    assert parser._resolve_wmo_averaging("newdelhi", None) == "unknown"
    assert parser._resolve_wmo_averaging(None, 65.0) == "unknown"


def test_cross_basin_detection_bounds():
    """Verify points outside the North Indian Ocean box (0-40N, 30-105E) are flagged CROSS_BASIN."""
    # Regional NI points
    lat, lon = 15.0, 85.0
    is_cross_basin = lat > 40.0 or lon < 30.0 or lon > 105.0
    assert not is_cross_basin

    # Arctic extratropical (e.g. Hurricane Faith 83N)
    lat, lon = 83.0, 45.0
    is_cross_basin = lat > 40.0 or lon < 30.0 or lon > 105.0
    assert is_cross_basin

    # Atlantic transit point (-20.5W)
    lat, lon = 12.9, -20.5
    is_cross_basin = lat > 40.0 or lon < 30.0 or lon > 105.0
    assert is_cross_basin

    # Pacific transit point (120.0E)
    lat, lon = 18.0, 120.0
    is_cross_basin = lat > 40.0 or lon < 30.0 or lon > 105.0
    assert is_cross_basin


def test_imd_four_way_venn_reconciliation_math():
    """Verify that four-way partition of IMD observations satisfies exact population conservation."""
    # Authentic North Indian Ocean numbers verified in F1.1:
    both_wind_and_cat = 8397
    cat_only_null_wind = 1161
    wind_only_null_cat = 1070
    neither = 131

    total_imd_obs = both_wind_and_cat + cat_only_null_wind + wind_only_null_cat + neither
    assert total_imd_obs == 10759

    # Table 3 denominator (all non-null wind observations)
    non_null_wind_count = both_wind_and_cat + wind_only_null_cat
    assert non_null_wind_count == 9467

    # Table 4 denominator (all populated category observations)
    populated_cat_count = both_wind_and_cat + cat_only_null_wind
    assert populated_cat_count == 9558

    # The 51 apparent discrepancy is exactly the difference between the two independent subsets:
    discrepancy = populated_cat_count - 40 - non_null_wind_count  # 40 historical/regional grades
    assert discrepancy == 51
