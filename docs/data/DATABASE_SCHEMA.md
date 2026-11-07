# Database Schema Specification (PostgreSQL / PostGIS)

**System:** Vayumarg Scientific Data Foundation  
**Dialect:** PostgreSQL 16.4 with PostGIS 3.4.3  
**Migration Engine:** Alembic (Current Revision: `002_storm_identity_and_safety`)  

---

## 1. Architectural Principles & Identity Governance

The Vayumarg database architecture adheres to strict scientific and operational data integrity principles:
1. **Internal Identity Decoupling:** Storm entities are identified by immutable, internal UUID primary keys (`storms.id`). Natural keys like names or seasons are **never** used as unique constraints because multiple cyclones in the same basin/season can be "UNNAMED", "DEPRESSION", or share identical names.
2. **Authoritative Source Identifiers in Aliases:** External source identifiers (e.g., NOAA IBTrACS Storm Identifier `SID`, IMD Cyclone Number `BOB 01/2024`) are stored in `storm_aliases` with strict scoped uniqueness: `UNIQUE(source_agency, agency_storm_id)`.
3. **Immutable Source-Asset Revision Lineage:** Observations are strictly bound to their physical source asset (`source_assets.id`), backed by a SHA-256 hash. Re-analyzed or post-season revisions of datasets (e.g., IBTrACS v04r00 $\rightarrow$ v04r01) are ingested as new assets; previous observations are retained with `is_superseded = TRUE`, preserving the full historical audit trail.
4. **Multi-Agency Coexistence:** Observations from distinct meteorological agencies (e.g., IMD, JTWC, CMA) at the exact same synoptic hour coexist without collision or forced averaging.
5. **Database Environment Isolation:** The persistent research database (`vayumarg`) and the automated test database (`vayumarg_test`) are strictly separated. Destructive operations against the research database are blocked by safety guards.

---

## 2. Table Definitions

### 2.1 `data_sources`
Registers primary scientific data providers, institutions, licensing, and citations.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key (`uuid_generate_v4()`) |
| `provider_name` | `VARCHAR(100)` | No | Institution name (e.g., `IMD`, `JTWC`, `NOAA`, `ISRO`) |
| `dataset_name` | `VARCHAR(150)` | No | Official dataset name (e.g., `RSMC Best Track`, `IBTrACS`) |
| `version` | `VARCHAR(50)` | No | Dataset version (e.g., `v04r01`, `2024.1`) |
| `citation` | `TEXT` | Yes | Formal academic/operational bibliographic citation |
| `license` | `VARCHAR(100)` | Yes | Data distribution license (e.g., `Open Access`, `CC-BY-4.0`) |
| `access_policy` | `TEXT` | Yes | Download URL, scraping restrictions, or API policy |
| `created_at_utc` | `TIMESTAMPTZ` | No | Registration timestamp |

*Constraints:* `UNIQUE(provider_name, dataset_name, version) [uq_datasource_triple]`

---

### 2.2 `source_assets`
Maintains an immutable cryptographic record of raw physical files and downloaded payloads.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key |
| `data_source_id` | `UUID` | No | FK $\rightarrow$ `data_sources(id)` ON DELETE CASCADE |
| `artifact_uri` | `VARCHAR(1024)`| No | URI or absolute relative path to raw stored file |
| `sha256_checksum` | `VARCHAR(64)` | No | Lowercase 64-character SHA-256 hash |
| `file_size_bytes` | `BIGINT` | No | File size in bytes |
| `asset_type` | `VARCHAR(50)` | No | `TRACK_CSV`, `SATELLITE_HDF5`, `SATELLITE_NETCDF`, etc. |
| `retrieval_time_utc`| `TIMESTAMPTZ` | No | Retrieval UTC timestamp |
| `asset_metadata` | `JSONB / JSON` | Yes | Header parameters, sensor specs, band descriptions |

*Constraints:* `UNIQUE(sha256_checksum, artifact_uri) [uq_source_asset_identity]`, Index on `sha256_checksum`

---

### 2.3 `ingestion_runs`
Transactional audit ledger tracking the execution and outcome of each ingestion operation.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key |
| `data_source_id` | `UUID` | No | FK $\rightarrow$ `data_sources(id)` ON DELETE CASCADE |
| `source_asset_id` | `UUID` | Yes | FK $\rightarrow$ `source_assets(id)` ON DELETE SET NULL |
| `started_at_utc` | `TIMESTAMPTZ` | No | Ingestion job start time |
| `completed_at_utc`| `TIMESTAMPTZ` | Yes | Ingestion job termination time |
| `status` | `VARCHAR(50)` | No | `STARTED`, `COMPLETED`, `FAILED`, `PARTIAL` |
| `records_read` | `INTEGER` | No | Total raw records parsed |
| `records_inserted`| `INTEGER` | No | Records successfully persisted |
| `records_rejected`| `INTEGER` | No | Records rejected by validation |
| `error_details` | `TEXT` | Yes | Error traceback or exception message |
| `transaction_outcome`| `TEXT` | Yes | `COMMITTED` or `ROLLED_BACK` |

