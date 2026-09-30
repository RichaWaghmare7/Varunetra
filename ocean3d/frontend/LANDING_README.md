# Landing Page — README
## Phase 7 of Ocean 3D Visualization Platform

`index.html` — the entry point, per Design Doc section 4.1 and App Flow
Doc section 2.1.

---

## What's on it

- **Hero:** full-screen, slowly-panning Cesium globe (Ion terrain/imagery,
  same token as the dashboard) framed on India's EEZ, dark gradient overlay
  for text legibility, headline + one-line description, two CTAs.
- **"What it shows"** — 4 cards: model fields, currents/SSH, Argo/glider
  markers, depth-profile charts.
- **"Who it's for"** — 3 cards: forecasters, researchers, students/public.
- **Standards strip** — INCOIS LAS, Copernicus Marine, Argo GDAC, OGC
  WMS/WCS, CF Conventions (per PRD section 7 data sources + section 5.5
  standards requirement).
- **Footer** — INCOIS/MoES branding + links to both app modes.

`Launch Platform` → `dashboard.html`. `Explore for Education` → `outreach.html`.
Both already link back to `index.html`'s sibling pages via their own nav (Phase 5/6).

---

## Design choices (and why)

- **The hero globe is decorative, not interactive** — camera input is
  disabled (`enableInputs = false`) so visitors can't accidentally drag it
  off-frame; it exists to set mood, not to be explored (that's what the
  "Launch Platform" button is for).
- **One motion moment**, not scattered effects: the headline/CTA fade-up on
  load, plus the continuous slow globe pan. No per-card hover animations,
  no scroll-triggered reveals — per the frontend design guidance against
  stacking generic motion.
- **`prefers-reduced-motion` respected** — both the hero fade-in and the
  globe rotation stop for users who've set that OS preference.
- Reused the same palette/type tokens as the dashboard and outreach pages
  (Inter, JetBrains Mono, navy/cyan/teal) so navigating between all three
  feels like one product, not three different builds.

---

## Known simplification

The hero uses a full Cesium `Viewer` instance for the rotating globe, which
is heavier than a lighter-weight decorative option (a pre-rendered video
loop, or a simpler WebGL sphere) would be. It was the fastest way to reuse
already-verified, working code from Phase 5/6 rather than building and
testing a second 3D approach. If load time on low-end devices becomes an
issue, swapping the hero for a lightweight looping video/canvas animation
is a quick follow-up (NFR-5 in the FRD asks for graceful degradation on
low-end hardware — this hasn't been tested on one specifically).

## Status: ✅ Phase 7 complete

## Next step
Say **"start phase 8"** for the Docker Compose deployment package (final phase).
