"""
main.py — FastAPI app entrypoint.

Run locally:
    export DATABASE_URL="postgresql://postgres:<password>@<host>:5432/postgres"
    export MODEL_NC_PATH="/path/to/model.nc"
    uvicorn app.main:app --reload --port 8000

Then browse http://localhost:8000/docs for interactive API docs (Swagger).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import floats, model
from app.db import close_pool

app = FastAPI(
    title="Ocean 3D Visualization Platform API",
    description="Backend for INCOIS Problem Statement 26067",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(model.router)
app.include_router(floats.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await close_pool()
