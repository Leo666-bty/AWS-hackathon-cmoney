from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from mindfolio_api.config import Settings
from mindfolio_api.repositories.market_context import MarketContextRepository
from mindfolio_api.schemas.ai_report import (
    EvidenceSection,
    InvestmentAIReport,
    QuestionAnswer,
    QuestionId,
    SuggestedQuestion,
)
from mindfolio_core.domain.models import ReconstructionResult

logger = logging.getLogger(__name__)

CONTEXT_VERSION = "investment-ai-context-v1"
PROMPT_VERSION = "investment-report-v1"
QUESTION_PROMPT_VERSION = "investment-question-v1"
QUESTION_LABELS: dict[QuestionId, str] = {
    "why-persona": "為什麼我是這種投資人格？",
    "most-influential-trade": "哪筆交易最影響結果？",
    "why-anomalous-month": "哪個買進月份最不尋常？",
}
FORBIDDEN = ("買進", "賣出", "加碼", "減碼", "目標價", "保證獲利", "焦慮診斷")


def build_context(report: dict[str, Any], market: MarketContextRepository) -> dict[str, Any]:
    result = ReconstructionResult.model_validate(report["result"])
    trades: list[dict[str, Any]] = []
    evidence: dict[str, dict[str, Any]] = {}
    for index, trade in enumerate(result.trades):
        trade_ref = f"trade:{index}"
        evidence[trade_ref] = trade.model_dump(mode="json")
        buy_month = trade.buy_month if trade.buy_month.startswith("2025-") else f"2025-{trade.buy_month}"
        market_context = market.get(trade.stock_id, buy_month)
        market_ref = f"market:{trade.stock_id}:{buy_month}"
        if market_context:
            evidence[market_ref] = market_context.model_dump(mode="json")
        trades.append({
            **trade.model_dump(mode="json"),
            "trade_ref": trade_ref,
            "market_ref": market_ref if market_context else None,
        })
    return {
        "context_version": CONTEXT_VERSION,
        "model_version": market.model_version or "unavailable",
        "content_sha256": market.content_sha256 or "unavailable",
        "result": result.model_dump(mode="json"),
        "trades": trades,
        "evidence": evidence,
    }


def cache_key(context: dict[str, Any]) -> str:
    # content_sha256 is included so a re-trained artifact invalidates the cache
    # even if MODEL_VERSION was not bumped (the checksum always changes).
    return "|".join((
        CONTEXT_VERSION,
        context["model_version"],
        context.get("content_sha256", "unavailable"),
        PROMPT_VERSION,
    ))


def _fallback_report(context: dict[str, Any]) -> InvestmentAIReport:
    result = context["result"]
    trades = context["trades"]
    strongest = max(trades, key=lambda trade: trade["return_pct"])
    weakest = min(trades, key=lambda trade: trade["return_pct"])
    market_trades = [trade for trade in trades if trade["market_ref"]]
    anomalous = max(
        market_trades,
        key=lambda trade: context["evidence"][trade["market_ref"]]["anomaly_score"],
        default=None,
    )
    moments: list[EvidenceSection] = []
    if anomalous:
        item = context["evidence"][anomalous["market_ref"]]
        moments.append(EvidenceSection(
            title=f"{anomalous['name']}的買進月份",
            body=f"{anomalous['buy_month']} 屬於「{item['regime_label']}」情境，異常程度為「{item['anomaly_level']}」。",
            evidence_refs=[anomalous["trade_ref"], anomalous["market_ref"]],
        ))
    return InvestmentAIReport(
        title="LEO 的 Investment DNA 深度解讀",
        executive_summary=f"你的五筆 2025 交易重建呈現「{result['persona_name']}」，平均重建報酬為 {result['average_return']:.1f}%。這是歷史資料回顧，不是未來行情預測。",
        strengths=[EvidenceSection(
            title="最有代表性的成果",
            body=f"{strongest['name']} 的重建報酬為 {strongest['return_pct']:.1f}%，是本次結果中表現最突出的交易。",
            evidence_refs=[strongest["trade_ref"]],
        )],
        watchouts=[EvidenceSection(
            title="值得回看的交易",
            body=f"{weakest['name']} 的重建報酬為 {weakest['return_pct']:.1f}%，適合回看當時進場月份與持有關係。",
            evidence_refs=[weakest["trade_ref"]],
        )],
        market_moments=moments,
        suggested_questions=[SuggestedQuestion(id=key, label=value) for key, value in QUESTION_LABELS.items()],
        source="fallback",
        versions={"context": CONTEXT_VERSION, "model": context["model_version"], "prompt": PROMPT_VERSION},
        generated_at=datetime.now(UTC),
    )


