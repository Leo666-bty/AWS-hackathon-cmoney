from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from mindfolio_api.ai.narrative import NarrativeDraft
from mindfolio_core.domain.models import DecisionScores


class ReportHandle(BaseModel):
    report_id: str
    claim_token: str
    expires_at: datetime


class SessionRequest(BaseModel):
    invite_code: str = Field(min_length=6, max_length=256)


class SessionResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    member_id: str
    display_name: str


class ClaimReportRequest(BaseModel):
    claim_token: str = Field(min_length=16, max_length=512)


class ClaimReportResponse(BaseModel):
    report_id: str
    member_id: str
    claimed_at: datetime
    holding_candidates: list[str]


class ConfirmReportHoldingsRequest(BaseModel):
    stock_ids: list[str] = Field(min_length=1, max_length=5)


class DashboardReport(BaseModel):
    report_id: str
    persona_code: str
    persona_name: str
    persona_headline: str
    confidence: int
    average_return: float
    scores: DecisionScores
    narrative: NarrativeDraft
    created_at: datetime


class DashboardHolding(BaseModel):
    stock_id: str
    name: str
    industry: str
    source: str
    confirmed_at: datetime
    shares: None = None
    average_cost: None = None


class CardEvidence(BaseModel):
    label: str
    value: str
    tone: Literal["neutral", "positive", "warning"] = "neutral"


class ActionCard(BaseModel):
    card_id: str
    stock_id: str
    stock_name: str
    title: str
    summary: str
    as_of: str
    provenance: str
    narrative_source: Literal["bedrock", "fallback"] = "fallback"
    evidence: list[CardEvidence]
    suggested_questions: list[str]
    current_preference: str | None = None


class WeeklyReview(BaseModel):
    title: str
    summary: str
    next_review_at: str
    data_as_of: str
    source: Literal["snapshot", "fixture"]


class MemberDashboard(BaseModel):
    member_id: str
    display_name: str
    report: DashboardReport | None
    portfolio: list[DashboardHolding]
    priority_card: ActionCard | None
    weekly_review: WeeklyReview


class CardFeedbackRequest(BaseModel):
    preference: Literal["review_evidence", "routine", "mute"]


class CardFeedbackResponse(BaseModel):
    card_id: str
    preference: str
    saved_at: datetime


class InteractionEventInput(BaseModel):
    event_id: str = Field(min_length=8, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=64)
    surface: str = Field(min_length=1, max_length=64)
    action: str | None = Field(default=None, max_length=64)
    stock_id: str | None = Field(default=None, max_length=32)
    occurred_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventBatchRequest(BaseModel):
    events: list[InteractionEventInput] = Field(min_length=1, max_length=50)


class EventBatchResponse(BaseModel):
    accepted_event_ids: list[str]
