# Frontend Dashboard — README
## Phase 5 of Ocean 3D Visualization Platform

`dashboard.html` — a single self-contained file (~670KB) you can open
directly in any browser or deploy to any static host. Built per the Design
Doc's visual language (deep navy/near-black, cyan-teal accents, glassmorphism
floating panels) and the App Flow Doc's dashboard layout.

---

## What's real vs. what's simplified

**Real:**
- The depth-slice grid you see is your actual uploaded Copernicus model
  data (temperature/salinity/SSH), embedded directly — not fake/random
  numbers. Colors are computed live from real values.
- The Argo profile chart (depth vs. temperature/salinity) uses real QC-good
  readings from your uploaded Argo files.
- Every control is functionally wired: variable selector, depth slider,
  time slider + play/pause, opacity slider, palette picker, min/max range
  override, log-scale toggle, layer/marker visibility toggles, marker
  click → profile panel.

**Simplified for this phase (flagged honestly, not hidden):**
1. **No true Three.js volumetric ray-marching yet.** The PRD asks for
   isosurface extraction and full water-column volumetric rendering. What's
   here is a 2D colored overlay per depth-level draped on the Cesium globe
   (real data, real colors, just not a 3D ray-marched volume). Adding actual
   Three.js volumetric rendering synced to the Cesium camera is a
   substantial separate build — recommend as a Phase 5b if you want it next.
2. **Argo marker positions are illustrative**, not real coordinates — same
   root cause flagged in Phases 1/4: the 3 uploaded Argo files had no floats
   over India that week. The profile *readings* (temperature/salinity by
   depth) are 100% real; only the plotted lat/lon is a placeholder inside
   the EEZ box, and the dashboard says so on-screen (bottom-left note).
3. **Data is embedded, not fetched from the live FastAPI backend.** Since
   this dashboard needs to run as a standalone file you can open anywhere
   (including offline), it bundles a small pre-extracted slice of data
   rather than calling `/model/slice` and `/floats/*` over the network. See
   "Wiring to the real backend" below for how to switch this.

---

## Try it
Open `dashboard.html` in a browser. Everything works client-side — no
server needed for this demo (Cesium's terrain/imagery calls out to Cesium
ion using the embedded token; nothing else needs network access).

---

## Wiring to the real backend (future step)

Right now `MODEL_BUNDLE` / `FLOATS_BUNDLE` are embedded JS constants. To
switch to live data from the Phase 3 FastAPI backend once it's deployed
somewhere reachable, replace `renderSlice()`'s bundle lookup with a fetch:
```js
const res = await fetch(`${API_BASE}/model/slice?variable=${state.variable}&depth=${depth}&time=${time}`);
const slice = await res.json();
```
and similarly for `/floats/nearby` and `/floats/{id}/profile`. The response
shapes already match exactly (same field names) since `model_source.py` and
this dashboard's bundle format were designed together.

---

## Rebuilding the data bundles

If you get real India-region Argo data (see Phase 1/4 notes) or a new
model file, regenerate the embedded bundles:
```bash
cd frontend/build_scripts
python generate_bundles.py \
  --model /path/to/new_model.nc \
  --instruments ../../data_samples/instruments_sample.json \
  --profiles ../../data_samples/profiles_sample.json \
  --outdir ../data_bundles

python inject_data.py \
  --model ../data_bundles/model_bundle.json \
  --floats ../data_bundles/floats_bundle.json \
  --token YOUR_CESIUM_ION_TOKEN \
  --out ../dashboard.html
```
Both scripts were run and verified in this session (21 model slices, 15
floats — output confirmed to match).

---

## Folder contents

| File | Purpose |
|---|---|
| `dashboard.html` | The finished, working dashboard — open this one |
| `dashboard_template.html` | Same file with `{{MODEL_BUNDLE_JSON}}` etc. placeholders, for rebuilding |
| `build_scripts/generate_bundles.py` | Regenerates the two JSON data bundles from source NetCDF/JSON |
| `build_scripts/inject_data.py` | Injects bundles + Cesium token into the template → final HTML |
| `data_bundles/model_bundle.json` | Embedded model slices (21 combos: temp/salinity × 3 depths × 3 days, + SSH × 3 days) |
| `data_bundles/floats_bundle.json` | Embedded Argo profile data (15 floats) |

## Status: ✅ Phase 5 complete (with the 3 scope notes above tracked, not hidden)

## Files added in Phase 6
See `OUTREACH_README.md` for the outreach/education mode (`outreach.html`)
— simplified UI + guided tours, same engine and real data as this dashboard.

## Next step
Say **"start phase 7"** for the landing page + remaining visual polish.
