"""Tests encode the demo/script.js formulas as the oracle (frontend parity)."""

import pytest

from mindfolio_core.domain.models import PriceRegime
from mindfolio_core.market.reconstruction import (
    MonthData,
    TradeInput,
    factor_for_raw_price,
    price_at_band,
    reconstruct_portfolio,
    reconstruct_trade,
)


def test_price_at_band() -> None:
    assert price_at_band(100, 160, "low") == 110  # 100 + 60/6
    assert price_at_band(100, 160, "mid") == 130  # 100 + 60/2
    assert price_at_band(100, 160, "high") == 150  # 100 + 60*5/6


def test_factor_for_raw_price_picks_regime() -> None:
    month = MonthData(
        low=60,
        high=120,
        close=110,
        adjusted_close=100,
        factor=0.9,
        corporate_action=True,
        regimes=(
            PriceRegime(low=100, high=120, factor=1.0),
            PriceRegime(low=60, high=72, factor=0.5),
        ),
    )
    assert factor_for_raw_price(month, 110) == 1.0
    assert factor_for_raw_price(month, 65) == 0.5
    assert factor_for_raw_price(month, 200) == 0.9  # no regime → month factor


def test_reconstruct_trade_holding_exact() -> None:
    buy = MonthData(low=90, high=110, close=105, adjusted_close=105, factor=1.0)
    exit_ = MonthData(low=110, high=130, close=120, adjusted_close=130, factor=1.0)
    trade = TradeInput(
        stock_id="2330",
        name="台積電",
        industry="電子–半導體",
        relation="holding",
        buy_month="01",
        buy_mode="exact",
        buy_exact=100,
        buy_data=buy,
        exit_data=exit_,
    )
    v = reconstruct_trade(trade)
    assert v.buy_raw == 100
    assert v.buy_adjusted == 100  # factor 1.0
    assert v.exit_adjusted == 130  # holding → adjusted_close
    assert v.exit_month == "12"
    assert v.duration == 11
    assert v.entry_position == 0.5  # (100-90)/20
    assert v.confidence == 100
    assert v.return_pct == pytest.approx(30.0)  # 130/100 - 1


def _holding_exact_trade(stock_id: str, industry: str) -> TradeInput:
    buy = MonthData(low=90, high=110, close=105, adjusted_close=105, factor=1.0)
    exit_ = MonthData(low=110, high=130, close=120, adjusted_close=130, factor=1.0)
    return TradeInput(
        stock_id=stock_id,
        name=stock_id,
        industry=industry,
        relation="holding",
        buy_month="01",
        buy_mode="exact",
        buy_exact=100,
        buy_data=buy,
        exit_data=exit_,
        future_adjusted=(130,),
    )


def test_portfolio_lhdx_diversified_holdings() -> None:
    trades = [
        _holding_exact_trade("A", "半導體"),
        _holding_exact_trade("B", "航運"),
        _holding_exact_trade("C", "金融"),
        _holding_exact_trade("D", "電腦"),
        _holding_exact_trade("E", "生技"),
    ]
    r = reconstruct_portfolio(trades)

    assert r.persona_code == "LHDX"
    assert r.persona_name == "低接收藏家"
    assert r.average_return == pytest.approx(30.0)
    assert r.confidence == 100
    assert r.scores.outcome == 34  # round(20 + 30*0.45) = round(33.5) = 34
    assert r.scores.entry == 13  # round((1-0.5)*25) = round(12.5) = 13 (half-up)
    assert r.scores.data == 15
    assert r.scores.capture == 6  # exit==future min==max → 6
    assert r.fingerprint[2] == pytest.approx(0.8)  # diversity: 1 - 5*(1/5)^2
    assert r.holding_candidates == ["A", "B", "C", "D", "E"]


def _sold_band_trade(stock_id: str) -> TradeInput:
    buy = MonthData(low=100, high=110, close=108, adjusted_close=108, factor=1.0)
    exit_ = MonthData(low=100, high=112, close=104, adjusted_close=104, factor=1.0)
    return TradeInput(
        stock_id=stock_id,
        name=stock_id,
        industry="半導體",  # same industry for all → low diversity
        relation="sold",
        buy_month="10",
        buy_mode="band",
        buy_band="high",  # entry_position 5/6 ≈ 0.833 → axis "T"
        buy_data=buy,
        exit_data=exit_,
        sell_month="11",
        sell_mode="estimate",
    )


def test_portfolio_tace_active_concentrated_estimated() -> None:
    trades = [_sold_band_trade(str(i)) for i in range(5)]
    r = reconstruct_portfolio(trades)

    assert r.persona_code == "TACE"
    assert r.persona_name == "趨勢突擊手"
    assert r.holding_candidates == []
    # band=78, sold&estimate -8 → 70
    assert all(t.confidence == 70 for t in r.trades)


def test_reproducible() -> None:
    trades = [_holding_exact_trade(c, c) for c in "ABCDE"]
    assert reconstruct_portfolio(trades) == reconstruct_portfolio(trades)
