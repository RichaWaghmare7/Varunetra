"""
routers/model.py
Implements: GET /model/slice?variable=&depth=&time=
per FRD FR-1.2, FR-1.3 and Backend_Schema_Doc API-to-schema mapping.
"""
from fastapi import APIRouter, HTTPException, Query

from app import model_source

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/meta")
async def model_meta():
    """Lets the frontend discover what variables/depths/times/region are available."""
    return {
        "variables": model_source.available_variables(),
        "depths_m": model_source.available_depths(),
        "times": model_source.available_times(),
        "bounds": model_source.bounds(),
    }


@router.get("/slice")
async def model_slice(
    variable: str = Query(..., description="temperature | salinity | u_current | v_current | ssh | mixed_layer_depth"),
    depth: float = Query(0, description="requested depth in meters; nearest available level is used"),
    time: str = Query(..., description="ISO date, e.g. 2026-06-21"),
    stride: int = Query(1, ge=1, le=10, description="downsample factor for lighter payloads"),
):
    try:
        return model_source.get_slice(variable, depth, time, stride=stride)
    except ValueError as e:
        raise HTTPException(400, str(e))
