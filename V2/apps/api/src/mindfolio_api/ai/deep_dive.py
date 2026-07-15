from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

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

CONTEXT_VERSION = "investment-ai-context-v2"
PROMPT_VERSION = "investment-report-v2-zh-tw"
QUESTION_PROMPT_VERSION = "investment-question-v1"
QUESTION_LABELS: dict[QuestionId, str] = {
    "why-persona": "為什麼我是這種投資人格？",
    "most-influential-trade": "哪筆交易最影響結果？",
    "why-anomalous-month": "哪個買進月份最不尋常？",
}
# Block investment ADVICE, guarantees and pseudo-diagnosis — not the bare words
# 買進/賣出, which are core historical-reconstruction vocabulary appearing
# throughout legitimate narratives (this whole product is about past buy/sell
# months, e.g. the card title "緯創的買進月份"). Guarding the bare words rejected
# almost every valid Bedrock report and silently forced the fallback. We still
# block the phrasings that would actually constitute regulated investment advice.
FORBIDDEN = (
    "建議買", "建議賣", "應該買", "應該賣", "可以買", "可以賣",
    "現在買", "現在賣", "加碼", "減碼", "目標價", "保證獲利",
    "穩賺", "必漲", "必跌", "焦慮診斷",
)

_HAN_CHARACTER = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_LATIN_CHARACTER = re.compile(r"[A-Za-z]")
_NUMBER_TOKEN = re.compile(r"(?<![A-Za-z0-9])[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?")
_POSITIVE_INSTITUTIONAL_CLAIMS = (
    "法人淨流入", "法人實際淨流入", "法人買超", "法人流入", "法人流向有利", "法人實際偏多",
)
_NEGATIVE_INSTITUTIONAL_CLAIMS = (
    "法人淨流出", "法人實際淨流出", "法人賣超", "法人流出", "法人流向不利", "法人實際偏空",
)
_STRONG_ANOMALY_CLAIMS = ("高度異常", "顯著異常", "明顯異常", "異常事件")


