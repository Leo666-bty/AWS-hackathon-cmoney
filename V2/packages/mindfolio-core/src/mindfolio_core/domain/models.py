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


class ConfirmedHolding(BaseModel):
    """A user-confirmed holding (only a consented `holding` trade lands here)."""

    user_id: str
    stock_id: str
    source: str = "user_confirmed"
    confirmed_at: datetime


class PriceValidation(BaseModel):
    """Displayable result of validating one user-entered price against a month."""

    valid: bool
    level: str  # "good" | "warn" | "bad"
    message: str


class TradeResult(BaseModel):
    """One reconstructed trade in a portfolio result."""

    stock_id: str
    name: str
    industry: str
    buy_month: str
    exit_month: str
    relation: str  # "holding" | "sold"
    buy_raw: float
    exit_raw: float
    return_pct: float
    confidence: int


class DecisionScores(BaseModel):
    """2025 情境決策力 breakdown (max 40/25/20/15)."""

    outcome: int
    entry: int
    capture: int
    data: int


class ReconstructionResult(BaseModel):
    """The verified portfolio reconstruction result.

    This is the contract the AI narrative service consumes — it never sees raw
    prices beyond what is here, and never recomputes any of these numbers.
    """

    trades: list[TradeResult]
    average_return: float
    confidence: int
    persona_code: str
    persona_name: str
    persona_headline: str
    fingerprint: list[float]
    scores: DecisionScores
    holding_candidates: list[str]
