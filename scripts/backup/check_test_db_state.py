import psycopg

conn = psycopg.connect("host=127.0.0.1 port=5433 user=vayumarg_user dbname=vayumarg_test password=vayumarg_dev_password")
with conn.cursor() as cur:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
    tables = [r[0] for r in cur.fetchall()]
    print("TABLES in vayumarg_test:", tables)

    for tbl in tables:
        try:
            cur.execute(f"SELECT count(*) FROM public.{tbl};")
            count = cur.fetchone()[0]
            print(f"  {tbl}: {count} rows")
        except Exception as e:
            print(f"  {tbl}: error ({e})")
conn.close()
