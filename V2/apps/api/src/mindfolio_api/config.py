import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MINDFOLIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    cors_origins: str = "http://localhost:5173"
    model_status: str = "not_loaded"
    market_data_path: str = "./data/market-catalog.json"

    # --- Bedrock AI narrative (feature 002) ---
    # Disabled by default so tests and offline demos take the deterministic
    # fallback path without ever touching AWS.
    bedrock_enabled: bool = False
    bedrock_model_id: str = "openai.gpt-oss-120b-1:0"
    # Read from the standard AWS_REGION env var (the SDK convention) rather than
    # MINDFOLIO_AWS_REGION. The selected gpt-oss model is served from us-east-1.
    aws_region: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))

    # --- Persistence (feature 003) ---
    # PostgreSQL self-hosted on the same EC2 instance (not RDS). Empty in local
    # dev/tests → an in-memory holdings store is used (non-persistent). Read from
    # the conventional DATABASE_URL env var.
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))

    # Comma-separated invite-code/member pairs for the P0 small-batch identity
    # adapter, e.g. "alpha-strong-code:LEO,beta-strong-code:MIA". Production
    # deployments must override the development default with random secrets.
    invite_identities: str = "demo-leo:LEO"
    report_ttl_hours: int = 72
    session_secret: str = "development-only-change-me"
    session_ttl_hours: int = 24

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def invite_identity_map(self) -> dict[str, str]:
        identities: dict[str, str] = {}
        for pair in self.invite_identities.split(","):
            code, separator, member_id = pair.strip().partition(":")
            if separator and code and member_id:
                identities[code] = member_id
        return identities

    @property
    def narrative_status(self) -> str:
        """Expose configured mode without making a billable health-check call."""
        if self.bedrock_enabled and self.bedrock_model_id:
            return "bedrock_enabled"
        return "fallback_ready"


@lru_cache
def get_settings() -> Settings:
    return Settings()
