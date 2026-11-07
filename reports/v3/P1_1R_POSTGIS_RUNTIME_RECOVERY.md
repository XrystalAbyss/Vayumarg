# VAYUMARG 3.0 — P1.1R POSTGIS RUNTIME RECOVERY & INFRASTRUCTURE AUDIT

## 1. Runtime Environment Investigation

A systematic host audit was conducted to evaluate local database availability, port bindings, PostGIS spatial extensions, and Docker container services.

### Port & Service Mapping
| Port | Bound Process / Service | Status | PostGIS Installed? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **5432** | Native Windows PostgreSQL 16 Service (`postgresql-x64-16`) | Running (`PID 6312`) | **NO** (`0` postgis extension files in `C:\Program Files\PostgreSQL\16\share\extension`) | Standard relational PostgreSQL without GIS binaries (`postgis-3.dll`, etc.). |
| **5433** | Docker Compose Target (`postgis/postgis:16-3.4`) | **STOPPED / DOWN** | **YES** (Inside container image) | The official project configuration (`docker-compose.yml`) routes Vayumarg to port 5433 to avoid port collisions with native PostgreSQL 5432. |

### Docker Desktop & WSL2 Daemon Status
- Service `com.docker.service` (Docker Desktop Service) is in state `Stopped` on Windows.
- Starting the Docker service on Windows requires elevated Administrator / UAC permissions (`access denied` without privilege escalation).
- WSL2 distribution `Ubuntu` reports `Failed to attach disk 'ext4.vhdx': ERROR_FILE_NOT_FOUND`, indicating the local WSL2 virtual disk was decoupled or removed, preventing unprivileged CLI startup of Docker Desktop.

---

## 2. GeoAlchemy2 & Spatial Extension Requirements

An evaluation was performed to test whether SQLite with SpatiaLite could serve as a local fallback for the database-dependent gate tests:

1. **Schema Dependency**: `TrackObservation` defines spatial geometry column:
   ```python
   geom = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
   ```
2. **PostGIS Function Dependency**: GeoAlchemy2 executes PostGIS extension management functions upon table creation:
   ```sql
   SELECT RecoverGeometryColumn('track_observations', 'geom', 4326, 'POINT', 2);
   ```
3. **Execution Result**: When attempting execution against an in-memory or file-based SQLite database without the custom C-extension `mod_spatialite.dll`, SQLite throws:
   ```text
   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such function: RecoverGeometryColumn
   ```
4. **Scientific Invariant**: Substituting a mock geometry type or stripping `Geometry` definitions would violate scientific database integrity. Therefore, the spatial schema must only run against an authentic PostGIS environment.

---

## 3. Containerized PostGIS Specification & CI Recovery

The canonical PostGIS runtime specification is preserved in `docker-compose.yml` and `.github/workflows/ci.yml`:

```yaml
services:
  postgis:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_USER: vayumarg
      POSTGRES_PASSWORD: vayumarg_secure_password
      POSTGRES_DB: vayumarg
    ports:
      - "5433:5432"
    volumes:
      - postgis_data:/var/lib/postgresql/data
```

### Reproducible Startup Procedure
When running with appropriate administrator privileges or in containerized CI:
```powershell
docker compose up -d postgis
.venv\Scripts\pytest.exe tests/integration/ tests/unit/test_f2_4_gate_c1r_metadata_closure.py
```
In GitHub Actions CI (`.github/workflows/ci.yml`), an unprivileged service container starts `postgis/postgis:16-3.4` with automated health checks, enabling full execution of the 15 database-dependent tests.

