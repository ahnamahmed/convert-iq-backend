from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # AI
    gemini_api_key: str

    # Stripe
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    # Redis
    enable_redis: bool = True
    redis_url: str | None = None

    # Rate limiting
    rate_limit_per_user: int = 10
    rate_limit_window_seconds: int = 3600

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

