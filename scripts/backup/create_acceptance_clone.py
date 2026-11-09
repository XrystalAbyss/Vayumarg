import psycopg

# Connect with autocommit to create database
conn = psycopg.connect(
    "host=127.0.0.1 port=5433 user=vayumarg_user dbname=postgres password=vayumarg_dev_password",
    autocommit=True,
)
with conn.cursor() as cur:
    # Drop clone if exists
    cur.execute("DROP DATABASE IF EXISTS vayumarg_acceptance_clone;")
    print("Dropped old clone if existed.")
    # Create clone from template vayumarg
    cur.execute("CREATE DATABASE vayumarg_acceptance_clone TEMPLATE vayumarg;")
    print("Created vayumarg_acceptance_clone from template vayumarg!")
conn.close()

# Verify clone tables and counts
clone_conn = psycopg.connect(
    "host=127.0.0.1 port=5433 user=vayumarg_user dbname=vayumarg_acceptance_clone password=vayumarg_dev_password"
)
with clone_conn.cursor() as cur:
    for tbl in ["storms", "track_observations", "storm_aliases", "satellite_granules", "satellite_processed_crops", "satellite_track_associations", "dataset_snapshots"]:
        cur.execute(f"SELECT count(*) FROM public.{tbl};")
        print(f"CLONE {tbl}: {cur.fetchone()[0]}")
clone_conn.close()