class _GeneratedEvidenceSection(BaseModel):
    """Provider-owned prose only; public response metadata stays server-owned."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=32)
    body: str = Field(min_length=10, max_length=180)
    evidence_refs: list[str] = Field(min_length=1, max_length=2)


class _GeneratedInvestmentAIContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=4, max_length=48)
    executive_summary: str = Field(min_length=20, max_length=280)
    strengths: list[_GeneratedEvidenceSection] = Field(min_length=1, max_length=1)
    watchouts: list[_GeneratedEvidenceSection] = Field(min_length=1, max_length=1)
    market_moments: list[_GeneratedEvidenceSection] = Field(max_length=1)


def _display_ratio(value: Any) -> str | None:
    return None if value is None else f"{float(value) * 100:.1f}%"


def _display_number(value: Any) -> str | None:
    return None if value is None else f"{float(value):,.0f}"


def _institutional_direction(value: Any) -> str:
    if value is None:
        return "法人流向資料缺失"
    number = float(value or 0)
    if number > 0:
        return "法人淨流入"
    if number < 0:
        return "法人淨流出"
    return "法人流向持平"


def _anomaly_interpretation(level: str) -> str:
    return {
        "general": "一般級，不得描述為異常事件或高度異常",
        "attention": "注意級，只能描述為值得留意",
        "significant": "顯著級，可描述為顯著偏離一般情境",
    }.get(level, "未知級，不得自行推論")


def _normalized_2025_month(value: str) -> str:
    return value if value.startswith("2025-") else f"2025-{value}"


def _display_facts(
    result: ReconstructionResult,
    trades: list[dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    market_facts: dict[str, dict[str, Any]] = {}
    for trade in trades:
        market_ref = trade.get("market_ref")
        if not market_ref:
            continue
        item = evidence[market_ref]
        metrics = item.get("evidence", {})
        institutional_net = metrics.get("institutional_net")
        buy_month = _normalized_2025_month(trade["buy_month"])
        year, month = buy_month.split("-")
        market_facts[market_ref] = {
            "stock_id": trade["stock_id"],
            "stock_name": trade["name"],
            "buy_month": buy_month,
            "buy_month_label": f"{year} 年 {int(month)} 月",
            "market_regime_cluster_label": item["regime_label"],
            "market_regime_rule": "這是市場情境群集標籤，不等於該股當月法人流向事實",
            "anomaly_level": item["anomaly_level"],
            "anomaly_interpretation": _anomaly_interpretation(item["anomaly_level"]),
            "anomaly_score": f"{float(item['anomaly_score']):.3f}",
            "market_monthly_return": _display_ratio(metrics.get("monthly_return")),
            "institutional_net": _display_number(institutional_net),
            "institutional_direction": _institutional_direction(institutional_net),
            "institutional_flow_ratio": _display_ratio(metrics.get("institutional_flow_ratio")),
            "community_bullish_ratio": _display_ratio(metrics.get("community_bullish_ratio")),
            "source_as_of": item.get("source_as_of"),
        }
    return {
        "portfolio": {
            "reconstruction_year": "2025",
            "trade_count": str(len(trades)),
            "persona_name": result.persona_name,
            "average_reconstruction_return": f"{result.average_return:.1f}%",
            "data_confidence_score": str(result.confidence),
        },
        "trades": {
            trade["trade_ref"]: {
                "stock_id": trade["stock_id"],
                "stock_name": trade["name"],
                "buy_month": _normalized_2025_month(trade["buy_month"]),
                "exit_month": _normalized_2025_month(trade["exit_month"]),
                "relation": "仍持有" if trade["relation"] == "holding" else "已賣出",
                "holding_period_reconstruction_return": f"{float(trade['return_pct']):.1f}%",
            }
            for trade in trades
        },
        "markets": market_facts,
    }


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
        "display_facts": _display_facts(result, trades, evidence),
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
        title="投資輪廓深度解讀",
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
        title="投資輪廓深度解讀",
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


def _user_facing_text(report: InvestmentAIReport) -> list[str]:
    sections = [*report.strengths, *report.watchouts, *report.market_moments]
    return [
        report.title,
        report.executive_summary,
        *(text for section in sections for text in (section.title, section.body)),
    ]


def _is_predominantly_zh_tw(report: InvestmentAIReport) -> bool:
    texts = _user_facing_text(report)
    if any(_HAN_CHARACTER.search(text) is None for text in texts):
        return False
    blob = "".join(texts)
    han_count = len(_HAN_CHARACTER.findall(blob))
    latin_count = len(_LATIN_CHARACTER.findall(blob))
    return han_count >= 20 and han_count / max(han_count + latin_count, 1) >= 0.45


def _numbers_are_server_grounded(report: InvestmentAIReport, display_facts: dict[str, Any]) -> bool:
    used = set(_NUMBER_TOKEN.findall(" ".join(_user_facing_text(report))))
    allowed = set(_NUMBER_TOKEN.findall(json.dumps(display_facts, ensure_ascii=False)))
    return used.issubset(allowed)


def _semantic_validation_error(report: InvestmentAIReport, context: dict[str, Any]) -> str | None:
    blob = " ".join(_user_facing_text(report))
    persona_name = context["display_facts"]["portfolio"]["persona_name"]
    if persona_name not in blob:
        return "persona_name"

    for section in [*report.strengths, *report.watchouts, *report.market_moments]:
        section_text = f"{section.title} {section.body}"
        for ref in section.evidence_refs:
            if not ref.startswith("market:"):
                continue
            item = context["evidence"][ref]
            metrics = item.get("evidence", {})
            institutional_net = metrics.get("institutional_net")
            if institutional_net is not None:
                net = float(institutional_net)
                if net < 0 and any(term in section_text for term in _POSITIVE_INSTITUTIONAL_CLAIMS):
                    return "institutional_direction"
                if net > 0 and any(term in section_text for term in _NEGATIVE_INSTITUTIONAL_CLAIMS):
                    return "institutional_direction"
                if net < 0 and "法人資金偏多" in section_text and "群集" not in section_text:
                    return "regime_as_flow"

            anomaly_level = item.get("anomaly_level")
            if anomaly_level in {"general", "attention"}:
                if any(term in section_text for term in _STRONG_ANOMALY_CLAIMS):
                    return "anomaly_overclaim"
    return None


def _validation_error(report: InvestmentAIReport, context: dict[str, Any]) -> str | None:
    text = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)
    sections = [*report.strengths, *report.watchouts, *report.market_moments]
    refs = [ref for section in sections for ref in section.evidence_refs]
    if any(term in text for term in FORBIDDEN):
        return "forbidden_term"
    if not refs:
        return "missing_evidence"
    if not set(refs).issubset(set(context["evidence"])):
        return "unknown_evidence"
    if not _is_predominantly_zh_tw(report):
        return "language"
    if not _numbers_are_server_grounded(report, context["display_facts"]):
        return "ungrounded_number"
    return _semantic_validation_error(report, context)


def _assemble_bedrock_report(
    generated: _GeneratedInvestmentAIContent,
    context: dict[str, Any],
) -> InvestmentAIReport:
    return InvestmentAIReport(
        title=generated.title,
        executive_summary=generated.executive_summary,
        strengths=[EvidenceSection.model_validate(item.model_dump()) for item in generated.strengths],
        watchouts=[EvidenceSection.model_validate(item.model_dump()) for item in generated.watchouts],
        market_moments=[EvidenceSection.model_validate(item.model_dump()) for item in generated.market_moments],
        suggested_questions=[SuggestedQuestion(id=key, label=value) for key, value in QUESTION_LABELS.items()],
        source="bedrock",
        versions={
            "context": CONTEXT_VERSION,
            "model": context["model_version"],
            "prompt": PROMPT_VERSION,
        },
        generated_at=datetime.now(UTC),
    )


def _generation_prompt(context: dict[str, Any], repair_reason: str | None = None) -> str:
    generation_context = {
        "context_version": context["context_version"],
        "display_facts": context["display_facts"],
        "evidence_keys": sorted(context["evidence"]),
    }
    repair = ""
    if repair_reason:
        repair = (
            f"\n上一份輸出被 server guardrail 拒絕，原因代碼為 {repair_reason}。"
            "請重新產生完整 JSON，修正該問題且遵守所有規則。"
        )
    return (
        "你是台灣投資歷史資料解讀器。所有使用者可見文字必須使用台灣繁體中文；股票代號、ETF、AI、Bedrock "
        "等專有名詞可保留英文。投資人格名稱必須原樣使用 display_facts.portfolio.persona_name，不得翻譯或另創名稱。\n"
        "你不能計算、四捨五入或改寫任何數字。文案中的數字只能逐字複製 display_facts 已格式化的值；"
        "confidence 必須稱為「資料信心分數」，return_pct 必須稱為「持有期間重建報酬」，"
        "monthly_return 必須稱為「買進月份市場月報酬」。\n"
        "regime_label 只能稱為「市場情境群集標籤」，不得把群集名稱當成該股當月法人流向事實。"
        "異常程度必須遵守 anomaly_level 與 anomaly_interpretation；general 不得描述為異常事件或高度異常。"
        "不得把同時出現的市場資料寫成未經證明的因果關係。\n"
        "只能使用 generation_context 的事實；不得提供買賣指令、目標價、心理診斷、適合性判斷或未來預測。"
        "每個 evidence_refs 必須逐字取自 generation_context.evidence_keys。"
        "請輸出完全符合 output_schema 的 JSON，不要 Markdown，也不要加入 schema 以外欄位。\n"
        + json.dumps(
            {
                "generation_context": generation_context,
                "output_schema": _GeneratedInvestmentAIContent.model_json_schema(),
            },
            ensure_ascii=False,
        )
        + repair
    )


def generate_report(context: dict[str, Any], client: Any | None, settings: Settings) -> InvestmentAIReport:
    try:
        fallback = _fallback_report(context)
    except Exception:  # noqa: BLE001 — the deterministic fallback must never bubble a 500.
        logger.warning("AI fallback report construction failed; using minimal report", exc_info=True)
        return _minimal_report(context)
    if client is None or not settings.bedrock_enabled:
        return fallback
    repair_reason: str | None = None
    for attempt in range(2):
        try:
            prompt = _generation_prompt(context, repair_reason)
            response = client.converse(
                modelId=settings.bedrock_model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
            )
            blocks = response["output"]["message"]["content"]
            text = next(block["text"] for block in blocks if isinstance(block.get("text"), str))
            content = _GeneratedInvestmentAIContent.model_validate(json.loads(text))
            generated = _assemble_bedrock_report(content, context)
            repair_reason = _validation_error(generated, context)
            if repair_reason is None:
                return generated
            logger.warning(
                "AI Deep Dive rejected by guardrail: %s (attempt %s/2)",
                repair_reason,
                attempt + 1,
            )
        except Exception:  # noqa: BLE001
            repair_reason = "provider_or_schema"
            logger.warning(
                "AI Deep Dive provider/schema failure (attempt %s/2)",
                attempt + 1,
                exc_info=True,
            )
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
