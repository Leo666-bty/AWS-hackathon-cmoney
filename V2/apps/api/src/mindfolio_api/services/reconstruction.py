"""Orchestration for the reconstruction endpoints.

Resolves catalog month data, re-validates every trade from raw input (never
trusting a prior /validate call — Constitution II), builds pure engine inputs,
and runs the deterministic engine. All numbers come from mindfolio-core.
"""

from __future__ import annotations

from typing import Any

from mindfolio_api.repositories.holdings import HoldingsRepository
from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_api.schemas.reconstruction import TradeConfig
from mindfolio_core.domain.models import (
    ConfirmedHolding,
    PriceRegime,
    PriceValidation,
    ReconstructionResult,
)
from mindfolio_core.market.reconstruction import MonthData, TradeInput, reconstruct_portfolio
from mindfolio_core.market.validation import validate_exact_price


class StockNotFound(Exception):
    def __init__(self, stock_id: str) -> None:
        super().__init__(stock_id)
        self.stock_id = stock_id


class MonthNotFound(Exception):
    def __init__(self, stock_id: str, month: str) -> None:
        super().__init__(f"{stock_id} {month}")
        self.stock_id = stock_id
        self.month = month


class TradeValidationError(Exception):
    def __init__(self, index: int, message: str) -> None:
        super().__init__(message)
        self.index = index
        self.message = message


def month_to_data(raw: dict[str, Any]) -> MonthData:
    return MonthData(
        low=raw["low"],
        high=raw["high"],
        close=raw["close"],
        adjusted_close=raw["adjustedClose"],
        factor=raw["factor"],
        corporate_action=bool(raw["corporateAction"]),
        regimes=tuple(
            PriceRegime(low=r["low"], high=r["high"], factor=r["factor"])
            for r in raw.get("regimes", [])
        ),
    )


def validate_buy(catalog: MarketCatalog, config: TradeConfig) -> PriceValidation:
    """Buy-side validation for the /validate endpoint (the builder's inline check)."""
    stock = catalog.get_stock(config.stock_id)
    if stock is None:
        raise StockNotFound(config.stock_id)
    raw = stock["months"].get(config.buy_month)
    if raw is None:
        raise MonthNotFound(config.stock_id, config.buy_month)

    buy = month_to_data(raw)
    if config.buy_mode == "exact":
        return validate_exact_price(buy, config.buy_exact)
    if buy.corporate_action:
        return PriceValidation(
            valid=False, level="bad", message="該月有公司行動，請改輸入實際成交價格。"
        )
    return PriceValidation(
        valid=True, level="good", message=f"可用價格區間估算（{buy.low:g}–{buy.high:g}）。"
    )


def _trade_error(stock: dict[str, Any], config: TradeConfig) -> str | None:
    """Return a reason string if the trade is invalid, else None."""
    months = stock["months"]
    buy_raw = months.get(config.buy_month)
    if buy_raw is None:
        return f"買進月份 {config.buy_month} 無行情資料。"
    buy = month_to_data(buy_raw)

    if config.buy_mode == "exact":
        result = validate_exact_price(buy, config.buy_exact)
        if not result.valid:
            return result.message
    elif buy.corporate_action:
        return "該月有公司行動，價格區間不可用，請改輸入實際成交價格。"

    if config.relation == "sold":
        if int(config.sell_month) <= int(config.buy_month):
            return "賣出月份必須晚於買進月份。"
        sell_raw = months.get(config.sell_month)
        if sell_raw is None:
            return f"賣出月份 {config.sell_month} 無行情資料。"
        if config.sell_mode == "exact":
            result = validate_exact_price(month_to_data(sell_raw), config.sell_exact)
            if not result.valid:
                return result.message
    return None


def _build_trade_input(stock: dict[str, Any], config: TradeConfig) -> TradeInput:
    months = stock["months"]
    exit_month = "12" if config.relation == "holding" else config.sell_month
    future_adjusted = tuple(
        data["adjustedClose"]
        for month, data in months.items()
        if int(month) > int(config.buy_month)
    )
    return TradeInput(
        stock_id=stock["id"],
        name=stock["name"],
        industry=stock["industry"],
        relation=config.relation,
        buy_month=config.buy_month,
        buy_mode=config.buy_mode,
        buy_data=month_to_data(months[config.buy_month]),
        exit_data=month_to_data(months[exit_month]),
        future_adjusted=future_adjusted,
        buy_band=config.buy_band,
        buy_exact=config.buy_exact,
        sell_month=config.sell_month,
        sell_mode=config.sell_mode,
        sell_exact=config.sell_exact,
    )


def complete_reconstruction(
    catalog: MarketCatalog, configs: list[TradeConfig]
) -> ReconstructionResult:
    stocks: list[dict[str, Any]] = []
    for config in configs:
        stock = catalog.get_stock(config.stock_id)
        if stock is None:
            raise StockNotFound(config.stock_id)
        stocks.append(stock)

    for index, (stock, config) in enumerate(zip(stocks, configs)):
        error = _trade_error(stock, config)
        if error is not None:
            raise TradeValidationError(index, error)

    inputs = [_build_trade_input(stock, config) for stock, config in zip(stocks, configs)]
    return reconstruct_portfolio(inputs)


def confirm_holdings(
    catalog: MarketCatalog,
    repo: HoldingsRepository,
    user_id: str,
    configs: list[TradeConfig],
) -> list[ConfirmedHolding]:
    """Re-run the reconstruction to derive holding candidates, then persist them.

    Only stocks the reconstruction marks as `holding` are written (Constitution
    V) — the client cannot smuggle in a watch/sold stock as a confirmed holding.
    Raises the same 404/422 as `complete`, plus HoldingsUnavailable (→ 503).
    """
    result = complete_reconstruction(catalog, configs)
    if result.holding_candidates:
        return repo.add_holdings(user_id, result.holding_candidates)
    return repo.list_holdings(user_id)
