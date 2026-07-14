"""Tests for the AI narrative service (feature 002, FR-005 / Constitution III).

A fake Bedrock client is used everywhere — no real AWS credentials, no network.
"""

import json

import pytest

from mindfolio_api.ai.fallback import fallback_narrative
from mindfolio_api.ai.narrative import NarrativeDraft, generate_narrative
from mindfolio_api.config import Settings
from mindfolio_core.domain.models import (
    DecisionScores,
    ReconstructionResult,
    TradeResult,
)


class FakeBedrockClient:
    """Minimal stand-in for a boto3 bedrock-runtime client."""

    def __init__(self, *, text: str | None = None, raise_exc: Exception | None = None):
        self._text = text
        self._raise = raise_exc
        self.called = False

    def converse(self, **kwargs) -> dict:
        self.called = True
        if self._raise is not None:
            raise self._raise
        return {"output": {"message": {"role": "assistant", "content": [{"text": self._text}]}}}


@pytest.fixture
def result() -> ReconstructionResult:
    return ReconstructionResult(
        trades=[
            TradeResult(
                stock_id="2330",
                name="台積電",
                industry="電子–半導體",
                buy_month="2025-03",
                exit_month="2025-12",
                relation="holding",
                buy_raw=800.0,
                exit_raw=1050.0,
                return_pct=31.25,
                confidence=100,
            ),
        ],
        average_return=18.4,
        confidence=87,
        persona_code="LHDX",
        persona_name="穩健佈局者",
        persona_headline="低檔進場、長期持有的耐心玩家",
        fingerprint=[0.42, 0.6, 0.7, 0.8, 0.46],
        scores=DecisionScores(outcome=28, entry=15, capture=12, data=13),
        holding_candidates=["2330"],
    )


@pytest.fixture
def enabled_settings() -> Settings:
    return Settings(bedrock_enabled=True, bedrock_model_id="fake.model-v1")


def _bedrock_json(**overrides) -> str:
    payload = {
        "headline": "你的投資人格是穩健佈局者",
        "summary": "回顧 2025，你的五檔重建平均報酬約 18.4%，資料信心 87。",
        "insight": "你傾向在相對低檔進場並長期持有。",
    }
    payload.update(overrides)
    return json.dumps(payload, ensure_ascii=False)


def test_valid_bedrock_json_is_narrated(result, enabled_settings):
    client = FakeBedrockClient(text=_bedrock_json())
    draft = generate_narrative(result, client=client, settings=enabled_settings)

    assert client.called is True
    assert isinstance(draft, NarrativeDraft)
    assert draft.headline == "你的投資人格是穩健佈局者"
    assert "18.4" in draft.summary
    assert draft.insight


def test_malformed_json_falls_back(result, enabled_settings):
    client = FakeBedrockClient(text="this is not json {")
    draft = generate_narrative(result, client=client, settings=enabled_settings)

    assert client.called is True
    assert draft == fallback_narrative(result)


def test_client_exception_falls_back_without_raising(result, enabled_settings):
    client = FakeBedrockClient(raise_exc=RuntimeError("bedrock timeout"))
    draft = generate_narrative(result, client=client, settings=enabled_settings)

    assert client.called is True
    assert draft == fallback_narrative(result)


def test_missing_field_fails_schema_and_falls_back(result, enabled_settings):
    # Drop "insight" -> schema validation fails -> fallback.
    payload = json.loads(_bedrock_json())
    del payload["insight"]
    client = FakeBedrockClient(text=json.dumps(payload, ensure_ascii=False))

    draft = generate_narrative(result, client=client, settings=enabled_settings)
    assert draft == fallback_narrative(result)


def test_disabled_bedrock_uses_fallback_without_calling(result):
    settings = Settings(bedrock_enabled=False)
    client = FakeBedrockClient(text=_bedrock_json())

    draft = generate_narrative(result, client=client, settings=settings)

    assert client.called is False
    assert draft == fallback_narrative(result)


def test_none_client_uses_fallback(result, enabled_settings):
    draft = generate_narrative(result, client=None, settings=enabled_settings)
    assert draft == fallback_narrative(result)


@pytest.mark.parametrize(
    "bad",
    [
        {"headline": "建議買進，把握機會"},
        {"summary": "設定目標價 300 元"},
        {"insight": "保證獲利的長期玩家"},
        {"summary": "You should buy now for guaranteed returns."},
        {"insight": "這是一種焦慮型人格的診斷"},
    ],
)
def test_forbidden_terms_trip_guardrail_and_fall_back(result, enabled_settings, bad):
    client = FakeBedrockClient(text=_bedrock_json(**bad))
    draft = generate_narrative(result, client=client, settings=enabled_settings)
    assert draft == fallback_narrative(result)


def test_fallback_is_clean_and_non_empty(result):
    draft = fallback_narrative(result)

    assert isinstance(draft, NarrativeDraft)
    assert draft.headline and draft.summary and draft.insight
    blob = f"{draft.headline}{draft.summary}{draft.insight}".lower()
    for term in ["買進", "賣出", "目標價", "保證", "獲利保證", "焦慮", "憂鬱", "診斷",
                 "buy", "sell", "target price", "guaranteed"]:
        assert term.lower() not in blob
    # The persona name is present so the demo narrative is meaningful.
    assert result.persona_name in draft.headline or result.persona_name in draft.summary
