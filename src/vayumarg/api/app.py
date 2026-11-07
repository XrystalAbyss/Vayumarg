"""FastAPI Application Factory for Vayumarg.

Exposes REST APIs for Module A Authentic Satellite Intelligence, Decision-Support
Analysis, and Cyclone Monitoring Subsystems.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vayumarg.api.routes_dataset import router as dataset_router
from vayumarg.api.routes_ml import router as ml_router
from vayumarg.api.routes_satellite import router as satellite_router
from vayumarg.core.logging import get_logger
from vayumarg.satellite.service import get_satellite_service

logger = get_logger("vayumarg.api.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: pre-warm preview cache on startup."""
    logger.info("Initializing Vayumarg backend API application...")
    try:
        service = get_satellite_service()
        # Verify and warm up previews cache
        crops = service.list_authentic_crops()
        logger.info("Verified %d authentic satellite crops at startup", len(crops))
    except Exception as e:
        logger.warning("Could not pre-warm satellite preview cache at startup: %s", e)
    yield
    logger.info("Shutting down Vayumarg backend API application.")


def create_app() -> FastAPI:
    """Create and configure the main FastAPI application instance."""
    app = FastAPI(
        title="Vayumarg Scientific Cyclone Intelligence API",
        description=(
            "AI/ML decision-support system and authentic satellite remote-sensing "
            "subsystem for tropical cyclone identification, intensity estimation, and forecasting."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # Enable CORS for frontend web application
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    app.include_router(dataset_router)
    app.include_router(ml_router)
    app.include_router(satellite_router)

    @app.get("/", tags=["System"])
    def root():
        return {
            "system": "Vayumarg",
            "version": "0.1.0",
            "status": "OPERATIONAL",
            "module_a": "AUTHENTIC_SATELLITE_INTELLIGENCE_READY",
            "docs_url": "/docs",
        }

    return app


app = create_app()
