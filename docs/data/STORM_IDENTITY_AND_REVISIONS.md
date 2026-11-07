# Storm Identity, Multi-Agency Lineage, and Observation Revisions

## 1. The Multi-Agency Cyclone Identity Problem

In tropical cyclone archives, defining storm identity based solely on `(canonical_name, season_year, basin)` leads to critical failure modes:
1. **Unnamed Systems:** In the North Indian Ocean, cyclonic disturbances were historically un-named prior to 2004. Multiple distinct depressions formed in the same basin and season year (e.g., three unnamed depressions in the Bay of Bengal during post-monsoon 1998).
2. **Re-used Names:** Names are routinely re-used across distinct meteorological seasons and basins.
3. **Multi-Agency Discrepancies:** A single synoptic event may be assigned different identifiers and classifications by different agencies (e.g. IMD calls a system `BOB 01/2020` while JTWC designates it `01B` and NOAA assigns IBTrACS SID `2020136N10088`).

---

## 2. Vayumarg Storm Identity Model

Vayumarg resolves this through a three-tier identity architecture:

```
+-------------------------------------------------------------------+
|                            Storm Entity                           |
|  - id: UUID (Canonical Stable Surrogate Key)                      |
|  - canonical_name: VARCHAR (e.g. "AMPHAN", "BIPARJOY", "UNNAMED")  |
|  - season_year: INTEGER (e.g. 2020)                               |
|  - primary_basin: VARCHAR (e.g. "NI")                             |
|  - nature: VARCHAR (e.g. "TS", "DS", "NR")                        |
+-------------------------------------------------------------------+
                                  |
                                  | 1:N
                                  v
+-------------------------------------------------------------------+
|                         StormAlias Entity                         |
|  - id: UUID                                                       |
|  - storm_id: UUID (Foreign Key -> storms.id)                       |
|  - source_agency: VARCHAR ("IBTRACS", "IMD", "JTWC", etc.)        |
|  - agency_storm_id: VARCHAR (e.g. "2020136N10088", "IO012020")    |
|  - agency_storm_name: VARCHAR (e.g. "AMPHAN")                     |
|  - matching_confidence: FLOAT [0.0, 1.0]                          |
|  Constraint: UNIQUE(source_agency, agency_storm_id)               |
+-------------------------------------------------------------------+
```

### Key Integrity Rules
1. **Primary Identity is Surrogate:** The internal canonical identity of any cyclone event is an immutable UUID primary key (`storms.id`). Distinct cyclones never collide.
2. **Authoritative Agency Namespaces:** External identifiers are partitioned by `source_agency`. IBTrACS SIDs are uniquely indexed within `source_agency='IBTRACS'`. Duplicate SIDs in the same agency namespace are strictly rejected via database unique constraint `uq_agency_storm_alias`.
3. **Unnamed Storm Co-existence:** Multiple unnamed storms (`canonical_name='UNNAMED'`) within the same season year and basin freely coexist as separate database entities.

---

## 3. Multi-Agency Observation Lineage & Migration 003

In Milestone F0.1, the unique constraint on observations was:
```sql
UNIQUE(source_asset_id, source_record_id)
```
In NOAA IBTrACS, a single physical CSV row represents a synoptic timestamp containing observations from **multiple agencies** (`WMO_WIND`, `NEWDELHI_WIND`, `USA_WIND`). If separate observation rows are extracted for WMO, IMD, and JTWC from the same raw CSV line index, a single-column record ID would collide.

### Solution Delivered in Migration 003 (`003_ibtracs_multi_agency_lineage.py`):
The schema was refined to scope record uniqueness by agency:
```sql
-- Migration 003 Upgrade:
ALTER TABLE track_observations DROP CONSTRAINT uq_track_asset_record;
ALTER TABLE track_observations ADD CONSTRAINT uq_track_asset_record_agency 
    UNIQUE(source_asset_id, source_record_id, source_agency);
```
In addition, `source_record_id` is deterministically formatted as `ROW_{line_index}:{source_agency}` (e.g. `ROW_1042:IMD`, `ROW_1042:JTWC`, `ROW_1042:IBTRACS`), providing both physical row provenance and agency-specific isolation.

---

## 4. Source Asset Revisions and Immutability Policy

When an updated best-track dataset is released by NOAA (e.g. revision `v04r02` replacing `v04r01`):
1. The new raw file is stored in `data/raw/` with a distinct filename and new SHA-256 manifest.
2. A new `source_assets` record is registered linking to the same `DataSource`.
3. Historical observations linked to previous assets (`source_asset_id`) remain **completely untouched and immutable**.
4. Revised observations are imported linking to the new `source_asset_id`.
5. Superseded records can be marked with `is_superseded = TRUE` without destructive deletion.
6. Module A and Module B queries can reproduce exact historical runs by filtering on `source_asset_id`.