---

### 2.4 `storms`
Canonical cyclone entities representing distinct physical storm systems.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key |
| `canonical_name` | `VARCHAR(100)` | No | Official cyclone name (e.g., `AMPHAN`, `UNNAMED`, `DEPRESSION`) |
| `season_year` | `INTEGER` | No | Cyclone season year (1900 - 2100) |
| `primary_basin` | `VARCHAR(20)` | No | `BOB`, `ARB`, `NIO`, etc. |
| `nature` | `VARCHAR(50)` | No | `TS` (Tropical Storm), `ET` (Extratropical), etc. |
| `created_at_utc` | `TIMESTAMPTZ` | No | Entity creation timestamp |

*Indexes:* Index on `(primary_basin, season_year) [ix_storms_basin_season]`.  
*Identity Note:* In Milestone F0.1 (Migration `002`), the legacy `UNIQUE(canonical_name, season_year, primary_basin)` constraint was removed to allow multiple unnamed depressions and distinct systems sharing names to coexist.

---

### 2.5 `storm_aliases`
Cross-agency mapping table reconciling different naming conventions and agency IDs.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key |
| `storm_id` | `UUID` | No | FK $\rightarrow$ `storms(id)` ON DELETE CASCADE |
| `source_agency` | `VARCHAR(50)` | No | `IMD`, `JTWC`, `IBTRACS`, `CMA`, `JMA`, etc. |
| `agency_storm_id`| `VARCHAR(100)` | No | Agency-specific ID (e.g., `BOB 01`, `01B`, IBTrACS SID `2020136N10087`) |
| `agency_storm_name`| `VARCHAR(100)` | Yes | Agency-specific name spelling |
| `matching_confidence`| `FLOAT` | No | Confidence score [0.0, 1.0] |
| `documented_evidence`| `TEXT` | Yes | Citation / rationale for storm reconciliation |

*Constraints:* `UNIQUE(source_agency, agency_storm_id) [uq_agency_storm_alias]`, `CHECK(matching_confidence >= 0.0 AND matching_confidence <= 1.0)`

---

### 2.6 `track_observations`
Core geospatial observation table storing synoptic locations and physical meteorological parameters.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key |
| `storm_id` | `UUID` | No | FK $\rightarrow$ `storms(id)` ON DELETE CASCADE |
| `source_asset_id` | `UUID` | No | FK $\rightarrow$ `source_assets(id)` ON DELETE RESTRICT |
| `source_agency` | `VARCHAR(50)` | No | Reporting agency (`IMD`, `JTWC`, etc.) |
| `source_record_id`| `VARCHAR(200)`| No | Deterministic source row identifier |
| `observation_time_utc`| `TIMESTAMPTZ`| No | Synoptic observation timestamp (Indexed) |
| `retrieval_time_utc`| `TIMESTAMPTZ`| No | Asset retrieval timestamp |
| `data_availability_time_utc`| `TIMESTAMPTZ`| Yes | Real-time release timestamp (nullable) |
| `is_retrospective_best_track`| `BOOLEAN`| No | `True` for post-season reanalysis |
| `is_superseded` | `BOOLEAN` | No | `True` if replaced by newer best-track asset (Migration 002) |
| `latitude` | `FLOAT` | No | Latitude in degrees `[-90.0, 90.0]` |
| `longitude` | `FLOAT` | No | Longitude in degrees `[-180.0, 180.0]` |
| `geom` | `GEOMETRY(Point, 4326)`| Yes | Spatial PostGIS point (Spatial Index) |
| `wind_speed_knots` | `FLOAT` | Yes | Standardized wind speed in knots `[0.0, 300.0]` |
| `original_wind_speed`| `FLOAT` | Yes | Speed as reported in source asset |
| `original_wind_unit`| `VARCHAR(20)` | Yes | `kt`, `m/s`, `km/h` |
| `averaging_period`| `VARCHAR(20)` | No | `3-min` (IMD), `1-min` (JTWC), `10-min` |
| `central_pressure_hpa`| `FLOAT` | Yes | Estimated minimum pressure `[800.0, 1080.0]` |
| `pressure_drop_hpa`| `FLOAT` | Yes | Environmental pressure deficit |
| `imd_category` | `VARCHAR(20)` | Yes | `LOW`, `D`, `DD`, `CS`, `SCS`, `VSCS`, `ESCS`, `SuCS` |
| `quality_flag` | `VARCHAR(50)` | No | `VALID`, `SUSPICIOUS`, `INTERPOLATED` |
| `raw_payload` | `JSONB / JSON` | Yes | Raw source fields |