def _minimal_report(context: dict[str, Any]) -> InvestmentAIReport:
    """Last-resort report when even the deterministic fallback cannot be built.

    References no evidence and makes no factual claim, so it can never raise on a
    malformed/degenerate context. This is what backstops the documented guarantee
    that a request never 500s just because narrative construction failed.
    """
    return InvestmentAIReport(
        title="Investment DNA 深度解讀",
        executive_summary="目前無法產生詳細解讀，這是歷史資料回顧，不是未來行情預測。",
        strengths=[],
        watchouts=[],
        market_moments=[],
        suggested_questions=[SuggestedQuestion(id=key, label=value) for key, value in QUESTION_LABELS.items()],
        source="fallback",
        versions={
            "context": CONTEXT_VERSION,
            "model": str(context.get("model_version", "unavailable")),
            "prompt": PROMPT_VERSION,
        },
        generated_at=datetime.now(UTC),
    )


def _safe(report: InvestmentAIReport, allowed_refs: set[str]) -> bool:
    text = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)
    refs = [ref for section in [*report.strengths, *report.watchouts, *report.market_moments] for ref in section.evidence_refs]
    return not any(term in text for term in FORBIDDEN) and set(refs).issubset(allowed_refs)


def generate_report(context: dict[str, Any], client: Any | None, settings: Settings) -> InvestmentAIReport:
    try:
        fallback = _fallback_report(context)
    except Exception:  # noqa: BLE001 — the deterministic fallback must never bubble a 500.
        logger.warning("AI fallback report construction failed; using minimal report", exc_info=True)
        return _minimal_report(context)
    if client is None or not settings.bedrock_enabled:
        return fallback
    try:
        prompt = (
            "你是投資歷史資料解讀器。只能使用 context 的數值與 evidence key；不得提供買賣指令、目標價、心理診斷或未來預測。"
            "請輸出完全符合 supplied JSON schema 的 JSON，不要 Markdown。\n"
            + json.dumps({"context": context, "schema": InvestmentAIReport.model_json_schema()}, ensure_ascii=False)
        )
        response = client.converse(modelId=settings.bedrock_model_id, messages=[{"role": "user", "content": [{"text": prompt}]}])
        blocks = response["output"]["message"]["content"]
        text = next(block["text"] for block in blocks if isinstance(block.get("text"), str))
        generated = InvestmentAIReport.model_validate(json.loads(text)).model_copy(update={"source": "bedrock"})
        if _safe(generated, set(context["evidence"])):
            return generated
    except Exception:  # noqa: BLE001
        logger.warning("AI Deep Dive failed; deterministic fallback used", exc_info=True)
    return fallback


def answer_question(question_id: QuestionId, context: dict[str, Any]) -> QuestionAnswer:
    trades = context["trades"]
    if question_id == "why-persona":
        result = context["result"]
        refs = [trade["trade_ref"] for trade in trades]
        answer = f"「{result['persona_name']}」來自五筆交易的報酬、進場位置、掌握程度與資料信心綜合計分，不是心理測驗或未來績效評級。"
    elif question_id == "most-influential-trade":
        trade = max(trades, key=lambda item: abs(item["return_pct"] - context["result"]["average_return"]))
        refs = [trade["trade_ref"]]
        answer = f"{trade['name']} 與整體平均差距最大，重建報酬為 {trade['return_pct']:.1f}%，因此對結果輪廓的影響最明顯。"
    else:
        candidates = [trade for trade in trades if trade["market_ref"]]
        if not candidates:
            refs = []
            answer = "目前 artifact 沒有涵蓋這五筆交易的買進月份，因此無法判定最不尋常的月份。"
        else:
            trade = max(candidates, key=lambda item: context["evidence"][item["market_ref"]]["anomaly_score"])
            evidence = context["evidence"][trade["market_ref"]]
            refs = [trade["trade_ref"], trade["market_ref"]]
            answer = f"{trade['name']} 的 {trade['buy_month']} 異常百分位最高，屬於「{evidence['regime_label']}」且標記為「{evidence['anomaly_level']}」。"
    return QuestionAnswer(
        question_id=question_id,
        answer=answer,
        evidence_refs=refs,
        limitations="僅依 2025 歷史重建與全站市場／社群資料解釋，不構成投資建議。",
    )
