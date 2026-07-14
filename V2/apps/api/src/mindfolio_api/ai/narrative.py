"""Bedrock narrative generation with a deterministic, guardrailed fallback.

Constitution III: the AI receives only a verified ``ReconstructionResult`` DTO,
its output must pass a Pydantic schema, and on ANY failure (timeout, provider
error, malformed JSON, schema-invalid, or a guardrail hit) a fixed-template
narrative is substituted so the core result always returns. This function must
never raise.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from mindfolio_api.ai.prompts import build_narrative_prompt
from mindfolio_api.config import Settings, get_settings
from mindfolio_core.domain.models import ReconstructionResult

logger = logging.getLogger(__name__)


class NarrativeDraft(BaseModel):
    """The schema Bedrock output must satisfy before it is trusted."""

    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    insight: str = Field(min_length=1)
    source: Literal["bedrock", "fallback"] = "fallback"


# Forbidden content (Constitution III). Chinese terms match verbatim; English
# terms are matched case-insensitively. A single hit routes to the fallback.
_FORBIDDEN_TERMS: tuple[str, ...] = (
    # buy / sell direction
    "買進",
    "賣出",
    "買入",
    "賣掉",
    "加碼",
    "減碼",
    "buy",
    "sell",
    # target price
    "目標價",
    "target price",
    "price target",
    # return guarantee
    "保證",
    "獲利保證",
    "穩賺",
    "包賺",
    "guarantee",
    "guaranteed",
    # psychological diagnosis framing
    "焦慮",
    "憂鬱",
    "抑鬱",
    "診斷",
    "病態",
    "anxiety",
    "depression",
    "diagnosis",
    "diagnose",
)


def _trips_guardrail(draft: NarrativeDraft) -> bool:
    blob = f"{draft.headline}\n{draft.summary}\n{draft.insight}"
    lowered = blob.lower()
    for term in _FORBIDDEN_TERMS:
        if term.isascii():
            if term.lower() in lowered:
                return True
        elif term in blob:
            return True
    return False


def _extract_text(response: dict[str, Any]) -> str:
    """Pull the assistant text out of a Bedrock Converse response.

    Reasoning-capable models such as gpt-oss may emit a ``reasoningContent``
    block before the user-visible ``text`` block, so content order cannot be
    assumed.
    """
    content = response["output"]["message"]["content"]
    for block in content:
        text = block.get("text")
        if isinstance(text, str) and text.strip():
            return text
    raise ValueError("Bedrock Converse response contains no text block")


def generate_narrative(
    result: ReconstructionResult,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
) -> NarrativeDraft:
    """Turn a verified result into a short narrative, never raising.

    Returns the deterministic fallback when Bedrock is disabled, no client is
    supplied, or anything at all goes wrong along the Bedrock path.
    """
    # Local import breaks the narrative <-> fallback import cycle.
    from mindfolio_api.ai.fallback import fallback_narrative

    settings = settings or get_settings()

    if not settings.bedrock_enabled or client is None:
        return fallback_narrative(result)

    try:
        prompt = build_narrative_prompt(result)
        response = client.converse(
            modelId=settings.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
        )
        text = _extract_text(response)
        draft = NarrativeDraft.model_validate(json.loads(text)).model_copy(
            update={"source": "bedrock"}
        )
    except Exception:  # noqa: BLE001 — any failure must degrade, never raise.
        logger.warning("Bedrock narrative failed; using fallback", exc_info=True)
        return fallback_narrative(result)

    if _trips_guardrail(draft):
        logger.warning("Bedrock narrative tripped content guardrail; using fallback")
        return fallback_narrative(result)

    return draft
