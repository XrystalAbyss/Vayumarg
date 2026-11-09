# Windows 11 Local Setup & Operational Runbook

**Target Environment:** Windows 11 Home / Pro (x64) with PowerShell 5.1 / PowerShell 7  
**Platform:** Vayumarg Scientific Data Foundation (Milestone F0.1)  

---

## 1. Prerequisites Checklist

Ensure the following tools are installed on your Windows machine:
1. **Python 3.12:** Verified installation (e.g., `CPython 3.12.10`).
2. **uv Package Manager:** Available on system PATH (`uv --version`).
3. **Docker Desktop:** Installed with WSL2 engine backend.
4. **Git for Windows:** Installed and accessible in PowerShell.

---

## 2. Step-by-Step Environment Bootstrap

### Step 2.1: Clone and Open PowerShell in Project Root
```powershell
cd C:\Users\astra\Desktop\Project\Vayumarg
```

### Step 2.2: Create Python 3.12 Virtual Environment with uv
```powershell
uv venv --python 3.12 .venv
.venv\Scripts\activate
```

### Step 2.3: Install Dependencies in Editable Mode
```powershell
uv pip install -e ".[dev]"
```

---

## 3. Docker PostGIS Service Configuration

### Step 3.1: Verify WSL2 Distro Configuration
If Docker Desktop shows WSL mount errors, set `docker-desktop` as the active WSL distribution:
```powershell
wsl -s docker-desktop
```

### Step 3.2: Launch Docker Desktop
```powershell
explorer.exe "C:\Program Files\Docker\Docker\Docker Desktop.exe"
# Wait approximately 10-15 seconds for daemon initialization
docker ps
```

### Step 3.3: Environment File Configuration
Copy the template configuration:
```powershell
Copy-Item .env.example .env
```

> [!NOTE]
> The PostGIS container is configured to expose host port **`5433`** (`5433:5432`) to prevent conflicts with any pre-existing PostgreSQL instances on Windows port 5432.

### Step 3.4: Spin Up PostGIS Container
```powershell
docker compose up -d
docker compose ps
```
Verify the container output displays `vayumarg-postgis ... Up (healthy)`.

---

## 4. Database Identity & Test Isolation

Vayumarg maintains strict separation between environments:
- **Canonical Research Database (`vayumarg`):** Preserves persistent scientific records.
- **Isolated Test Database (`vayumarg_test`):** Used strictly for automated integration tests and disposable fixtures.

### Step 4.1: Apply Schema Migrations
```powershell
# Upgrade canonical research database to head (Migration 002)
.venv\Scripts\alembic.exe upgrade head

# Upgrade isolated test database to head
$env:ALEMBIC_DB_URL = "postgresql+psycopg://vayumarg_user:$env:POSTGRES_PASSWORD@127.0.0.1:5433/vayumarg_test"
.venv\Scripts\alembic.exe upgrade head
Remove-Item Env:\ALEMBIC_DB_URL
```

### Step 4.2: Run Vayumarg CLI Health Checks
```powershell
.venv\Scripts\vayumarg.exe check-db
.venv\Scripts\vayumarg.exe counts
.venv\Scripts\vayumarg.exe migrations
.venv\Scripts\vayumarg.exe audit
```

---

## 5. Automated Backup & Recovery Demonstration

Vayumarg provides an automated, containerized backup and recovery utility using PostgreSQL's native `pg_dump` and `psql` tools:
```powershell
# Execute repeatable backup and restore demonstration with disposable fixtures
.venv\Scripts\python.exe scripts\backup_restore_demo.py
```

Manual Backup Command:
```powershell
docker exec vayumarg-postgis pg_dump -U vayumarg_user -d vayumarg_test -f /tmp/backup.sql
docker cp vayumarg-postgis:/tmp/backup.sql ./data/interim/manual_backup.sql
```

Manual Restore Command:
```powershell
docker cp ./data/interim/manual_backup.sql vayumarg-postgis:/tmp/restore.sql
docker exec vayumarg-postgis psql -U vayumarg_user -d vayumarg_test -f /tmp/restore.sql
```

---

## 6. Windows Security & WDAC Architectural Findings

- **Investigation:** During milestone F0, a transient `ImportError: DLL load failed while importing _util_cy: An Application Control policy has blocked this file` was observed.
- **Root Cause & Technical Fact:** In SQLAlchemy 2.0+, `_util_cy.pyd` is compiled via Cython. SQLAlchemy does **not** recognize the legacy environment variable `DISABLE_SQLALCHEMY_CEXT`. The transient error occurred because Windows Defender / SmartScreen temporarily locked the newly written binary DLL in `.venv` immediately after download.
- **Verification:** Fresh Python processes without any environment variable load SQLAlchemy and report `sqlalchemy.engine._util_cy._is_compiled() == True`.
- **Pure-Python Fallback:** Should an enterprise Windows machine enforce a strict WDAC rule blocking `.pyd` binaries, SQLAlchemy ships with pure-Python fallbacks (`_util_cy.py`, `_result_cy.py`, etc.) that execute seamlessly if the `.pyd` binary is omitted.

---

## 7. Running Automated Tests

Run the full pytest suite (both unit tests and real PostGIS integration tests):
```powershell
.venv\Scripts\pytest.exe
```

Run only unit tests:
```powershell
.venv\Scripts\pytest.exe -m unit
```

Run only PostGIS integration tests (strictly isolated against `vayumarg_test`):
```powershell
.venv\Scripts\pytest.exe -m integration
```
