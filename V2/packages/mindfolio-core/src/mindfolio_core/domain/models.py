from datetime import datetime

from pydantic import BaseModel, Field


class ModelArtifactMetadata(BaseModel):
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    feature_version: str = Field(min_length=1)
    training_range: tuple[str, str]
    sample_count: int = Field(ge=0)
    metrics: dict[str, float]
    generated_at: datetime


class MarketInference(BaseModel):
    regime_id: str
    anomaly_level: str
    evidence_keys: list[str]
    model_version: str
