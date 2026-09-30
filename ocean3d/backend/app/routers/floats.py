"""
routers/floats.py
Implements:
    GET /floats/nearby?bbox=lon_min,lat_min,lon_max,lat_max&time_start=&time_end=
    GET /floats/{id}/profile
per FRD FR-2.1, FR-2.2, FR-2.3, FR-2.4 and Backend_Schema_Doc section 5/6/7.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import get_pool

router = APIRouter(prefix="/floats", tags=["floats"])


@router.get("/nearby")
async def floats_nearby(
    bbox: str = Query(..., description="lon_min,lat_min,lon_max,lat_max"),
    time_start: Optional[str] = Query(None),
    time_end: Optional[str] = Query(None),
):
    """Returns the latest known position of every instrument active in the
    bbox/time window — used to plot markers on the map (App Flow 2.2)."""
    try:
        lon_min, lat_min, lon_max, lat_max = (float(x) for x in bbox.split(","))
    except ValueError:
        raise HTTPException(400, "bbox must be 'lon_min,lat_min,lon_max,lat_max'")

    t_end = datetime.fromisoformat(time_end) if time_end else datetime.utcnow()
    t_start = datetime.fromisoformat(time_start) if time_start else (datetime.utcnow() - timedelta(days=30))

    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT DISTINCT ON (p.instrument_id)
            p.instrument_id,
            i.instrument_type,
            ST_X(p.location::geometry) AS lon,
            ST_Y(p.location::geometry) AS lat,
            p.observed_at
        FROM profiles p
        JOIN instruments i ON i.instrument_id = p.instrument_id
        WHERE ST_Within(
                p.location::geometry,
                ST_MakeEnvelope($1, $2, $3, $4, 4326)
              )
          AND p.observed_at BETWEEN $5 AND $6
        ORDER BY p.instrument_id, p.observed_at DESC
        """,
        lon_min, lat_min, lon_max, lat_max, t_start, t_end,
    )

    if not rows:
        return {"count": 0, "floats": [], "message": "No instruments found in this bbox/time window"}

    return {
        "count": len(rows),
        "floats": [
            {
                "instrument_id": r["instrument_id"],
                "instrument_type": r["instrument_type"],
                "lon": r["lon"],
                "lat": r["lat"],
                "last_observed_at": r["observed_at"].isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/{instrument_id}/profile")
async def float_profile(instrument_id: str, variable: Optional[str] = None):
    """Depth-vs-variable profile for the click-to-inspect chart
    (FRD FR-2.3, FR-2.4). Uses the most recent timestamp available for
    this instrument unless data is sparse."""
    pool = await get_pool()

    latest = await pool.fetchval(
        "SELECT MAX(observed_at) FROM profiles WHERE instrument_id = $1", instrument_id
    )
    if latest is None:
        raise HTTPException(404, f"No profile data for instrument '{instrument_id}'")

    var_filter = "AND variable = $2" if variable else ""
    args = [instrument_id, latest] if not variable else [instrument_id, variable, latest]

    if variable:
        rows = await pool.fetch(
            f"""
            SELECT depth_m, variable, value, observed_at, qc_flag
            FROM profiles
            WHERE instrument_id = $1 AND variable = $2 AND observed_at = $3
            ORDER BY depth_m ASC
            """,
            instrument_id, variable, latest,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT depth_m, variable, value, observed_at, qc_flag
            FROM profiles
            WHERE instrument_id = $1 AND observed_at = $2
            ORDER BY variable, depth_m ASC
            """,
            instrument_id, latest,
        )

    meta = await pool.fetchrow(
        "SELECT instrument_type, deployment_date, status, metadata FROM instruments WHERE instrument_id = $1",
        instrument_id,
    )

    by_variable: dict[str, list] = {}
    for r in rows:
        by_variable.setdefault(r["variable"], []).append(
            {"depth_m": float(r["depth_m"]), "value": float(r["value"]), "qc_flag": r["qc_flag"]}
        )

    return {
        "instrument_id": instrument_id,
        "instrument_type": meta["instrument_type"] if meta else None,
        "observed_at": latest.isoformat(),
        "series": by_variable,  # e.g. {"temperature": [{"depth_m":..,"value":..}, ...], "salinity": [...]}
    }
