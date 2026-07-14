import pytest
from fastapi.testclient import TestClient

from mindfolio_api.main import create_app
from mindfolio_api.repositories.holdings import (
    HoldingsUnavailable,
    InMemoryHoldingsRepository,
)
from mindfolio_api.repositories.market_data import MarketCatalog


def _month():
    return {
        "low": 100,
        "high": 120,
        "close": 110,
        "adjustedClose": 110.0,
        "factor": 1.0,
        "corporateAction": False,
        "regimes": [{"low": 100, "high": 120, "factor": 1.0}],
    }


def _stock(stock_id, industry):
    return {
        "id": stock_id,
        "name": stock_id,
        "industry": industry,
        "views": 100,
        "popular": False,
        "months": {f"{m:02d}": _month() for m in range(1, 13)},
    }


CATALOG = {
    "asOf": "2025-12-31",
    "stocks": [_stock(s, ind) for s, ind in
               [("S1", "半導體"), ("S2", "航運"), ("S3", "金融"), ("S4", "電腦"), ("S5", "生技")]],
}


def _holding(stock_id):
    return {"stock_id": stock_id, "relation": "holding", "buy_month": "01", "buy_mode": "band", "buy_band": "mid"}


def _sold(stock_id):
    return {"stock_id": stock_id, "relation": "sold", "buy_month": "01", "buy_mode": "band",
            "buy_band": "mid", "sell_month": "06", "sell_mode": "estimate"}


def _client(holdings=None) -> TestClient:
    return TestClient(
        create_app(
            catalog=MarketCatalog(CATALOG),
            holdings_repo=holdings or InMemoryHoldingsRepository(),
        )
    )


def test_confirm_writes_only_holdings() -> None:
    client = _client()
    # 3 holdings + 2 sold → only the 3 holdings become confirmed
    trades = [_holding("S1"), _holding("S2"), _holding("S3"), _sold("S4"), _sold("S5")]
    res = client.post("/api/v2/confirmed-holdings", json={"user_id": "LEO", "trades": trades})
    assert res.status_code == 200
    ids = {h["stock_id"] for h in res.json()}
    assert ids == {"S1", "S2", "S3"}
    assert all(h["source"] == "user_confirmed" for h in res.json())


def test_confirm_then_list() -> None:
    client = _client()
    trades = [_holding(s) for s in ("S1", "S2", "S3", "S4", "S5")]
    client.post("/api/v2/confirmed-holdings", json={"user_id": "LEO", "trades": trades})
    listed = client.get("/api/v2/users/LEO/confirmed-holdings").json()
    assert {h["stock_id"] for h in listed} == {"S1", "S2", "S3", "S4", "S5"}


def test_confirm_unknown_stock_404() -> None:
    client = _client()
    trades = [_holding("S1"), _holding("S2"), _holding("S3"), _holding("S4"), _holding("NOPE")]
    assert client.post("/api/v2/confirmed-holdings", json={"user_id": "LEO", "trades": trades}).status_code == 404


def test_confirm_invalid_trade_422() -> None:
    client = _client()
    trades = [_holding(s) for s in ("S1", "S2", "S3", "S4", "S5")]
    trades[0] = {"stock_id": "S1", "relation": "holding", "buy_month": "01", "buy_mode": "exact", "buy_exact": 9999}
    assert client.post("/api/v2/confirmed-holdings", json={"user_id": "LEO", "trades": trades}).status_code == 422


class _FailingRepo:
    def add_holdings(self, user_id, stock_ids):
        raise HoldingsUnavailable("db down")

    def list_holdings(self, user_id):
        raise HoldingsUnavailable("db down")


def test_db_down_returns_503() -> None:
    client = _client(holdings=_FailingRepo())
    trades = [_holding(s) for s in ("S1", "S2", "S3", "S4", "S5")]
    assert client.post("/api/v2/confirmed-holdings", json={"user_id": "LEO", "trades": trades}).status_code == 503
    assert client.get("/api/v2/users/LEO/confirmed-holdings").status_code == 503
