"""Price validation, mirroring ``validateExact`` in ``V2/demo/script.js``.

A user's remembered exact price must fall within the month's raw range; in a
corporate-action month it must additionally land inside one of the pre/post
regimes so the correct adjustment factor applies.
"""

from __future__ import annotations

import math

from mindfolio_core.domain.models import PriceValidation
from mindfolio_core.market.reconstruction import MonthData


def _fmt(value: float) -> str:
    return f"{value:g}"


def validate_exact_price(month: MonthData, price: float | None) -> PriceValidation:
    if price is None or not math.isfinite(price) or price <= 0:
        return PriceValidation(valid=False, level="bad", message="請輸入大於 0 的成交價格。")

    if price < month.low or price > month.high:
        return PriceValidation(
            valid=False,
            level="bad",
            message=(
                f"超出該月行情 {_fmt(month.low)}–{_fmt(month.high)}，"
                "請確認月份或改用價格區間。"
            ),
        )

    if month.corporate_action:
        regime = next(
            (r for r in month.regimes if r.low <= price <= r.high), None
        )
        if regime is None:
            segments = " 或 ".join(f"{_fmt(r.low)}–{_fmt(r.high)}" for r in month.regimes)
            return PriceValidation(
                valid=False,
                level="bad",
                message=f"該月有公司行動，價格必須落在實際交易區段：{segments}。",
            )
        return PriceValidation(
            valid=True,
            level="warn",
            message=(
                f"價格符合 {_fmt(regime.low)}–{_fmt(regime.high)} 區段，"
                "報酬會用對應還原因子校正。"
            ),
        )

    return PriceValidation(
        valid=True,
        level="good",
        message=f"通過行情驗證：落在 {_fmt(month.low)}–{_fmt(month.high)}。",
    )
