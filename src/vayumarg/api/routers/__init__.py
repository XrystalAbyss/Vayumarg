"""FastAPI modular routers for Vayumarg.

Organized by functional responsibility: health/governance, storms, forecasting, satellite, and machine learning.
"""

from vayumarg.api.routers.forecast import router as forecast_router
from vayumarg.api.routers.health import router as health_router
from vayumarg.api.routers.satellite import router as satellite_router
from vayumarg.api.routers.storms import router as storms_router

__all__ = [
    "health_router",
    "storms_router",
    "forecast_router",
    "satellite_router",
]

