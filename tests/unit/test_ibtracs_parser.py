"""Unit tests for NOAA IBTrACS CSV parser."""

import tempfile
from pathlib import Path

from vayumarg.ingestion.ibtracs_parser import IBTrACSParser, parse_clean_float, parse_clean_str

MINI_CSV_CONTENT = """SID,SEASON,NUMBER,BASIN,SUBBASIN,NAME,ISO_TIME,NATURE,LAT,LON,WMO_WIND,WMO_PRES,WMO_AGENCY,TRACK_TYPE,DIST2LAND,LANDFALL,IFLAG,USA_AGENCY,USA_ATCF_ID,USA_LAT,USA_LON,USA_RECORD,USA_STATUS,USA_WIND,USA_PRES,USA_SSHS,NEWDELHI_LAT,NEWDELHI_LON,NEWDELHI_GRADE,NEWDELHI_WIND,NEWDELHI_PRES,NEWDELHI_CI,NEWDELHI_DP,NEWDELHI_POCI
,Year, , , , , , ,degrees_north,degrees_east,kts,mb, , ,km,km, , , ,degrees_north,degrees_east, , ,kts,mb, ,degrees_north,degrees_east, ,kts,mb, ,mb,mb
2020136N10088,2020,1,NI,BB,AMPHAN,2020-05-16 00:00:00,TS,10.4,86.6,25,1000,newdelhi,main,650,640,_O____________,usa,IO012020,10.4,86.6, ,TS,30,998,-1,10.5,86.5,D,25,1000,1.5,4.0,1004
2020136N10088,2020,1,NI,BB,AMPHAN,2020-05-18 12:00:00,TS,13.7,86.2,130,907,newdelhi,main,510,490,_O____________,usa,IO012020,13.7,86.2, ,ST,140,901,5,13.7,86.2,SuCS,125,920,6.5,80.0,1000
"""


def test_parse_clean_float():
    assert parse_clean_float("25.5") == 25.5
    assert parse_clean_float("") is None
    assert parse_clean_float("   ") is None
    assert parse_clean_float("-999") is None
    assert parse_clean_float("NaN") is None
    assert parse_clean_float("invalid") is None


def test_parse_clean_str():
    assert parse_clean_str("AMPHAN") == "AMPHAN"
    assert parse_clean_str("   ") is None
    assert parse_clean_str(None) is None


def test_ibtracs_parser_mini_stream():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write(MINI_CSV_CONTENT)
        tmp_path = Path(tmp.name)

    try:
        parser = IBTrACSParser(tmp_path)
        records = list(parser.iter_records())

        assert len(records) == 2

        # First row checks
        storm_info, obs_list = records[0]
        assert storm_info["sid"] == "2020136N10088"
        assert storm_info["canonical_name"] == "AMPHAN"
        assert storm_info["season_year"] == 2020
        assert storm_info["primary_basin"] == "NI"
        assert storm_info["usa_atcf_id"] == "IO012020"

        # Multi-agency observations
        agency_map = {o["source_agency"]: o for o in obs_list}
        assert "IBTRACS" in agency_map
        assert "IMD" in agency_map
        assert "JTWC" in agency_map

        # Verify conventions (WMO_AGENCY is 'newdelhi', so averaging period is 3-min)
        assert agency_map["IBTRACS"]["averaging_period"] == "3-min"
        assert agency_map["IBTRACS"]["wmo_agency"] == "newdelhi"
        assert agency_map["IBTRACS"]["wind_speed_knots"] == 25.0
        assert agency_map["IBTRACS"]["central_pressure_hpa"] == 1000.0

        assert agency_map["IMD"]["averaging_period"] == "3-min"
        assert agency_map["IMD"]["wind_speed_knots"] == 25.0
        assert agency_map["IMD"]["imd_category"] == "D"
        assert agency_map["IMD"]["latitude"] == 10.5
        assert agency_map["IMD"]["longitude"] == 86.5

        assert agency_map["JTWC"]["averaging_period"] == "1-min"
        assert agency_map["JTWC"]["wind_speed_knots"] == 30.0
        assert agency_map["JTWC"]["central_pressure_hpa"] == 998.0

        # Second row checks (Super Cyclone Intensity)
        _, obs_list_2 = records[1]
        agency_map_2 = {o["source_agency"]: o for o in obs_list_2}
        assert agency_map_2["IMD"]["wind_speed_knots"] == 125.0
        assert agency_map_2["IMD"]["imd_category"] == "SuCS"
        assert agency_map_2["JTWC"]["wind_speed_knots"] == 140.0
        assert agency_map_2["IBTRACS"]["wind_speed_knots"] == 130.0

    finally:
        tmp_path.unlink(missing_ok=True)
