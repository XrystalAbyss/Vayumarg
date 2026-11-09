"""FastAPI Operational Backend for VAYUMARG Cyclone Intelligence Studio.

Exposes authentic meteorological services:
- Authoritative PostgreSQL/PostGIS IBTrACS historical tracks & multi-agency observations.
- Deterministic Geodesic Constant-Velocity Extrapolation (+6h, +12h, +24h) with strict leakage protection.
- Independent Hindsight Verification against retrospective ground-truth observations.
- Curated visual demonstration cases (BIPARJOY, AMPHAN, REMAL) with pre-landfall ocean coordinates.
- Dynamic rendering of authentic ISRO INSAT multichannel HDF5 crops (TIR-1, TIR-2, WV, MIR).
- Scientific methodology, assumptions, and physical limitations registry.
- Machine Learning inference and model registry integration.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from vayumarg.api.routers.forecast import router as forecast_router
from vayumarg.api.routers.health import router as health_router
from vayumarg.api.routers.satellite import router as satellite_router
from vayumarg.api.routers.storms import router as storms_router
from vayumarg.api.routes_dataset import router as dataset_router
from vayumarg.api.routes_ml import router as ml_router
from vayumarg.api.routes_satellite import router as satellite_v1_router
from vayumarg.services.cyclone_service import populate_initial_registry

# Project root paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
UI_DIR = Path(__file__).resolve().parent.parent / "ui"
UI_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    populate_initial_registry()
    yield


app = FastAPI(
    title="VAYUMARG Cyclone Intelligence Studio API",
    description=(
        "Operational meteorological data engine delivering authentic IBTrACS historical tracks, "
        "real INSAT satellite analytics, and deterministic geodesic forecasts."
    ),
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular subrouters
app.include_router(dataset_router)
app.include_router(ml_router)
app.include_router(satellite_v1_router)
app.include_router(health_router)
app.include_router(storms_router)
app.include_router(forecast_router)
app.include_router(satellite_router)

# Mount static asset directories
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

if UI_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


@app.get("/favicon.svg")
def get_favicon_svg():
    fav = FRONTEND_DIST / "favicon.svg"
    if fav.is_file():
        return FileResponse(fav)
    raise HTTPException(status_code=404)


@app.get("/favicon.ico")
def get_favicon_ico():
    fav = FRONTEND_DIST / "favicon.svg"
    if fav.is_file():
        return FileResponse(fav, media_type="image/svg+xml")
    raise HTTPException(status_code=404)


@app.get("/", response_class=FileResponse)
def get_index():
    """Serve Vayumarg Cyclone Intelligence Studio Single-Page Application."""
    if (FRONTEND_DIST / "index.html").is_file():
        return FileResponse(FRONTEND_DIST / "index.html")
    index_file = UI_DIR / "index.html"
    if not index_file.is_file():
        raise HTTPException(status_code=404, detail="UI index.html not found.")
    return FileResponse(index_file)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("vayumarg.api.server:app", host="127.0.0.1", port=8000, reload=True)
