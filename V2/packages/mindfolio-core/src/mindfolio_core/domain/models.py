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


class StockSummary(BaseModel):
    """UI-facing stock summary for popular/search lists."""

    id: str
    name: str
    industry: str
    views: int = Field(ge=0)
    popular: bool = False


class PriceRegime(BaseModel):
    """A pre/post corporate-action raw-price band with its adjustment factor."""

    low: float
    high: float
    factor: float


class MonthEnvelope(BaseModel):
    """A stock's price envelope for one month, plus the input modes it allows."""

    stock_id: str
    month: str
    raw_low: float
    raw_high: float
    close: float
    adjusted_close: float
    factor: float
    corporate_action: bool
    regimes: list[PriceRegime]
    allowed_price_modes: list[str]
