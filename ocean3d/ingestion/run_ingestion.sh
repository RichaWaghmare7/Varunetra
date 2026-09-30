#!/usr/bin/env bash
# run_ingestion.sh
# One-shot: create schema (if not already) + load sample Argo data into your
# Supabase Postgres+PostGIS instance.
#
# WHY YOU RUN THIS, NOT ME: my build sandbox cannot resolve/reach
# db.udcjdlmxzrxvzzbnvvnf.supabase.co (only npm/pypi/github registries are
# whitelisted in its network). This script is tested logic (verified against
# a local Postgres+PostGIS in Phase 3) — you just need to run it from a
# machine/network that can reach Supabase (your laptop, a server, etc).
#
# Usage:
#   export DATABASE_URL="postgresql://postgres:<password>@<host>:5432/postgres"
#   bash run_ingestion.sh
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: set DATABASE_URL first, e.g.:"
  echo '  export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.YOURPROJECT.supabase.co:5432/postgres"'
  exit 1
fi

echo "== Step 1/3: applying schema.sql =="
psql "$DATABASE_URL" -f ../backend/schema.sql

echo "== Step 2/3: loading sample Argo data (instruments + profiles) =="
pip install psycopg2-binary --quiet
python3 load_to_postgres.py \
  --instruments ../data_samples/instruments_sample.json \
  --profiles ../data_samples/profiles_sample.json \
  --db-url "$DATABASE_URL"

echo "== Step 3/3: verifying =="
psql "$DATABASE_URL" -c "SELECT instrument_type, count(*) FROM instruments GROUP BY instrument_type;"
psql "$DATABASE_URL" -c "SELECT variable, count(*) FROM profiles GROUP BY variable;"

echo ""
echo "Done. Sanity-check with:"
echo '  psql "$DATABASE_URL" -c "SELECT * FROM profiles LIMIT 5;"'
