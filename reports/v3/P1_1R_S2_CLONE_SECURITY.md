# VAYUMARG 3.0 — P1.1R-S2 ACCEPTANCE CLONER SECURITY HARDENING

**Document ID:** `reports/v3/P1_1R_S2_CLONE_SECURITY.md`  
**Milestone:** P1.1R-S2 Source Hardening & Injection Defense  
**Security Lead:** Senior PostgreSQL Security Engineer & Software Verification Specialist  
**Date:** 2026-11-09  
**Artifact Script:** `scripts/backup/create_acceptance_clone.py`  
**Test Suite:** `scripts/backup/test_clone_safeguards.py` (10 Test Cases, 100% Passed)  

---

## 1. Vulnerability Assessment of Prior Implementation

An independent code audit of the acceptance cloning script revealed three structural deficiencies:
1. **F-String SQL Assembly:** Dynamic identifiers in `DROP DATABASE "{clone_db}";`, `CREATE DATABASE "{clone_db}" TEMPLATE "{source_db}";`, and table counts were assembled using Python f-strings rather than AST-safe SQL abstractions.
2. **Permissive Regular Expressions:** The previous allowlist regex (`r".*_acceptance_clone$"`) used unanchored prefixes (`.*`), permitting malicious characters (such as semicolons, spaces, quotes, or control characters) prior to the suffix.
3. **Unvalidated Source Identifier:** The source database argument was accepted directly without validation against an explicit source allowlist or verification of primary database schema markers.

---

## 2. Hardened Architecture & Security Guardrails

The script `scripts/backup/create_acceptance_clone.py` was completely refactored with defense-in-depth protections:

### 2.1 Strict Identifier Validation via `re.fullmatch`
All database names are validated against strict POSIX/PostgreSQL naming rules:
```python
DB_NAME_REGEX = re.compile(r"^[a-z][a-z0-9_]{1,62}$")
```
Any name containing uppercase letters, hyphens, spaces, quotes, semicolons, or null bytes is immediately rejected with an `InvalidDatabaseNameError`.

### 2.2 AST-Safe Parameterization via `psycopg.sql.Identifier`
All SQL statements containing database or table names are compiled through `psycopg.sql.Identifier` and `psycopg.sql.SQL`:
```python
drop_stmt = sql.SQL("DROP DATABASE {}").format(sql.Identifier(clean_clone))
cur.execute(drop_stmt)

create_stmt = sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
    sql.Identifier(clean_clone),
    sql.Identifier(clean_source),
)
cur.execute(create_stmt)
```
This guarantees that libpq treats the identifier as a lexical token, mathematically preventing SQL injection regardless of input.

### 2.3 Explicit Source and Target Allowlisting
- **Source Database Allowlist:** Strictly limited to known templates:
  ```python
  ALLOWED_SOURCE_DATABASES = {"vayumarg", "vayumarg_test"}
  ```
- **Clone Target Allowlist:** Must conform strictly to disposable suffixes:
  ```python
  ALLOWED_CLONE_TARGET_PATTERNS = [
      re.compile(r"^vayumarg_acceptance_clone$"),
      re.compile(r"^[a-z][a-z0-9_]*_acceptance_clone$"),
      re.compile(r"^[a-z][a-z0-9_]*_clone$"),
      re.compile(r"^[a-z][a-z0-9_]*_test$"),
  ]
  ```
- **Protected System Blacklist:** Under no condition can `vayumarg`, `postgres`, `template0`, `template1`, or `template_postgis` be overwritten or targeted.

### 2.4 Fail-if-Exists Policy & Two-Phase Destruction Gate
By default, if the target clone already exists, the script raises `ExistingCloneRefusalError` and aborts. Overwriting an existing clone requires **two separate explicit opt-in flags**:
1. `--force-replace`
2. `--confirm-destructive-replace`

If `--force-replace` is passed without `--confirm-destructive-replace`, the execution is halted with `DestructiveConfirmationRequiredError`.

### 2.5 Primary Database Identity Verification
Before initiating any template clone, the script queries `pg_database` to ensure:
- `source_db` exists and is connectable (`datallowconn = true`).
- `source_db` is not marked as a template (`datistemplate = false`).
- If `source_db == 'vayumarg'`, verifies the existence of primary tables (`storms`, `track_observations`).

---

## 3. Automated Test Suite Execution Evidence

The test suite in `scripts/backup/test_clone_safeguards.py` was executed with `.venv\Scripts\pytest.exe -v`:

| Test Name | Attack / Failure Scenario Tested | Expected Behavior | Result |
| :--- | :--- | :--- | :--- |
| `test_sql_injection_in_source_name` | Injections: `vayumarg; DROP TABLE...`, `vayumarg' OR 1=1...`, `/*comment*/`, `\x00` | Rejects with `InvalidDatabaseNameError` | **PASSED** |
| `test_sql_injection_in_clone_name` | Injections: `clone; DROP DATABASE...`, `clone' OR '1'='1`, `$(rm -rf /)` | Rejects with `InvalidDatabaseNameError` | **PASSED** |
| `test_names_with_quotes_and_semicolons` | Special characters: `"vayumarg"`, `'vayumarg'`, `db;name`, `db name`, `db-name` | Rejects with `InvalidDatabaseNameError` | **PASSED** |
| `test_unauthorized_source_databases` | Sources: `postgres`, `template0`, `other_research_db` | Rejects with `UnauthorizedSourceError` | **PASSED** |
| `test_protected_target_databases` | Targets: `vayumarg`, `postgres`, `template0`, `template1` | Rejects with `UnauthorizedTargetError` | **PASSED** |
| `test_identical_source_and_destination` | Source: `vayumarg_test`, Target: `vayumarg_test` | Rejects with `CloneSecurityError` | **PASSED** |
| `test_existing_clone_refusal_without_flags` | Existing clone targeted without `--force-replace` | Rejects with `ExistingCloneRefusalError` | **PASSED** |
| `test_existing_clone_refusal_without_destructive_confirmation` | `--force-replace` without `--confirm-destructive-replace` | Rejects with `DestructiveConfirmationRequiredError` | **PASSED** |
| `test_inaccessible_or_nonexistent_source` | Connection to inaccessible host or invalid port | Rejects with `CloneSecurityError` | **PASSED** |
| `test_failed_authentication` | Invalid password provided | Rejects with `AuthenticationFailureError` | **PASSED** |

**Summary:** 10 passed, 0 failed in 0.47 seconds.

