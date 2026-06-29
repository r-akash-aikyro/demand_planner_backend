from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "dev"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://dpb:dpb_pass@localhost:5432/dpb"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "change-me-dev-secret"
    JWT_ALG: str = "HS256"
    ACCESS_TTL: int = 900
    REFRESH_TTL: int = 604800
    RATE_LIMIT: str = "100/minute"

    ADK_URL: str = "http://adk-service:9000"
    ADK_SECRET: str = "change-me-adk-secret"
    GOOGLE_API_KEY: str = "REPLACE_ME_LATER"

    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@demandplanner.local"
    APP_BASE_URL: str = "http://localhost:3000"

    KPI_CACHE_TTL: int = 300


settings = Settings()
