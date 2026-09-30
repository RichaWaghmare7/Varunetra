# Ingestion Layer — README
## Phase 1 of Ocean 3D Visualization Platform

This folder parses the raw NetCDF files (Argo floats + Copernicus ocean
model) into the row/grid formats the rest of the system expects, per
`Backend_Schema_Doc_Ocean_3D_Visualization_Platform.md`.

---

## Files

| File | What it does |
|---|---|
| `parse_argo.py` | Reads Argo GDAC profile `.nc` files → rows matching the `instruments` + `profiles` PostGIS tables |
| `parse_model.py` | Reads a CF-convention ocean model `.nc` file → depth-slice JSON grids matching what the `GET /model/slice` API will return |

---

## `parse_argo.py`

**What it does:** for every profile in the file, keeps only QC-good
(`QC flag 1` or `2`) temperature/salinity readings, converts to long-format
rows (one row per depth-level per variable), and groups them by float
(`PLATFORM_NUMBER`) into an `instruments` table.

**Run it:**
```bash
python parse_argo.py D20260621_prof_0.nc D20260622_prof_0.nc --bbox 63 -2 96 30 --outdir ./out
```
- `--bbox LON_MIN LAT_MIN LON_MAX LAT_MAX` — filters to a region (default: rough India EEZ box)
- Outputs `instruments.json` and `profiles.json` in `--outdir`

**⚠️ Important finding from the 3 files you uploaded:**
`D20260621_prof_0.nc`, `D20260622_prof_0.nc`, `D20260623_prof_0.nc` are
**global** Argo GDAC daily index files (the `_0` suffix means "chunk 0 of
the day's global file"), not India-specific extracts. None of the profiles
in these 3 files happen to fall inside the India EEZ box on those dates —
floats were in the Pacific/Southern Ocean/Atlantic instead.

This does **not** mean the parser is broken — it correctly filters by
bounding box. It means: for a real India-only dataset, pull from Ifremer's
**Indian Ocean regional directory** instead of the global daily index:
```
ftp://ftp.ifremer.fr/ifremer/argo/geo/indian_ocean/
```
or query the GDAC index by region before downloading.

For this demo, I re-ran the parser with a global bbox so we'd have *real*
Argo data to build and test the profile-chart feature against — see
`data_samples/instruments_sample.json` / `profiles_sample.json` (15 floats,
~8,000 depth readings, real temperature + salinity values). These floats are
NOT in the Indian Ocean — swap in real regional files before production use.

---

## `parse_model.py`

**What it does:** opens the Copernicus model file, maps short variable
names (`thetao`, `so`, `uo`, `vo`, `zos`, `mlotst`) to schema names
(`temperature`, `salinity`, `u_current`, `v_current`, `ssh`,
`mixed_layer_depth`), and extracts a single depth/time slice as a JSON grid
— exactly what the real `/model/slice` FastAPI endpoint will compute
on-demand from THREDDS/OPeNDAP.

**Run it:**
```bash
# inspect what's inside
python parse_model.py model.nc --list-variables

# one slice
python parse_model.py model.nc --variable temperature --depth 0 --time 2026-06-21 --out slice.json

# export a demo bundle (small, downsampled) for the frontend
python parse_model.py model.nc --export-all --stride 3 --outdir ../data_samples/model_slices
```
- `--stride N` downsamples the grid (keeps every Nth lat/lon point) — only
  needed for bundling many slices into a lightweight browser demo. The real
  backend endpoint would serve full resolution on request, not pre-export
  everything.

**✅ Good news on the model file:** `cmems_mod_glo_phy_my_0_083deg_...nc`
covers **exactly** the India EEZ region already (lat -1.83° to 29.5°,
lon 63.25° to 96.08° = Arabian Sea + Bay of Bengal), 3 days, 19 depth
levels, and has all the variables the PRD asks for (temperature, salinity,
currents, SSH, mixed layer depth). No region-filtering needed for this one.

---

## Output Schema Reference

`instruments.json` → `instruments` table:
```json
{"instrument_id": "2902917", "instrument_type": "argo", "deployment_date": "...", "status": "active", "metadata": {...}}
```

`profiles.json` → `profiles` table (long format, one row per reading):
```json
{"instrument_id": "2902917", "lat": 12.3, "lon": 88.1, "depth_m": 10.4, "observed_at": "2026-06-21T...", "variable": "temperature", "value": 28.6, "qc_flag": 1, "source_file": "..."}
```

Model slice JSON → what `/model/slice` returns:
```json
{"variable": "temperature", "actual_depth_m": 0.49, "time": "2026-06-21", "lat": [...], "lon": [...], "grid": [[28.1, 28.3, null, ...], ...], "units": "degC"}
```
`grid` is `[lat][lon]`; `null` = land/no-data cell.

---

## Status: ✅ Phase 1 complete

- [x] Argo parser built + tested against your 3 uploaded files
- [x] Model slicer built + tested against your uploaded Copernicus file
- [x] Demo-sized sample data generated for Phase 5 (frontend)
- [ ] Real India-region Argo files still needed for production (see finding above)

---
---

# Phase 4 — Loading into Supabase

## ⚠️ Why you run this step, not me

This build sandbox cannot resolve `db.udcjdlmxzrxvzzbnvvnf.supabase.co` —
confirmed with a direct DNS test (only npm/pypi/github-type registries are
network-whitelisted here). So I:

1. Built the ingestion script (`load_to_postgres.py`)
2. Installed a **real local Postgres+PostGIS** in this sandbox
3. Ran the exact same script against it, end-to-end, with your real sample
   Argo data — verified below
4. Packaged it as `run_ingestion.sh` for you to run against your actual
   Supabase, from your machine/network

The logic is proven. Only the network path (your machine → Supabase) is
untested by me, because I can't reach it.

## Files added this phase

| File | Purpose |
|---|---|
| `run_ingestion.sh` | One command: applies `schema.sql` + loads sample data + verifies |
| `load_to_postgres.py` | Core loader — upserts `instruments`, inserts `profiles`, logs the run in `ingestion_jobs` |

## Run it (on your machine, not in this chat)

```bash
export DATABASE_URL="postgresql://postgres:<your-password>@db.udcjdlmxzrxvzzbnvvnf.supabase.co:5432/postgres"
cd ocean3d/ingestion
bash run_ingestion.sh
```
Needs `psql` installed locally (`brew install postgresql` / `apt install postgresql-client`) and Python 3 (the script auto-installs `psycopg2-binary`).

## What it logs

Every run now writes a row to `ingestion_jobs` (status: `running` →
`success`/`failed`, with row counts and error messages) — exactly what the
Admin Panel (Phase 7) will read to show ingestion history, per FR-7.2.

## Verified Test Results (this session, against a real local Postgres+PostGIS)

```
Upserted 15 instruments
Inserted 8037 profile rows

ingestion_jobs:
 job_id | source_id    | status  | rows_ingested | started_at                 | finished_at
      1 | argo_ifremer | success | 8037          | 2026-09-11 19:37:32.596218 | 2026-09-11 19:37:32.602786
```
Post-load sanity checks also confirmed `instruments` (15 rows,
`instrument_type='argo'`) and `profiles` (temperature + salinity rows,
spatially indexed) are queryable by the `/floats/nearby` and
`/floats/{id}/profile` endpoints — already tested live against this same
data in Phase 3.

## Status: ✅ Phase 4 complete (pipeline proven end-to-end; awaiting your run against live Supabase)
