"""Deterministic, AI-free narrative used on every failure path.

This is what keeps the demo working with Bedrock down (Constitution VI). It is
built purely from the verified result — no network, no model — and by
construction contains none of the forbidden terms.
"""

from mindfolio_api.ai.narrative import NarrativeDraft
from mindfolio_core.domain.models import ReconstructionResult


def fallback_narrative(result: ReconstructionResult) -> NarrativeDraft:
    """Build a fixed-template ``NarrativeDraft`` from the result alone."""
    headline = f"你的 2025 投資人格是「{result.persona_name}」"
    summary = (
        f"{result.persona_headline}。回顧 2025，你的五檔重建平均報酬約為 "
        f"{result.average_return:.1f}%，資料信心分數 {result.confidence}。"
    )
    insight = "這是根據你記憶重建的估算結果，僅供回顧參考，並非實際交易憑證。"
    return NarrativeDraft(headline=headline, summary=summary, insight=insight)
