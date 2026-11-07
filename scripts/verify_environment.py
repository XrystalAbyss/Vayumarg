"""Environment, schema, and restart persistence verification script for Vayumarg F0."""

import os
import subprocess
import time
import uuid

os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from vayumarg.database.engine import (
    audit_database_integrity,
    check_database_connectivity,
    get_db_session,
    get_default_engine,
    verify_postgis_extension,
)
from vayumarg.database.schema import DataSource


def verify_all() -> None:
    print("=" * 70)
    print("VAYUMARG F0: SCIENTIFIC DATA FOUNDATION VERIFICATION")
    print("=" * 70)

    # 1. Connectivity Check
    engine = get_default_engine()
    conn_info = check_database_connectivity(engine)
    print(
        f"[+] Connectivity: {conn_info['status']} (Dialect: {conn_info['dialect']}, Version: {conn_info['server_version']})"
    )

    # 2. PostGIS Verification
    postgis_info = verify_postgis_extension(engine)
    print(
        f"[+] PostGIS Extension: {postgis_info['postgis_installed']} (Version: {postgis_info.get('version')})"
    )
    assert postgis_info["postgis_installed"] is True, "PostGIS extension must be active!"

    # 3. Insert Persistent Synthetic Fixture
    test_id = uuid.uuid4()
    with get_db_session(engine) as session:
        ds = DataSource(
            id=test_id,
            provider_name="PERSISTENCE_TEST_PROVIDER",
            dataset_name="PERSISTENCE_TEST_DATASET",
            version="1.0.0",
            citation="Synthetic test record for Docker restart verification",
        )
        session.add(ds)
        session.commit()
    print(f"[+] Inserted synthetic record {test_id} for restart persistence test.")

    # 4. Restart Docker Container
    print("[*] Restarting Docker PostGIS container: vayumarg-postgis...")
    subprocess.run(["docker", "restart", "vayumarg-postgis"], check=True)
    print("[*] Waiting 6 seconds for container health check...")
    time.sleep(6)

    # 5. Verify Record Persistence After Container Restart
    with get_db_session(engine) as session:
        queried = session.get(DataSource, test_id)
        assert queried is not None, "Record was lost across container restart!"
        print(f"[+] Restart persistence VERIFIED! Record {queried.id} survived container restart.")

        # Clean up synthetic test record
        session.delete(queried)
        session.commit()
        print("[+] Synthetic test record cleaned up successfully.")

    # 6. Audit Summary
    audit = audit_database_integrity(engine)
    print("\n[+] Audit Table Counts:")
    for tbl, count in audit["table_counts"].items():
        print(f"    - {tbl}: {count}")

    print("\n[SUCCESS] ALL F0 FOUNDATION CRITERIA VERIFIED SUCCESSFULLY.")


if __name__ == "__main__":
    verify_all()
