"""
app/model_source.py

Serves model depth-slices by reading a local CF-convention NetCDF file with
xarray. This is a drop-in stand-in for what the real backend will do
against THREDDS/OPeNDAP (per Tech_Stack_Doc): the FastAPI route logic
(routers/model.py) doesn't change at all when you swap this for a real
`xr.open_dataset("http://<thredds-host>/thredds/dodsC/<dataset>.nc")` call —
only this file changes.

Set MODEL_NC_PATH env var to the NetCDF file to serve.
"""
import os
import threading

import numpy as np
import xarray as xr

MODEL_NC_PATH = os.environ.get("MODEL_NC_PATH", "/mnt/user-data/uploads/cmems_mod_glo_phy_my_0_083deg_P1D-m_1789139037755.nc")

VAR_MAP = {
    "temperature": "thetao",
    "salinity": "so",
    "u_current": "uo",
    "v_current": "vo",
    "ssh": "zos",
    "mixed_layer_depth": "mlotst",
}

_lock = threading.Lock()
_ds = None


def _dataset():
    global _ds
    if _ds is None:
        with _lock:
            if _ds is None:
                _ds = xr.open_dataset(MODEL_NC_PATH)
    return _ds


def available_variables():
    ds = _dataset()
    return [v for v in VAR_MAP if VAR_MAP[v] in ds]


def available_depths():
    ds = _dataset()
    return ds["depth"].values.tolist() if "depth" in ds.coords else []


def available_times():
    ds = _dataset()
    return [str(np.datetime_as_string(t, unit="D")) for t in ds["time"].values]


def bounds():
    ds = _dataset()
    return {
        "lat_min": float(ds["latitude"].min()), "lat_max": float(ds["latitude"].max()),
        "lon_min": float(ds["longitude"].min()), "lon_max": float(ds["longitude"].max()),
    }


def get_slice(variable: str, depth: float, time: str, stride: int = 1):
    if variable not in VAR_MAP:
        raise ValueError(f"Unknown variable '{variable}'. Choose from {list(VAR_MAP)}")
    ds = _dataset()
    var = VAR_MAP[variable]
    if var not in ds:
        raise ValueError(f"Variable '{var}' not present in this dataset")

    da = ds[var].sel(time=time, method="nearest")

    actual_depth = None
    if "depth" in da.dims:
        depths = ds["depth"].values
        idx = int(np.argmin(np.abs(depths - depth)))
        actual_depth = float(depths[idx])
        da = da.isel(depth=idx)

    if stride > 1:
        da = da.isel(latitude=slice(None, None, stride), longitude=slice(None, None, stride))

    grid = np.round(da.values.astype(float), 3)
    grid = np.where(np.isnan(grid), None, grid)

    lat_vals = ds["latitude"].values[::stride] if stride > 1 else ds["latitude"].values
    lon_vals = ds["longitude"].values[::stride] if stride > 1 else ds["longitude"].values

    return {
        "variable": variable,
        "requested_depth_m": depth,
        "actual_depth_m": actual_depth,
        "time": str(np.datetime_as_string(da["time"].values, unit="D")) if "time" in da.coords else time,
        "lat": np.round(lat_vals, 3).tolist(),
        "lon": np.round(lon_vals, 3).tolist(),
        "grid": grid.tolist(),
        "units": ds[var].attrs.get("units", ""),
        "long_name": ds[var].attrs.get("long_name", ""),
    }
