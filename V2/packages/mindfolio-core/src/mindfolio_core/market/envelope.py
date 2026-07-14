"""Pure envelope shaping and price-mode rules.

The catalog stores each month as a dict with keys ``low``, ``high``, ``close``,
``adjustedClose``, ``factor``, ``corporateAction`` and ``regimes`` (see
``V2/tools/build_market_catalog.py``). These helpers turn that raw shape into a
typed :class:`MonthEnvelope` and decide which price-input modes are allowed.
"""

from __future__ import annotations

from typing import Any

from mindfolio_core.domain.models import MonthEnvelope, PriceRegime


def allowed_price_modes(*, corporate_action: bool) -> list[str]:
    """Band estimates are refused in a corporate-action month.

    A corporate action inside the month distorts the merged raw range, so only
    an exact price (which the engine maps to a pre/post regime) is accepted.
    """
    return ["exact"] if corporate_action else ["band", "exact"]


def to_month_envelope(stock_id: str, month: str, raw: dict[str, Any]) -> MonthEnvelope:
    """Map a catalog month dict to a typed envelope; performs no arithmetic."""
    corporate_action = bool(raw["corporateAction"])
    regimes = [
        PriceRegime(low=r["low"], high=r["high"], factor=r["factor"])
        for r in raw.get("regimes", [])
    ]
    return MonthEnvelope(
        stock_id=stock_id,
        month=month,
        raw_low=raw["low"],
        raw_high=raw["high"],
        close=raw["close"],
        adjusted_close=raw["adjustedClose"],
        factor=raw["factor"],
        corporate_action=corporate_action,
        regimes=regimes,
        allowed_price_modes=allowed_price_modes(corporate_action=corporate_action),
    )