*Constraints:*
- `CHECK(latitude >= -90.0 AND latitude <= 90.0)`
- `CHECK(longitude >= -180.0 AND longitude <= 180.0)`
- `CHECK(wind_speed_knots IS NULL OR (wind_speed_knots >= 0.0 AND wind_speed_knots <= 300.0))`
- `CHECK(central_pressure_hpa IS NULL OR (central_pressure_hpa >= 800.0 AND central_pressure_hpa <= 1080.0))`
- `UNIQUE(source_asset_id, source_record_id) [uq_track_asset_record]` (Deterministic row import idempotency)
- `UNIQUE(storm_id, source_agency, source_asset_id, observation_time_utc, source_record_id) [uq_storm_agency_asset_obs_record]`
- Spatial R-Tree Index on `geom`
- Composite Indexes on `(storm_id, observation_time_utc)` and `(source_agency, observation_time_utc)`

---

### 2.7 `data_quality_issues`
Tracks record-level anomalies, physical violations, and exception resolution status.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key |
| `source_asset_id` | `UUID` | Yes | FK $\rightarrow$ `source_assets(id)` ON DELETE SET NULL |
| `track_observation_id`| `UUID` | Yes | FK $\rightarrow$ `track_observations(id)` ON DELETE CASCADE |
| `severity` | `VARCHAR(20)` | No | `CRITICAL`, `WARNING`, `INFO` |
| `cause` | `VARCHAR(255)`| No | Description of rule failure |
| `details` | `JSONB / JSON` | Yes | Context payload (violating values, bounds) |
| `resolution_status`| `VARCHAR(50)` | No | `OPEN`, `RESOLVED`, `SUPPRESSED` |
| `created_at_utc` | `TIMESTAMPTZ` | No | Creation timestamp |

---

### 2.8 `dataset_snapshots`
Logs reproducible manifests for transformations, model training splits, and evaluation benchmarks.

| Column | Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | Primary Key |
| `snapshot_name` | `VARCHAR(150)`| No | Human-readable name (e.g., `nio_train_2000_2020`) |
| `transformation_version`| `VARCHAR(50)`| No | Pipeline version identifier |
| `manifest_sha256` | `VARCHAR(64)` | No | Hash of the generated manifest JSON |
| `total_samples` | `INTEGER` | No | Record count in this split |
| `filter_criteria` | `JSONB / JSON` | Yes | Criteria used to construct the snapshot |
| `manifest_uri` | `VARCHAR(1024)`| No | File path to stored manifest file |
| `created_at_utc` | `TIMESTAMPTZ` | No | Snapshot creation timestamp |

*Constraints:* `UNIQUE(snapshot_name, transformation_version, manifest_sha256)`

---

## 3. Migration and Recovery Procedures

### Migration History
1. `001_initial_schema`: Initial creation of PostGIS extensions, 8 canonical tables, check constraints, foreign keys, and indexes.
2. `002_storm_identity_and_safety`: Removed `uq_storm_canonical` from `storms`; added `is_superseded` to `track_observations`; added `uq_track_asset_record` and `uq_storm_agency_asset_obs_record` for deterministic row lineage.

### Running Migrations
```powershell
# Upgrade canonical research database to head
.venv\Scripts\alembic.exe upgrade head

# Upgrade isolated test database to head
$env:ALEMBIC_DB_URL = "postgresql+psycopg://vayumarg_user:vayumarg_dev_password@127.0.0.1:5433/vayumarg_test"
.venv\Scripts\alembic.exe upgrade head
Remove-Item Env:\ALEMBIC_DB_URL
```

### Safe Recovery from a Failed Migration
1. Inspect current applied revision:
   ```powershell
   .venv\Scripts\alembic.exe current
   ```
2. Roll back one revision safely:
   ```powershell
   .venv\Scripts\alembic.exe downgrade -1
   ```
3. In case of dirty state, resolve foreign-key blockers and re-run:
   ```powershell
   .venv\Scripts\alembic.exe upgrade head
   ```
