# Outreach / Education Mode — README
## Phase 6 of Ocean 3D Visualization Platform

`outreach.html` — the simplified public/student-facing mode from the
PRD/Design Doc, sharing the **same rendering engine and real data** as the
operational dashboard (FR-6.3), with a friendlier UI (FR-6.1) and guided
tours (FR-6.2).

---

## What changed vs. the operational dashboard

| Operational (`dashboard.html`) | Outreach (`outreach.html`) |
|---|---|
| Dropdown variable selector | 3 big icon buttons (🌡️ Temperature, 💧 Salinity, 🌊 Sea Height) |
| Colorbar editor (palette/min-max/log) | Removed — auto colors only |
| Layer/marker toggles, opacity slider | Removed — always on |
| Time slider + play | Removed from free-explore (still used inside tours) |
| — | **Guided Tours panel** (new) |
| — | **Caption bar** with Next/Exit (new) |

Both pages link to each other (top-right corner) — matches the landing
page's "Launch Platform" / "Explore for Education" fork from the App Flow
Doc, ahead of Phase 7 actually building that landing page.

---

## The 3 guided tours (FR-6.2)

1. **The Monsoon Current** — steps through real SSH data across all 3
   embedded days, then shows sea surface temperature, with captions
   explaining what's changing and why it matters operationally.
2. **A Float's Journey** — built dynamically from the first float in
   `FLOATS_BUNDLE`, not hard-coded: pulls that float's actual shallowest
   and deepest temperature readings into the caption text, so the story
   always matches whatever real data is loaded.
3. **Layers of the Ocean** — walks through temperature at 0m → 10m → 30m
   to introduce the thermocline concept, then contrasts with salinity to
   show it's driven by different forces (rainfall/runoff, not depth alone).

Tours drive the same `renderSlice()` / camera-fly functions the free-explore
mode uses — nothing tour-specific is faked.

---

## Known simplification carried over from Phase 5

Same as the operational dashboard: no true Three.js volumetric rendering
yet (2D depth-slice overlay instead), and Argo marker positions are
illustrative placements within the EEZ (see Phase 1/5 notes) — the float
readings used in "A Float's Journey" are real, only its plotted position
is a placeholder.

## Status: ✅ Phase 6 complete

## Next step
Say **"start phase 7"** for the landing page + final visual polish.
