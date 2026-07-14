"""Deterministic portfolio reconstruction engine.

Every formula here mirrors ``V2/demo/script.js`` exactly so the backend and the
shipped frontend agree to the digit. Rounding uses ``floor(x + 0.5)`` to match
JavaScript ``Math.round`` (round-half-up), NOT Python's banker's rounding.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mindfolio_core.domain.models import (
    DecisionScores,
    PriceRegime,
    ReconstructionResult,
    TradeResult,
)

# persona headline copy keyed by the first three axes (from demo/script.js).
PERSONA_MAP: dict[str, tuple[str, str]] = {
    "LHD": ("低接收藏家", "你偏好在月內相對低位建立部位，並用較長時間與分散配置等待價值展開。"),
    "LHC": ("深潛集中派", "你願意在價格回落時集中研究少數主題，並以長期持有驗證判斷。"),
    "LAD": ("低點輪動者", "你喜歡在相對低位進場，再依月份節奏主動調整不同產業部位。"),
    "LAC": ("逆勢狙擊手", "你在回落時聚焦少數機會，也會主動尋找離場月份。"),
    "THD": ("趨勢配置師", "你偏好價格確認後進場，並用多產業配置讓趨勢持續發展。"),
    "THC": ("主題領航員", "你會在主題與價格同步後集中投入，並給核心部位更長的驗證時間。"),
    "TAD": ("動能輪動者", "你跟隨市場方向，也會在不同產業與月份之間主動輪動。"),
    "TAC": ("趨勢突擊手", "你重視方向確認、主題集中與明確的進出節奏。"),
}

_BAND_POSITION = {"low": 1 / 6, "mid": 1 / 2, "high": 5 / 6}


def _round(value: float) -> int:
    """Round-half-up, matching JavaScript ``Math.round``."""
    return math.floor(value + 0.5)


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


@dataclass(frozen=True)
class MonthData:
    low: float
    high: float
    close: float
    adjusted_close: float
    factor: float
    corporate_action: bool = False
    regimes: tuple[PriceRegime, ...] = ()


@dataclass(frozen=True)
class TradeInput:
    stock_id: str
    name: str
    industry: str
    relation: str  # "holding" | "sold"
    buy_month: str
    buy_mode: str  # "band" | "exact"
    buy_data: MonthData
    exit_data: MonthData
    future_adjusted: tuple[float, ...] = ()  # adjustedClose of months after buy_month
    buy_band: str = "mid"
    buy_exact: float | None = None
    sell_month: str = "12"
    sell_mode: str = "estimate"  # "estimate" | "exact"
    sell_exact: float | None = None


@dataclass(frozen=True)
class _TradeValues:
    buy_raw: float
    exit_raw: float
    buy_adjusted: float
    exit_adjusted: float
    exit_month: str
    entry_position: float
    duration: int
    confidence: int
    return_pct: float


def price_at_band(low: float, high: float, band: str) -> float:
    return low + (high - low) * _BAND_POSITION[band]


def factor_for_raw_price(month: MonthData, raw_price: float) -> float:
    for regime in month.regimes:
        if regime.low <= raw_price <= regime.high:
            return regime.factor
    return month.factor


def reconstruct_trade(trade: TradeInput) -> _TradeValues:
    buy = trade.buy_data
    exit_data = trade.exit_data
    exit_month = "12" if trade.relation == "holding" else trade.sell_month

    if trade.buy_mode == "exact":
        buy_raw = float(trade.buy_exact or 0.0)
    else:
        buy_raw = price_at_band(buy.low, buy.high, trade.buy_band)

    if trade.relation == "sold" and trade.sell_mode == "exact":
        exit_raw = float(trade.sell_exact or 0.0)
    else:
        exit_raw = exit_data.close

    buy_adjusted = buy_raw * factor_for_raw_price(buy, buy_raw)
    if trade.relation == "holding" or trade.sell_mode == "estimate":
        exit_adjusted = exit_data.adjusted_close
    else:
        exit_adjusted = exit_raw * factor_for_raw_price(exit_data, exit_raw)

    entry_position = (buy_raw - buy.low) / max(buy.high - buy.low, 1e-4)
    duration = int(exit_month) - int(trade.buy_month)

    confidence = 100.0 if trade.buy_mode == "exact" else 78.0
    if trade.relation == "sold" and trade.sell_mode == "estimate":
        confidence -= 8
    if trade.relation == "sold" and trade.sell_mode == "exact":
        confidence = (confidence + 100) / 2
    if buy.corporate_action or exit_data.corporate_action:
        confidence -= 15
    confidence_int = max(45, _round(confidence))

    return_pct = (exit_adjusted / buy_adjusted - 1) * 100
    return _TradeValues(
        buy_raw=buy_raw,
        exit_raw=exit_raw,
        buy_adjusted=buy_adjusted,
        exit_adjusted=exit_adjusted,
        exit_month=exit_month,
        entry_position=entry_position,
        duration=duration,
        confidence=confidence_int,
        return_pct=return_pct,
    )


def reconstruct_portfolio(trades: list[TradeInput]) -> ReconstructionResult:
    if len(trades) != 5:
        raise ValueError(f"Expected exactly 5 trades, got {len(trades)}.")

    values = [reconstruct_trade(t) for t in trades]
    n = len(trades)

    average_return = sum(v.return_pct for v in values) / n
    entry_average = sum(_clamp(v.entry_position, 0, 1) for v in values) / n
    duration_average = sum(v.duration / 11 for v in values) / n
    holdings = [t for t in trades if t.relation == "holding"]

    industry_counts: dict[str, int] = {}
    for t in trades:
        industry_counts[t.industry] = industry_counts.get(t.industry, 0) + 1
    concentration = sum((count / 5) ** 2 for count in industry_counts.values())
    diversity = 1 - concentration

    exact_ratio = sum(1 for t in trades if t.buy_mode == "exact") / n
    confidence = _round(sum(v.confidence for v in values) / n)

    axis1 = "L" if entry_average <= 0.5 else "T"
    axis2 = "H" if (len(holdings) >= 3 or duration_average >= 0.55) else "A"
    axis3 = "D" if diversity >= 0.65 else "C"
    precision = "X" if exact_ratio >= 0.5 else "E"
    prefix = axis1 + axis2 + axis3
    name, headline = PERSONA_MAP[prefix]

    fingerprint = [
        entry_average,
        duration_average,
        diversity,
        exact_ratio,
        _clamp((average_return + 50) / 150, 0, 1),
    ]

    outcome = int(_clamp(_round(20 + average_return * 0.45), 0, 40))
    entry_score = _round((1 - entry_average) * 25)
    capture_values = []
    for t, v in zip(trades, values):
        future = t.future_adjusted
        if not future:
            capture_values.append(10.0)
            continue
        lo, hi = min(future), max(future)
        capture_values.append(6 + (v.exit_adjusted - lo) / max(hi - lo, 1e-4) * 14)
    capture = int(_round(_clamp(sum(capture_values) / len(capture_values), 0, 20)))
    data = _round(confidence / 100 * 15)

    trade_results = [
        TradeResult(
            stock_id=t.stock_id,
            name=t.name,
            industry=t.industry,
            buy_month=t.buy_month,
            exit_month=v.exit_month,
            relation=t.relation,
            buy_raw=v.buy_raw,
            exit_raw=v.exit_raw,
            return_pct=v.return_pct,
            confidence=v.confidence,
        )
        for t, v in zip(trades, values)
    ]

    return ReconstructionResult(
        trades=trade_results,
        average_return=average_return,
        confidence=confidence,
        persona_code=prefix + precision,
        persona_name=name,
        persona_headline=headline,
        fingerprint=fingerprint,
        scores=DecisionScores(
            outcome=outcome, entry=entry_score, capture=capture, data=data
        ),
        holding_candidates=[t.stock_id for t in holdings],
    )
