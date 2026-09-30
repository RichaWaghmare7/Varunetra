-- schema.sql
-- PostGIS + admin metadata schema, per Backend_Schema_Doc_Ocean_3D_Visualization_Platform.md
-- Run once against your Supabase (or any Postgres+PostGIS) instance:
--   psql "postgresql://<user>:<password>@<host>:5432/postgres" -f schema.sql

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- 2.1 instruments — master record per physical Argo float/Glider/CTD
-- ============================================================
CREATE TABLE IF NOT EXISTS instruments (
    instrument_id     TEXT PRIMARY KEY,
    instrument_type   TEXT NOT NULL,          -- 'argo', 'glider', 'ctd', 'bgc', etc.
    deployment_date   TIMESTAMP,
    status            TEXT DEFAULT 'active',  -- 'active', 'inactive', 'lost'
    metadata          JSONB DEFAULT '{}'::jsonb
);

-- ============================================================
-- 2.2 profiles — one row per depth reading per instrument per timestamp
-- (long format: easy to add a new variable without ALTER TABLE)
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
    profile_id        BIGSERIAL PRIMARY KEY,
    instrument_id     TEXT REFERENCES instruments(instrument_id),
    location          GEOGRAPHY(POINT, 4326) NOT NULL,
    depth_m           NUMERIC NOT NULL,
    observed_at       TIMESTAMP NOT NULL,
    variable          TEXT NOT NULL,          -- 'temperature', 'salinity', 'chlorophyll', 'oxygen', etc.
    value             NUMERIC NOT NULL,
    qc_flag           SMALLINT DEFAULT 1,
    source_file       TEXT
);

CREATE INDEX IF NOT EXISTS idx_profiles_location   ON profiles USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_profiles_inst_time   ON profiles (instrument_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_profiles_var_time    ON profiles (variable, observed_at);

-- ============================================================
-- 2.3 instrument_tracks — glider trajectories (optional)
-- ============================================================
CREATE TABLE IF NOT EXISTS instrument_tracks (
    track_id        BIGSERIAL PRIMARY KEY,
    instrument_id   TEXT REFERENCES instruments(instrument_id),
    path            GEOGRAPHY(LINESTRING, 4326),
    start_time      TIMESTAMP,
    end_time        TIMESTAMP
);

-- ============================================================
-- 3.1 data_sources — registry enabling plugin-style extensibility
-- ============================================================
CREATE TABLE IF NOT EXISTS data_sources (
    source_id       TEXT PRIMARY KEY,          -- e.g. 'argo_ifremer', 'incois_las_temp'
    source_type     TEXT NOT NULL,             -- 'model' or 'observation'
    parser_class    TEXT NOT NULL,
    location_uri    TEXT,
    enabled         BOOLEAN DEFAULT TRUE,
    schedule_cron   TEXT,
    created_at      TIMESTAMP DEFAULT now()
);

-- ============================================================
-- 3.2 ingestion_jobs — log of every ingestion run (Admin Panel)
-- ============================================================
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id          BIGSERIAL PRIMARY KEY,
    source_id       TEXT REFERENCES data_sources(source_id),
    started_at      TIMESTAMP DEFAULT now(),
    finished_at     TIMESTAMP,
    status          TEXT,                      -- 'success', 'failed', 'partial'
    rows_ingested   INTEGER DEFAULT 0,
    error_message   TEXT
);

-- ============================================================
-- 3.3 users — admin/internal users only
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT DEFAULT 'viewer',     -- 'admin', 'researcher', 'viewer'
    created_at      TIMESTAMP DEFAULT now()
);

-- seed the two data sources we already have parsers for
INSERT INTO data_sources (source_id, source_type, parser_class, location_uri, enabled, schedule_cron)
VALUES
    ('argo_ifremer', 'observation', 'parse_argo.py', 'ftp://ftp.ifremer.fr/ifremer/argo/geo/indian_ocean/', TRUE, '0 3 * * *'),
    ('copernicus_model', 'model', 'parse_model.py', 'https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030', TRUE, '0 2 * * *')
ON CONFLICT (source_id) DO NOTHING;
