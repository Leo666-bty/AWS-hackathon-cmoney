from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


QuestionId = Literal["why-persona", "most-influential-trade", "why-anomalous-month"]


class EvidenceSection(BaseModel):
    title: str
    body: str
    evidence_refs: list[str]


class SuggestedQuestion(BaseModel):
    id: QuestionId
    label: str


class InvestmentAIReport(BaseModel):
    title: str
    executive_summary: str
    strengths: list[EvidenceSection]
    watchouts: list[EvidenceSection]
    market_moments: list[EvidenceSection]
    suggested_questions: list[SuggestedQuestion]
    source: Literal["bedrock", "fallback"]
    versions: dict[str, str]
    generated_at: datetime


class QuestionRequest(BaseModel):
    question_id: QuestionId


class QuestionAnswer(BaseModel):
    question_id: QuestionId
    answer: str
    evidence_refs: list[str]
    limitations: str
    source: Literal["bedrock", "fallback"] = "fallback"
    prompt_version: str = "investment-question-v1"
