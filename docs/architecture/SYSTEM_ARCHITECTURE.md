# Vayumarg System Architecture (Milestone F0)

**Project:** Vayumarg — AI/ML Decision-Support System for Tropical Cyclones  
**Problem Statement:** SIH26070 | Team VortexA  
**Status:** Approved Architecture (Milestone F0 Frozen)  

---

## 1. Architectural Philosophy

Vayumarg is built on four core architectural tenets:
1. **Decoupled Analytical Modules:** Module A (Satellite-based current-state classification and intensity estimation) and Module B (Multi-step track and future wind forecasting) are completely decoupled. **Module B does not depend on Module A predictions.**
2. **Scientific Integrity & Agency Preserving:** Meteorological conventions (specifically IMD's 3-minute sustained wind standard versus JTWC/NHC's 1-minute standard) are preserved in their native forms without ad-hoc, unvalidated conversion.
3. **Immutable Lineage & Auditability:** Every observation maps to a physical source asset with an immutable SHA-256 hash, an explicit UTC timestamp, and a data availability timestamp.
4. **Relational vs. Large Array Separation:** Relational structures (metadata, tracks, quality issues, manifests) reside in PostgreSQL/PostGIS. Dense multi-band satellite rasters (INSAT HDF5/NetCDF) remain on high-speed disk storage referenced by cryptographic manifests.

---

## 2. Decoupled Modular Architecture

```mermaid
flowchart TD
    subgraph DataSources["Data Sources (External)"]
        IMD["IMD RSMC New Delhi (3-min MSW)"]
        JTWC["JTWC / IBTrACS (1-min MSW)"]
        MOSDAC["ISRO MOSDAC (INSAT-3D/3DR)"]
    end

    subgraph DataFoundation["Vayumarg Scientific Data Foundation (F0)"]
        Ingestion["Ingestion & Transaction Manager"]
        QualityVal["Quality & Convention Validator"]
        DB[(PostgreSQL 16 + PostGIS 3.4)]
        ManifestStore["Cryptographic Manifest Registry (SHA-256)"]
        DiskStore["Large Raster Storage (HDF5 / NetCDF)"]
    end

    subgraph ModuleA["Module A: Current-State Estimation"]
        SatPreproc["Satellite Preprocessing & Dvorak Features"]
        IntClass["Intensity Classification Model"]
        ModAOut["Current-State Intensity Contract"]
    end

    subgraph ModuleB["Module B: Independent Track Forecasting"]
        TrackPrep["Track Sequence Preprocessing"]
        TrackModel["Spatio-Temporal Track Predictor"]
        ModBOut["Future Track & Intensity Contract"]
    end

    IMD --> Ingestion
    JTWC --> Ingestion
    MOSDAC --> Ingestion
    Ingestion --> QualityVal
    QualityVal --> DB
    QualityVal --> ManifestStore
    MOSDAC -. Raw Arrays .-> DiskStore

    DB --> SatPreproc
    DiskStore --> SatPreproc
    SatPreproc --> IntClass
    IntClass --> ModAOut

    DB --> TrackPrep
    TrackPrep --> TrackModel
    TrackModel --> ModBOut
```

---

## 3. Database Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    data_sources ||--o{ source_assets : "provides"
    data_sources ||--o{ ingestion_runs : "audits"
    source_assets ||--o{ track_observations : "contains"
    source_assets ||--o{ data_quality_issues : "originates"
    source_assets ||--o| ingestion_runs : "processed_by"
    storms ||--o{ storm_aliases : "known_as"
    storms ||--o{ track_observations : "tracked_by"
    track_observations ||--o{ data_quality_issues : "flags"

    data_sources {
        uuid id PK
        string provider_name
        string dataset_name
        string version
        text citation
        string license
        datetime created_at_utc
    }

    source_assets {
        uuid id PK
        uuid data_source_id FK
        string artifact_uri
        string sha256_checksum
        bigint file_size_bytes
        string asset_type
        datetime retrieval_time_utc
        json asset_metadata
    }

    ingestion_runs {
        uuid id PK
        uuid data_source_id FK
        uuid source_asset_id FK
        datetime started_at_utc
        datetime completed_at_utc
        string status
        int records_read
        int records_inserted
        int records_rejected
        text error_details
    }

    storms {
        uuid id PK
        string canonical_name
        int season_year
        string primary_basin
        string nature
        datetime created_at_utc
    }

    storm_aliases {
        uuid id PK
        uuid storm_id FK
        string source_agency
        string agency_storm_id
        string agency_storm_name
        float matching_confidence
        text documented_evidence
    }

    track_observations {
        uuid id PK
        uuid storm_id FK
        uuid source_asset_id FK
        string source_agency
        string source_record_id
        datetime observation_time_utc
        datetime retrieval_time_utc
        datetime data_availability_time_utc
        boolean is_retrospective_best_track
        float latitude
        float longitude
        geometry geom
        float wind_speed_knots
        string averaging_period
        float central_pressure_hpa
        string imd_category
        string quality_flag
    }

    data_quality_issues {
        uuid id PK
        uuid source_asset_id FK
        uuid track_observation_id FK
        string severity
        string cause
        json details
        string resolution_status
        datetime created_at_utc
    }

    dataset_snapshots {
        uuid id PK
        string snapshot_name
        string transformation_version
        string manifest_sha256
        int total_samples
        json filter_criteria
        string manifest_uri
        datetime created_at_utc
    }
```

---

## 4. Software Stack Specification

| Component | Selected Technology | Version | Rationale |
| :--- | :--- | :--- | :--- |
| **Language Runtime** | Python (CPython) | 3.12.10 | Modern type system, enhanced performance, long-term support. |
| **Environment & Package Mgmt** | uv | 0.12.21 | Extremely fast virtual environment and dependency lock tool. |
| **Relational / Geospatial DB** | PostgreSQL + PostGIS | PostgreSQL 16.4 / PostGIS 3.4.3 | Canonical standard for spatial indexing, R-Tree indices, and SRID 4326 geometry operations. |
| **ORM & Database Driver** | SQLAlchemy 2 + psycopg (v3) | SQLAlchemy 2.1.6, psycopg 3.3.6 | Modern 2.0-style mapped columns, strict typing, high-performance async/sync binary driver. |
| **Schema Migrations** | Alembic | 1.20.1 | Version-controlled, reproducible schema DDL transitions. |
| **Data Contracts & Validation**| Pydantic v2 | 2.14.2 | High-throughput data parsing and strict type constraints. |
| **Geospatial & Numerics** | Shapely, NumPy, pandas | Shapely 2.2.0, NumPy 2.5.4, pandas 3.1.0 | Standard scientific computing and computational geometry stack. |
| **CLI & Interface** | Typer + Rich | Typer 0.27.3, Rich 15.0.0 | User-friendly, auditable command-line interface. |
| **Test Suite** | pytest | 9.2.0 | Automated testing with isolated unit and integration markers. |
| **Linting & Code Quality** | Ruff | 0.17.3 | Ultra-fast linter and code formatter. |

