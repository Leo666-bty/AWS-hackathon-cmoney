import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINDFOLIO_", extra="ignore")

    env: str = "development"
    cors_origins: str = "http://localhost:5173"
    model_status: str = "not_loaded"
    market_data_path: str = "./data/market-catalog.json"

    # --- Bedrock AI narrative (feature 002) ---
    # Disabled by default so tests and offline demos take the deterministic
    # fallback path without ever touching AWS.
    bedrock_enabled: bool = False
    bedrock_model_id: str = ""
    # Read from the standard AWS_REGION env var (the SDK convention) rather than
    # MINDFOLIO_AWS_REGION; falls back to the Tokyo region used by the project.
    aws_region: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "ap-northeast-1"))

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
