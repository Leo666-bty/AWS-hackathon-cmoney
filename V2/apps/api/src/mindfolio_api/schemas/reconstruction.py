from typing import Literal

from pydantic import BaseModel, Field

from mindfolio_api.ai.narrative import NarrativeDraft
from mindfolio_api.schemas.retention import ReportHandle
from mindfolio_core.domain.models import ReconstructionResult

_MONTH = r"^(0[1-9]|1[0-2])$"


class TradeConfig(BaseModel):
    """One stock's reconstructed trade, as the builder submits it."""

    stock_id: str
    relation: Literal["holding", "sold"] = "holding"
    buy_month: str = Field(pattern=_MONTH)
    buy_mode: Literal["band", "exact"] = "band"
    buy_band: Literal["low", "mid", "high"] = "mid"
    buy_exact: float | None = None
    sell_month: str = Field(default="12", pattern=_MONTH)
    sell_mode: Literal["estimate", "exact"] = "estimate"
    sell_exact: float | None = None


class CompleteRequest(BaseModel):
    trades: list[TradeConfig] = Field(min_length=5, max_length=5)


class CompleteResponse(BaseModel):
    result: ReconstructionResult
    narrative: NarrativeDraft
    report: ReportHandle | None = None


class ConfirmHoldingsRequest(BaseModel):
    """Consent to save holdings. The trades are re-sent so the backend can
    re-verify which stocks are `holding` candidates before writing any."""

    user_id: str
    trades: list[TradeConfig] = Field(min_length=5, max_length=5)
