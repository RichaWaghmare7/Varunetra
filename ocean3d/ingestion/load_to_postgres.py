"""
load_to_postgres.py
Loads the JSON output of parse_argo.py (instruments.json, profiles.json)
into a Postgres+PostGIS database matching schema.sql.

This is the script that must run from a machine that can reach your
Supabase instance (this build sandbox cannot reach supabase.co directly).

Usage:
    export DATABASE_URL="postgresql://postgres:<password>@<host>:5432/postgres"
    python load_to_postgres.py --instruments instruments.json --profiles profiles.json
"""
import argparse
import json
import os
import sys

import psycopg2
from psycopg2.extras import execute_values


def load(conn, instruments_path, profiles_path, source_id="argo_ifremer"):
    with open(instruments_path) as f:
        instruments = json.load(f)
    with open(profiles_path) as f:
        profiles = json.load(f)

    cur = conn.cursor()

    # --- log ingestion_jobs start (per FR-7.2 / FR-8.3) ---
    cur.execute(
        "INSERT INTO ingestion_jobs (source_id, status) VALUES (%s, 'running') RETURNING job_id",
        (source_id,),
    )
    job_id = cur.fetchone()[0]
    conn.commit()

    try:
        # --- instruments (upsert) ---
        inst_rows = [
            (i["instrument_id"], i["instrument_type"], i.get("deployment_date"),
             i.get("status", "active"), json.dumps(i.get("metadata", {})))
            for i in instruments
        ]
        execute_values(cur, """
            INSERT INTO instruments (instrument_id, instrument_type, deployment_date, status, metadata)
            VALUES %s
            ON CONFLICT (instrument_id) DO UPDATE SET
                status = EXCLUDED.status,
                metadata = EXCLUDED.metadata
        """, inst_rows)
        print(f"Upserted {len(inst_rows)} instruments", file=sys.stderr)

        # --- profiles (insert; PostGIS point built from lat/lon) ---
        prof_rows = [
            (p["instrument_id"], p["lon"], p["lat"], p["depth_m"], p["observed_at"],
             p["variable"], p["value"], p.get("qc_flag", 1), p.get("source_file"))
            for p in profiles
        ]
        execute_values(cur, """
            INSERT INTO profiles (instrument_id, location, depth_m, observed_at, variable, value, qc_flag, source_file)
            VALUES %s
        """, prof_rows, template="(%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s, %s, %s, %s, %s, %s)")
        print(f"Inserted {len(prof_rows)} profile rows", file=sys.stderr)

        cur.execute(
            "UPDATE ingestion_jobs SET status='success', finished_at=now(), rows_ingested=%s WHERE job_id=%s",
            (len(prof_rows), job_id),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.execute(
            "UPDATE ingestion_jobs SET status='failed', finished_at=now(), error_message=%s WHERE job_id=%s",
            (str(e), job_id),
        )
        conn.commit()
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", required=True)
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL"))
    args = ap.parse_args()

    if not args.db_url:
        print("ERROR: set DATABASE_URL env var or pass --db-url", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(args.db_url)
    try:
        load(conn, args.instruments, args.profiles)
    finally:
        conn.close()
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
