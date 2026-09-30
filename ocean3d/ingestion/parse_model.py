"""
parse_model.py
Extracts a single depth-slice, single time-step grid from a CF-convention
ocean model NetCDF file (e.g. Copernicus Marine GLOBAL_MULTIYEAR_PHY).

This mimics what the real `GET /model/slice?variable=&depth=&time=` FastAPI
endpoint will do against THREDDS/OPeNDAP via xarray -- except here it reads
a local file directly (no THREDDS server available in this environment).

Usage:
    python parse_model.py model.nc --variable thetao --depth 0 --time 2026-06-21 --out slice.json
    python parse_model.py model.nc --list-variables
    python parse_model.py model.nc --export-all --outdir ../data_samples

Variable name mapping (Copernicus short names -> our schema names):
    thetao -> temperature
    so     -> salinity
    uo, vo -> currents (u, v components)
    zos    -> ssh
    mlotst -> mixed_layer_depth
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr

VAR_MAP = {
    "temperature": "thetao",
    "salinity": "so",
    "u_current": "uo",
    "v_current": "vo",
    "ssh": "zos",
    "mixed_layer_depth": "mlotst",
}


def nearest_depth_index(ds, requested_depth):
    depths = ds["depth"].values
    idx = int(np.argmin(np.abs(depths - requested_depth)))
    return idx, float(depths[idx])


def extract_slice(ds, variable, depth, time_str, stride=1, decimals=2):
    """stride>1 downsamples the lat/lon grid (e.g. stride=4 keeps every 4th
    point) -- real production endpoint would serve full resolution; a browser
    demo bundling many slices needs a much smaller payload."""
    if variable not in VAR_MAP:
        raise ValueError(f"Unknown variable '{variable}'. Choose from {list(VAR_MAP)}")
    var = VAR_MAP[variable]
    if var not in ds:
        raise ValueError(f"Variable '{var}' not present in this file")

    da = ds[var].sel(time=time_str, method="nearest")

    if "depth" in da.dims:
        depth_idx, actual_depth = nearest_depth_index(ds, depth)
        da = da.isel(depth=depth_idx)
    else:
        actual_depth = None  # surface-only variable (e.g. zos, mlotst)

    if stride > 1:
        da = da.isel(latitude=slice(None, None, stride), longitude=slice(None, None, stride))

    grid = da.values.astype(float)
    grid = np.round(grid, decimals)
    grid = np.where(np.isnan(grid), None, grid)  # land/mask cells -> null

    lat_vals = ds["latitude"].values[::stride] if stride > 1 else ds["latitude"].values
    lon_vals = ds["longitude"].values[::stride] if stride > 1 else ds["longitude"].values

    return {
        "variable": variable,
        "requested_depth_m": depth,
        "actual_depth_m": actual_depth,
        "time": str(np.datetime_as_string(da["time"].values, unit="D")) if "time" in da.coords else time_str,
        "lat": np.round(lat_vals, 3).tolist(),
        "lon": np.round(lon_vals, 3).tolist(),
        "grid": grid.tolist(),  # shape [lat][lon], row-major, null = no data
        "units": ds[var].attrs.get("units", ""),
        "long_name": ds[var].attrs.get("long_name", ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Path to model NetCDF file")
    ap.add_argument("--variable", choices=list(VAR_MAP), default="temperature")
    ap.add_argument("--depth", type=float, default=0)
    ap.add_argument("--time", default=None, help="ISO date, e.g. 2026-06-21. Defaults to first time-step.")
    ap.add_argument("--out", default=None)
    ap.add_argument("--list-variables", action="store_true")
    ap.add_argument("--export-all", action="store_true",
                     help="Export every variable x every depth x every time-step (small file, for demo)")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--stride", type=int, default=1, help="Downsample grid every Nth point (demo bundling)")
    args = ap.parse_args()

    ds = xr.open_dataset(args.file)

    if args.list_variables:
        print("Available (mapped) variables:", list(VAR_MAP.keys()))
        print("Depths (m):", ds["depth"].values.tolist())
        print("Times:", [str(np.datetime_as_string(t, unit='D')) for t in ds["time"].values])
        print("Lat range:", float(ds["latitude"].min()), float(ds["latitude"].max()))
        print("Lon range:", float(ds["longitude"].min()), float(ds["longitude"].max()))
        return

    if args.export_all:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        times = [str(np.datetime_as_string(t, unit="D")) for t in ds["time"].values]
        # limit to a few representative depths so the demo bundle stays small
        depth_choices = [0, 10, 30]
        manifest = []
        for varname in VAR_MAP:
            if VAR_MAP[varname] not in ds:
                continue
            for t in times:
                depths_to_use = [None] if "depth" not in ds[VAR_MAP[varname]].dims else depth_choices
                for d in depths_to_use:
                    dd = d if d is not None else 0
                    try:
                        result = extract_slice(ds, varname, dd, t, stride=args.stride)
                    except Exception as e:
                        print(f"skip {varname}/{t}/{d}: {e}", file=sys.stderr)
                        continue
                    fname = f"slice_{varname}_{t}_{int(dd)}m.json"
                    with open(outdir / fname, "w") as fh:
                        json.dump(result, fh)
                    manifest.append({"variable": varname, "time": t, "depth_m": result["actual_depth_m"], "file": fname})
                    print(f"wrote {fname}", file=sys.stderr)
        with open(outdir / "model_manifest.json", "w") as fh:
            json.dump(manifest, fh, indent=2)
        return

    result = extract_slice(ds, args.variable, args.depth, args.time or str(ds["time"].values[0])[:10])
    out_path = args.out or "slice.json"
    with open(out_path, "w") as fh:
        json.dump(result, fh)
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
