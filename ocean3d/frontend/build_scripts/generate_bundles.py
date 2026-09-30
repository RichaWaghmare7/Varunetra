"""
generate_bundles.py — regenerates the two small JSON bundles the dashboard
embeds directly (model_bundle.json, floats_bundle.json).

Run this whenever the underlying model file or Argo sample changes.

Usage:
    python generate_bundles.py \
        --model /path/to/model.nc \
        --instruments ../../data_samples/instruments_sample.json \
        --profiles ../../data_samples/profiles_sample.json \
        --outdir .
"""
import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ingestion"))
from parse_model import extract_slice  # noqa: E402
import xarray as xr  # noqa: E402

TIMES = None  # discovered from file
DEPTHS = [0, 10, 30]
VARIABLES_WITH_DEPTH = ["temperature", "salinity"]


def build_model_bundle(model_path, stride=6):
    global TIMES
    ds = xr.open_dataset(model_path)
    import numpy as np
    TIMES = [str(np.datetime_as_string(t, unit="D")) for t in ds["time"].values]

    bundle = {}
    for v in VARIABLES_WITH_DEPTH:
        for t in TIMES:
            for d in DEPTHS:
                key = f"{v}_{t}_{d}m"
                bundle[key] = extract_slice(ds, v, d, t, stride=stride)
    for t in TIMES:
        key = f"ssh_{t}_0m"
        bundle[key] = extract_slice(ds, "ssh", 0, t, stride=stride)
    return bundle


def build_floats_bundle(instruments_path, profiles_path, seed=42):
    with open(instruments_path) as f:
        instruments = json.load(f)
    with open(profiles_path) as f:
        profiles = json.load(f)

    by_inst = defaultdict(list)
    for p in profiles:
        by_inst[p["instrument_id"]].append(p)

    random.seed(seed)
    out = []
    for inst in instruments:
        iid = inst["instrument_id"]
        rows = by_inst.get(iid, [])
        if not rows:
            continue
        latest_time = max(r["observed_at"] for r in rows)
        latest_rows = [r for r in rows if r["observed_at"] == latest_time]
        series = defaultdict(list)
        for r in latest_rows:
            series[r["variable"]].append({"depth_m": r["depth_m"], "value": r["value"]})
        for k in series:
            series[k] = sorted(series[k], key=lambda x: x["depth_m"])[:60]

        # NOTE: demo_lat/demo_lon are illustrative placements inside the India
        # EEZ box -- swap this block out once real India-region Argo files
        # are used (then just use rows[0]['lat']/['lon'] directly).
        demo_lat = round(random.uniform(6, 20), 3)
        demo_lon = round(random.uniform(70, 90), 3)

        out.append({
            "instrument_id": iid,
            "instrument_type": inst["instrument_type"],
            "demo_lat": demo_lat,
            "demo_lon": demo_lon,
            "real_lat": rows[0]["lat"],
            "real_lon": rows[0]["lon"],
            "observed_at": latest_time,
            "series": series,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--instruments", required=True)
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--stride", type=int, default=6)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    model_bundle = build_model_bundle(args.model, stride=args.stride)
    with open(outdir / "model_bundle.json", "w") as f:
        json.dump(model_bundle, f)
    print(f"model_bundle.json: {len(model_bundle)} slices", file=sys.stderr)

    floats_bundle = build_floats_bundle(args.instruments, args.profiles)
    with open(outdir / "floats_bundle.json", "w") as f:
        json.dump(floats_bundle, f)
    print(f"floats_bundle.json: {len(floats_bundle)} floats", file=sys.stderr)


if __name__ == "__main__":
    main()
