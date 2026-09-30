"""
parse_argo.py
Parses Argo float NetCDF profile files (GDAC format) into rows matching
the `instruments` + `profiles` PostGIS schema from Backend_Schema_Doc.

Usage:
    python parse_argo.py <input1.nc> <input2.nc> ... --out profiles.json
    python parse_argo.py D20260621_prof_0.nc --bbox 63 -2 96 30

Output: two JSON files
    instruments.json  -> rows for the `instruments` table
    profiles.json      -> rows for the `profiles` table (long format:
                           one row per instrument/depth/time/variable)

Only keeps QC-flagged "good" data (QC flag '1' = good, '2' = probably good).
Filters to a bounding box if --bbox is given (default: India EEZ approx box).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr

GOOD_QC = {"1", "2"}

# Approx India EEZ bounding box (lon_min, lat_min, lon_max, lat_max)
# Loosely covers Arabian Sea + Bay of Bengal. Refine with real EEZ polygon
# (Marine Regions gazetteer id 8480) for production use.
DEFAULT_BBOX = (30.0, -10.0, 100.0, 25.0)


def qc_ok(qc_val):
    if qc_val is None:
        return True
    try:
        s = qc_val.decode() if isinstance(qc_val, bytes) else str(qc_val)
    except Exception:
        return True
    return s.strip() in GOOD_QC


def parse_file(path, bbox, source_type="argo"):
    ds = xr.open_dataset(path)
    n_prof = ds.dims.get("N_PROF", 0)

    instruments = {}
    profiles = []

    lon_min, lat_min, lon_max, lat_max = bbox

    for i in range(n_prof):
        lat = float(ds["LATITUDE"].values[i])
        lon = float(ds["LONGITUDE"].values[i])

        if not (lon_min <= lon <= lon_max and lat_min <= lat <= lat_max):
            continue  # outside region of interest

        platform = ds["PLATFORM_NUMBER"].values[i]
        platform = platform.decode().strip() if isinstance(platform, bytes) else str(platform).strip()

        juld = ds["JULD"].values[i]
        observed_at = str(np.datetime_as_string(juld, unit="s"))

        if platform not in instruments:
            instruments[platform] = {
                "instrument_id": platform,
                "instrument_type": source_type,
                "deployment_date": observed_at,
                "status": "active",
                "metadata": {"source_file": Path(path).name},
            }

        pres = ds["PRES"].values[i]
        temp = ds["TEMP"].values[i] if "TEMP" in ds else None
        psal = ds["PSAL"].values[i] if "PSAL" in ds else None
        pres_qc = ds["PRES_QC"].values[i] if "PRES_QC" in ds else None
        temp_qc = ds["TEMP_QC"].values[i] if "TEMP_QC" in ds else None
        psal_qc = ds["PSAL_QC"].values[i] if "PSAL_QC" in ds else None

        n_levels = pres.shape[0]
        for lvl in range(n_levels):
            depth = pres[lvl]
            if np.isnan(depth):
                continue
            if not qc_ok(pres_qc[lvl] if pres_qc is not None else None):
                continue

            if temp is not None and not np.isnan(temp[lvl]) and qc_ok(temp_qc[lvl] if temp_qc is not None else None):
                profiles.append({
                    "instrument_id": platform,
                    "lat": lat, "lon": lon,
                    "depth_m": round(float(depth), 2),
                    "observed_at": observed_at,
                    "variable": "temperature",
                    "value": round(float(temp[lvl]), 4),
                    "qc_flag": 1,
                    "source_file": Path(path).name,
                })

            if psal is not None and not np.isnan(psal[lvl]) and qc_ok(psal_qc[lvl] if psal_qc is not None else None):
                profiles.append({
                    "instrument_id": platform,
                    "lat": lat, "lon": lon,
                    "depth_m": round(float(depth), 2),
                    "observed_at": observed_at,
                    "variable": "salinity",
                    "value": round(float(psal[lvl]), 4),
                    "qc_flag": 1,
                    "source_file": Path(path).name,
                })

    ds.close()
    return list(instruments.values()), profiles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="Argo .nc profile files")
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("LON_MIN", "LAT_MIN", "LON_MAX", "LAT_MAX"),
                     default=DEFAULT_BBOX)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    all_instruments = {}
    all_profiles = []

    for f in args.files:
        print(f"Parsing {f} ...", file=sys.stderr)
        insts, profs = parse_file(f, tuple(args.bbox))
        for inst in insts:
            all_instruments.setdefault(inst["instrument_id"], inst)
        all_profiles.extend(profs)
        print(f"  -> {len(insts)} instruments, {len(profs)} profile rows in bbox", file=sys.stderr)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with open(outdir / "instruments.json", "w") as fh:
        json.dump(list(all_instruments.values()), fh, indent=2)
    with open(outdir / "profiles.json", "w") as fh:
        json.dump(all_profiles, fh, indent=2)

    print(f"\nTOTAL: {len(all_instruments)} instruments, {len(all_profiles)} profile rows", file=sys.stderr)
    print(f"Written to {outdir}/instruments.json and {outdir}/profiles.json", file=sys.stderr)


if __name__ == "__main__":
    main()
