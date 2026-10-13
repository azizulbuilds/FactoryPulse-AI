from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.predictions import router as predictions_router
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AMD-powered industrial intelligence platform "
        "for machine anomaly detection and maintenance insights."
    ),
)


# Health endpoint
app.include_router(
    health_router,
    prefix=settings.API_PREFIX,
)

# Machine anomaly prediction endpoint
app.include_router(
    predictions_router,
    prefix=settings.API_PREFIX,
)


@app.get("/")
def root():
    return {
        "message": "Welcome to ForgePulse AI",
        "status": "running",
    }