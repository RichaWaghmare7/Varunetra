# Backend API — README
## Phase 3 of Ocean 3D Visualization Platform

FastAPI backend implementing the 3 core endpoints from
`Tech_Stack_Doc` / `FRD` / `Backend_Schema_Doc`.

**✅ This was actually built AND tested end-to-end in this session** — not
just written. A local Postgres+PostGIS instance was installed, your real
sample Argo data was loaded into it via `schema.sql` +
`ingestion/load_to_postgres.py`, and all 3 endpoints were hit with real
requests against real data (your uploaded model file + your uploaded Argo
files). Results are in the "Verified Test Results" section below.

---

## Folder structure

```
backend/
├── requirements.txt
├── .env.example          <- copy to .env, fill in your real DATABASE_URL
├── schema.sql             <- run once against Supabase to create tables
└── app/
    ├── main.py             <- FastAPI app, mounts routers
    ├── db.py               <- asyncpg connection pool (reads DATABASE_URL)
    ├── model_source.py     <- reads model NetCDF via xarray (stand-in for THREDDS)
    └── routers/
        ├── model.py         <- GET /model/meta, GET /model/slice
        └── floats.py        <- GET /floats/nearby, GET /floats/{id}/profile
```

---

## Endpoints

| Endpoint | Purpose | Backed by |
|---|---|---|
| `GET /health` | Liveness check | — |
| `GET /model/meta` | Discover available variables/depths/times/bounds | NetCDF file via xarray |
| `GET /model/slice?variable=&depth=&time=&stride=` | Depth-slice grid for the Three.js shader | NetCDF file via xarray |
| `GET /floats/nearby?bbox=&time_start=&time_end=` | Latest position of instruments in a region/time window (map markers) | PostGIS `profiles`+`instruments` |
| `GET /floats/{id}/profile?variable=` | Depth-vs-variable series for the click-to-inspect chart | PostGIS `profiles` |

Interactive Swagger docs at `/docs` once running.

---

## Run it

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # then edit .env with your real Supabase URL + NetCDF path
export $(cat .env | xargs)
uvicorn app.main:app --reload --port 8000
```

Then load real data:
```bash
psql "$DATABASE_URL" -f schema.sql
python ../ingestion/load_to_postgres.py \
  --instruments ../data_samples/instruments_sample.json \
  --profiles ../data_samples/profiles_sample.json \
  --db-url "$DATABASE_URL"
```

---

## ⚠️ Important: THREDDS is not stood up yet

`model_source.py` currently reads the NetCDF file **directly with xarray**
(pointed at by `MODEL_NC_PATH`) instead of going through a THREDDS/OPeNDAP
server, because no THREDDS instance exists yet in this build.

**This is intentional and matches the Tech Stack Doc's own design** — xarray
can open a remote OPeNDAP URL exactly the same way it opens a local file:
```python
# today (local file):
ds = xr.open_dataset(MODEL_NC_PATH)
# once THREDDS is running (Phase 8 / deployment):
ds = xr.open_dataset("http://<thredds-host>/thredds/dodsC/<dataset>.nc")
```
Only `model_source.py`'s dataset-opening line changes. `routers/model.py`
and the frontend contract stay identical — this was designed so swapping
in real THREDDS later is a one-line change, not a rewrite.

---

## Verified Test Results (this session, against your real uploaded files)

**`/model/meta`** →
```json
{"variables":["temperature","salinity","u_current","v_current","ssh","mixed_layer_depth"],
 "depths_m":[0.49,...,55.76],"times":["2026-06-21","2026-06-22","2026-06-23"],
 "bounds":{"lat_min":-1.83,"lat_max":29.5,"lon_min":63.25,"lon_max":96.08}}
```

**`/model/slice?variable=temperature&depth=0&time=2026-06-21`** → real 38×40
grid of sea surface temperature (India EEZ region), e.g. `29.455°C, 29.4°C,
29.3°C...` — units `degrees_C`, confirmed non-null.

**`/floats/nearby?bbox=-180,-90,180,90&...`** → 15 real Argo floats returned
with real lat/lon/instrument_id (using global bbox since your 3 sample
files had no India-region floats that week — see `ingestion/README.md`).

**`/floats/2902893/profile`** → real depth-vs-temperature/salinity series,
96–140 readings, e.g. `{"depth_m": 2.1, "value": 30.137}` for temperature.

---

## Known gaps for production (tracked, not blocking the demo)

- CORS is wide open (`allow_origins=["*"]`) — restrict to your real frontend domain before deploying.
- No auth on any route yet — Admin routes (Phase 7) will need it; public read routes (`/model/*`, `/floats/*`) can likely stay open per PRD ("no login for public visualization").
- `asyncpg` pool is created lazily on first request, not pre-warmed at startup — fine for a demo, add a startup warm-up for production.

## Status: ✅ Phase 3 complete — tested end-to-end
