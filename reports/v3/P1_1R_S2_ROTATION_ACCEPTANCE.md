# VAYUMARG 3.0 — P1.1R-S2 POSTGRESQL CREDENTIAL ROTATION & PREFLIGHT AUDIT

**Document ID:** `reports/v3/P1_1R_S2_ROTATION_ACCEPTANCE.md`  
**Milestone:** P1.1R-S2 Credential Rotation & Final Security Closure  
**Lead Engineer:** Senior PostgreSQL Security Engineer & Scientific Software Auditor  
**Date:** 2026-11-09  
**Status:** **ROTATION_REQUIRED (Interactive Owner Action Pending)**  

---

## 1. Executive Summary & Security Policy

In accordance with strict security standards:
1. The automated agent has **NOT** automatically mutated the active database credentials.
2. The previously unsafe rotation snippet (which printed cleartext passwords in command lines) has been **permanently deprecated**.
3. All sensitive credentials are strictly omitted from command-line arguments, reports, transcripts, and Git tracking.
4. Preflight inspection of the running database container, network bindings, and database backups was completed non-destructively.
5. A safe, interactive, libpq-supported `\password` protocol is provided for the repository owner to execute in a trusted local terminal.

---

## 2. Preflight Inspection Evidence

### 2.1 PostGIS Container Identity & Administrative Role
Inspection of the running Docker daemon confirmed:
- **Container Name:** `vayumarg-postgis`
- **Container ID:** `9c9c474ab228`
- **Image:** `postgis/postgis:16-3.4`
- **Status:** Healthy (`Up 2+ hours`)
- **Persistent Volume:** `vayumarg_pgdata` mounted at `/var/lib/postgresql/data`

Role enumeration via `psql -c "\du"` confirmed:
```
                               List of roles
   Role name   |                         Attributes                         
---------------+------------------------------------------------------------
 vayumarg_user | Superuser, Create role, Create DB, Replication, Bypass RLS
```
> [!IMPORTANT]
> The database has **only one user**: `vayumarg_user`, which serves as the superuser and owner of all databases (`postgres`, `template_postgis`, `vayumarg`, `vayumarg_acceptance_clone`, `vayumarg_test`). A separate `postgres` role does **not** exist.

### 2.2 Network Exposure & Port Binding
- **Current Container Port Mapping:** `0.0.0.0:5433->5432/tcp`, `[::]:5433->5432/tcp`.
- **Finding:** The container is currently listening on all network interfaces.
- **Remediation:** `docker-compose.yml` has been updated to `127.0.0.1:${POSTGRES_PORT:-5433}:5432` to restrict network exposure strictly to local loopback upon container restart.

### 2.3 Research Database Backup Verification
A preflight check of the backup repository was conducted without modifying any files:
- **File:** `data/backups/vayumarg_pre_f1_1_backup.sql`
- **Physical Size:** 42,071,784 bytes (40.1 MB)
- **Integrity Checksum (SHA-256):** `ca49ff0dde29e6c7bc04fd48b145f8d66813638750001540fd6325e707b9a1ac`
- **Status:** Valid, accessible, unmodified.

### 2.4 Local Applications Dependent on Role `vayumarg_user`
1. **Local `.env`**: Central environment configuration ignored by Git.
2. **FastAPI Application Config**: `src/vayumarg/core/config.py` (reads `DATABASE_URL` via environment).
3. **Database Migrations Engine**: `migrations/env.py` (reads `DATABASE_URL` / `ALEMBIC_DB_URL`).
4. **Database Acceptance Cloner**: `scripts/backup/create_acceptance_clone.py` (reads `POSTGRES_PASSWORD`).

---

## 3. Interactive Password Rotation Protocol (Safe Terminal Procedure)

The repository owner must execute the password change directly inside the container using PostgreSQL's native interactive password entry, which masks user typing and never logs the secret to bash/PowerShell history.

### Step 1: Open an Interactive Terminal
Run the following command in PowerShell or cmd:
```powershell
docker exec -it vayumarg-postgis psql -U vayumarg_user -d postgres
```

### Step 2: Issue the Protected Interactive `\password` Command
At the `postgres=#` prompt, type:
```sql
\password vayumarg_user
```
PostgreSQL will prompt:
```
Enter new password: <type new password>
Enter it again: <confirm new password>
```
Type `\q` and press Enter to exit `psql`.

### Step 3: Update Local `.env` Configuration
Open your local ignored `C:\Users\astra\Desktop\Project\Vayumarg\.env` file in an editor and update the password:
```ini
POSTGRES_USER=vayumarg_user
POSTGRES_PASSWORD=<your_new_password>

DATABASE_URL=postgresql+psycopg://vayumarg_user:<your_new_password>@127.0.0.1:5433/vayumarg
TEST_DATABASE_URL=postgresql+psycopg://vayumarg_user:<your_new_password>@127.0.0.1:5433/vayumarg_test
```
*(Save and close `.env`. Never commit `.env` to Git).*

### Step 4: Apply Loopback Binding (Optional / Recommended)
To apply the hardened `127.0.0.1:5433:5432` loopback binding defined in `docker-compose.yml`, run:
```powershell
docker compose up -d
```
*(This briefly restarts the container in 2 seconds; persistent volume `vayumarg_pgdata` is preserved).*

---

## 4. Post-Rotation Verification Checklist

Once the owner has completed Steps 1–3 above, verify the new credential:

1. **Verify New Credential Authenticates:**
   ```powershell
   .venv\Scripts\python.exe -c "import psycopg, os; from vayumarg.core.config import settings; print('Connected:', bool(psycopg.connect(settings.DATABASE_URL.replace('+psycopg', ''), connect_timeout=3)))"
   ```
2. **Verify Old Exposed Credential Fails:**
   Ensure connection with the old compromised password raises `AuthenticationFailureError` / `password authentication failed`.
3. **Verify Research Database Integrity:**
   ```powershell
   .venv\Scripts\vayumarg.exe check-db
   ```
   (Must report 1,860 storms and 68,095 track points intact).
4. **Verify Acceptance Clone Creation:**
   ```powershell
   .venv\Scripts\python.exe scripts/backup/create_acceptance_clone.py --force-replace --confirm-destructive-replace
   ```

---

## 5. Current Gate Verdict

### **`ROTATION_REQUIRED`**
The preflight audit, backup verification, and safe rotation procedures are complete. Automated release publication is paused pending the owner's interactive execution of Step 2 and Step 3 in their local terminal.
