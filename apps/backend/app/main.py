from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.predictions import router as predictions_router
from app.api.maintenance import router as maintenance_router
from app.api.monitoring import router as monitoring_router
from app.api.alerts import router as alerts_router
from app.api.machine_health import router as machine_health_router
from app.api.fleet import router as fleet_router

from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Industrial intelligence platform for machine "
        "monitoring, anomaly detection, and maintenance insights."
    ),
)


# --------------------------------------------------
# API routers
# --------------------------------------------------

app.include_router(
    health_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    predictions_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    maintenance_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    monitoring_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    alerts_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    machine_health_router,
    prefix=settings.API_PREFIX,
)
app.include_router(
    fleet_router,
    prefix=settings.API_PREFIX,
)

# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to FactoryPulse AI",
        "application": settings.APP_NAME,
        "status": "running",
    }