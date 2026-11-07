from pathlib import Path
import re

sql_path = Path('data/backups/vayumarg_pre_f1_1_backup.sql')
assert sql_path.exists(), f'SQL backup not found at {sql_path}!'
sz = sql_path.stat().st_size
print(f"SQL Dump Path: {sql_path.as_posix()}")
print(f"Size: {sz} bytes ({sz / (1024*1024):.2f} MiB / {sz / 1e6:.2f} MB)")

tables = []
postgis_found = False
auth_keywords = []

with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
    for i in range(500):
        line = f.readline()
        if not line:
            break
        if 'PostgreSQL database dump' in line:
            print('Dump Header:', line.strip())
        if 'CREATE EXTENSION' in line and 'postgis' in line.lower():
            postgis_found = True
        m = re.match(r'CREATE TABLE (?:IF NOT EXISTS )?([a-zA-Z0-9_\.\"]+)', line, re.IGNORECASE)
        if m:
            tables.append(m.group(1))

with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.startswith('COPY ') or line.startswith('CREATE TABLE '):
            parts = line.split()
            if len(parts) > 2:
                tables.append(parts[1])
        if any(k in line.upper() for k in ['ALTER USER', 'CREATE ROLE', 'CREATE USER', 'ENCRYPTED PASSWORD']):
            auth_keywords.append(line.strip()[:60])

unique_tables = sorted(list(set(tables)))
print(f"PostGIS Extension present: {postgis_found}")
print(f"Discovered Tables / Data sections ({len(unique_tables)}): {unique_tables[:20]}")
print(f"Auth/Credential Statements found: {len(auth_keywords)}")
if auth_keywords:
    print(f"Sample auth statements: {len(auth_keywords)} detected")
else:
    print("Zero credential or password statements detected (Clean schema & data dump).")
