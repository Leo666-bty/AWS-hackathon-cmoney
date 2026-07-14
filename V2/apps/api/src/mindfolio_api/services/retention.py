from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from mindfolio_api.ai.narrative import NarrativeDraft
from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_api.schemas.retention import (
    ActionCard,
    CardEvidence,
    DashboardHolding,
    DashboardReport,
    MemberDashboard,
    WeeklyReview,
)
from mindfolio_core.domain.models import ConfirmedHolding, DecisionScores


def build_action_card(
    catalog: MarketCatalog,
    holding: ConfirmedHolding,
    preference: str | None,
) -> ActionCard:
    stock = catalog.get_stock(holding.stock_id)
    name = stock["name"] if stock else holding.stock_id
    card_id = f"historical-review-{holding.stock_id}-2025"

    if holding.stock_id == "2382":
        return ActionCard(
            card_id=card_id,
            stock_id="2382",
            stock_name=name,
            title="法人與社群觀點在 2025 年底出現背離",
            summary="短期法人轉買，但 20 日籌碼仍偏保守；社群看多討論明顯集中。先看證據，再決定是否需要持續追蹤。",
            as_of="2025-12-31",
            provenance="CMoney Hackathon 2025 historical dataset",
            narrative_source="fallback",
            evidence=[
                CardEvidence(label="單日法人", value="+3,957 張", tone="positive"),
                CardEvidence(label="20 日法人", value="−60,265 張", tone="warning"),
                CardEvidence(label="社群看多", value="93.9%", tone="positive"),
                CardEvidence(label="殖利率", value="4.78%", tone="neutral"),
            ],
            suggested_questions=["法人短買、長賣代表什麼？", "社群 93.9% 的分母是什麼？", "這會影響我的提醒頻率嗎？"],
            current_preference=preference,
        )

    month = stock.get("months", {}).get("12") if stock else None
    close = f"{month['close']:g}" if month else "資料不足"
    return ActionCard(
        card_id=card_id,
        stock_id=holding.stock_id,
        stock_name=name,
        title=f"{name} 的 2025 年底持股回顧已整理",
        summary="這是封存行情的歷史回顧卡，不是即時訊號；正式上線即時資料前，不會以舊資料冒充今天的市場狀態。",
        as_of="2025-12-31",
        provenance="CMoney Hackathon 2025 historical dataset",
        narrative_source="fallback",
        evidence=[
            CardEvidence(label="年底收盤", value=close, tone="neutral"),
            CardEvidence(label="關係來源", value="使用者確認持股", tone="positive"),
        ],
        suggested_questions=["這張卡的資料日期？", "為什麼沒有即時行情？", "如何降低同類提醒？"],
        current_preference=preference,
    )


def build_dashboard(
    *,
    member_id: str,
    display_name: str,
    report: dict[str, Any] | None,
    holdings: list[ConfirmedHolding],
    catalog: MarketCatalog,
    feedback: str | None,
) -> MemberDashboard:
    dashboard_report: DashboardReport | None = None
    if report:
        result = report["result"]
        dashboard_report = DashboardReport(
            report_id=report["report_id"],
            persona_code=result["persona_code"],
            persona_name=result["persona_name"],
            persona_headline=result["persona_headline"],
            confidence=result["confidence"],
            average_return=result["average_return"],
            scores=DecisionScores.model_validate(result["scores"]),
            narrative=NarrativeDraft.model_validate(report["narrative"]),
            created_at=report["created_at"],
        )

    portfolio: list[DashboardHolding] = []
    for holding in holdings:
        stock = catalog.get_stock(holding.stock_id)
        portfolio.append(
            DashboardHolding(
                stock_id=holding.stock_id,
                name=stock["name"] if stock else holding.stock_id,
                industry=stock.get("industry", "") if stock else "",
                source=holding.source,
                confirmed_at=holding.confirmed_at,
            )
        )

    priority_card = build_action_card(catalog, holdings[0], feedback) if holdings else None
    next_review = (datetime.now(UTC) + timedelta(days=7)).date().isoformat()
    return MemberDashboard(
        member_id=member_id,
        display_name=display_name,
        report=dashboard_report,
        portfolio=portfolio,
        priority_card=priority_card,
        weekly_review=WeeklyReview(
            title="每週 Portfolio Review",
            summary=(
                f"目前有 {len(portfolio)} 檔已確認持股。下一次回顧會優先整理有來源日期的市場證據。"
                if portfolio else "先從 Time Machine 確認至少一檔仍持有股票，Portfolio Radar 才會開始運作。"
            ),
            next_review_at=next_review,
            data_as_of="2025-12-31",
            source="snapshot" if portfolio else "fixture",
        ),
    )
