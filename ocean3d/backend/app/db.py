"""
db.py — database connection pool for the FastAPI backend.

Reads DATABASE_URL from environment (set it to your Supabase connection
string, or the local test DB used during development).
"""
import os
import asyncpg

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:localtest@localhost:5432/ocean3d",  # local dev fallback only
)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
