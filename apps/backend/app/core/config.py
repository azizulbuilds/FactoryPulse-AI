import os


class Settings:
    APP_NAME: str = "FactoryPulse AI"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    ENVIRONMENT: str = os.getenv(
        "ENVIRONMENT",
        "development",
    )


settings = Settings()