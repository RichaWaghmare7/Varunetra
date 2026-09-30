# Deployment — README
## Phase 8 of Ocean 3D Visualization Platform (final phase)

Docker Compose package per the Deployment Plan doc: 3 containers
(`backend`, `frontend`, `scheduler`) on one internal network, Postgres
staying external on your Supabase (not a local container, per the Phase
3/4 decision already made).

---

## ⚠️ What was verified vs. what wasn't (read this first)

**No `docker` binary is available in this build sandbox** — so I could not
run `docker build` / `docker-compose up` here. What I *did* verify:

| Check | Result |
|---|---|
| `docker-compose.yml` YAML syntax | ✅ Parsed successfully with PyYAML, both services structurally sound |
| `infra/nginx.conf` syntax | ✅ Verified with a real installed `nginx -t` (adapted proxy target for the test, since `backend` isn't resolvable outside compose) |
| Every file path referenced by the Dockerfiles/compose actually exists | ✅ Checked directly (`backend/requirements.txt`, `frontend/*.html`, `infra/nginx.conf`, etc.) |
| Full `docker build` / container boot | ❌ Not possible here — **you should run this once before trusting it in production** |

Recommend running `docker compose config` (validates + shows resolved
config) and `docker compose up --build` yourself as the first real test.

---

## Services

| Service | What it does | Port |
|---|---|---|
| `backend` | FastAPI app from Phase 3, built from `backend/Dockerfile` | internal :8000 |
| `frontend` | Nginx serving `index.html`/`dashboard.html`/`outreach.html`, reverse-proxies `/api/*` to backend | :80 (host) |
| `scheduler` | Cron container running daily ingestion (Deployment Plan step 6) | — |

Postgres = your Supabase instance, reached via `DATABASE_URL`. THREDDS is
not containerized yet — `backend/app/model_source.py` reads a local NetCDF
file (mounted via the `data/` volume) until a real THREDDS server exists.

---

## Run it

```bash
cp .env.example .env
# edit .env: real DATABASE_URL, and put your model file at ./data/model.nc

docker compose config      # sanity-check the resolved config first
docker compose up --build
```
Then visit `http://localhost` (or your `HTTP_PORT`).

---

## Frontend → backend wiring note

The Phase 5-7 HTML files currently use **embedded sample data**, not live
fetches to `/api/*` (see `frontend/README.md`). The Nginx reverse proxy is
ready and tested for when you switch the dashboard/outreach JS to call
`fetch('/api/model/slice?...')` instead — that's a small JS change in
`dashboard.html`/`outreach.html`, not an infra change.

---

## Data refresh (Deployment Plan step 6)

`infra/crontab` runs the ingestion script daily at 03:00. As shipped, it
only **re-loads** whatever `instruments.json`/`profiles.json` are in
`./data/` — it does not itself download new files from Ifremer/Copernicus.
Add a download step (wget/curl or the Copernicus Marine API client) before
the ingestion line in `infra/crontab` once you're pulling live upstream
data instead of the bundled sample.

---

## Monitoring & backups (Deployment Plan step 7 — not automated here)

- All 3 containers have `HEALTHCHECK`/`healthcheck` blocks — `docker compose ps` will show unhealthy containers.
- Supabase handles Postgres backups on its own schedule/plan — check your Supabase project's backup settings rather than adding a custom backup job, since you're not running Postgres yourself.

## Status: ✅ Phase 8 complete (config verified; full container boot needs to happen on your machine/server where Docker is available)

---

# 🎉 All 8 phases complete
See the top-level `README.md` for the full project status table and the
running list of known scope gaps (all flagged honestly, not hidden):
1. True Three.js volumetric ray-marching (Phase 5) — currently a real-data 2D depth-slice overlay
2. Argo marker positions are illustrative (Phases 1/4/5/6) — your uploaded files had no India-region floats that week
3. Full Docker container boot untested (this phase) — sandbox has no Docker
