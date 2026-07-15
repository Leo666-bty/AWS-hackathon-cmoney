from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MarketContextEvidence(BaseModel):
    stock_id: str = Field(min_length=1)
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    regime_id: int = Field(ge=0)
    regime_label: str = Field(min_length=1)
    regime_match: Literal["strong", "moderate", "weak"]
    anomaly_level: Literal["general", "attention", "significant"]
    anomaly_score: float = Field(ge=0, le=1)
    salient_feature_keys: list[str]
    evidence: dict[str, float | int | str | None]
    feature_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    source_as_of: str


class MarketContextArtifactMetadata(BaseModel):
    model_version: str = Field(min_length=1)
    feature_version: str = Field(min_length=1)
    training_range: tuple[str, str]
    sample_count: int = Field(gt=0)
    feature_keys: list[str]
    preprocessing: dict[str, object]
    metrics: dict[str, object]
    generated_at: datetime


class MarketContextArtifact(BaseModel):
    metadata: MarketContextArtifactMetadata
    contexts: dict[str, MarketContextEvidence]
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
