import pytest
from fastapi.testclient import TestClient

from mindfolio_api.main import create_app
from mindfolio_api.repositories.market_data import MarketCatalog


def _month(low=100, high=120, close=110, adj=110.0, factor=1.0, corp=False, regimes=None):
    return {
        "low": low,
        "high": high,
        "close": close,
        "adjustedClose": adj,
        "factor": factor,
        "corporateAction": corp,
        "regimes": regimes or [{"low": low, "high": high, "factor": factor}],
    }


def _stock(stock_id, industry, views, corp_month=None):
    months = {f"{m:02d}": _month() for m in range(1, 13)}
    if corp_month:
        months[corp_month] = _month(
            low=60,
            high=120,
            corp=True,
            regimes=[
                {"low": 100, "high": 120, "factor": 1.0},
                {"low": 60, "high": 72, "factor": 0.5},
            ],
        )
    return {"id": stock_id, "name": stock_id, "industry": industry, "views": views, "popular": False, "months": months}


CATALOG = {
    "asOf": "2025-12-31",
    "stocks": [
        _stock("S1", "半導體", 500),
        _stock("S2", "航運", 400),
        _stock("S3", "金融", 300),
        _stock("S4", "電腦", 200),
        _stock("S5", "生技", 100),
        _stock("CORP", "半導體", 50, corp_month="03"),
    ],
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(catalog=MarketCatalog(CATALOG)))


def _holding(stock_id):
    return {"stock_id": stock_id, "relation": "holding", "buy_month": "01", "buy_mode": "band", "buy_band": "mid"}


def test_complete_happy_path(client: TestClient) -> None:
    trades = [_holding(s) for s in ("S1", "S2", "S3", "S4", "S5")]
    res = client.post("/api/v2/reconstructions/complete", json={"trades": trades})
    assert res.status_code == 200
    body = res.json()
    assert len(body["result"]["trades"]) == 5
    assert body["result"]["persona_code"]
    assert body["result"]["holding_candidates"] == ["S1", "S2", "S3", "S4", "S5"]
    assert body["narrative"]["headline"]  # fallback narrative present (Bedrock disabled)


def test_complete_invalid_trade_422(client: TestClient) -> None:
    trades = [_holding(s) for s in ("S1", "S2", "S3", "S4", "S5")]
    trades[2] = {"stock_id": "S3", "relation": "holding", "buy_month": "01", "buy_mode": "exact", "buy_exact": 9999}
    res = client.post("/api/v2/reconstructions/complete", json={"trades": trades})
    assert res.status_code == 422
    assert "Trade 2" in res.json()["detail"]


def test_complete_unknown_stock_404(client: TestClient) -> None:
    trades = [_holding(s) for s in ("S1", "S2", "S3", "S4", "NOPE")]
    res = client.post("/api/v2/reconstructions/complete", json={"trades": trades})
    assert res.status_code == 404


def test_complete_requires_five_trades_422(client: TestClient) -> None:
    trades = [_holding(s) for s in ("S1", "S2", "S3", "S4")]
    assert client.post("/api/v2/reconstructions/complete", json={"trades": trades}).status_code == 422


def test_validate_exact_in_range_good(client: TestClient) -> None:
    res = client.post(
        "/api/v2/reconstructions/validate",
        json={"stock_id": "S1", "buy_month": "01", "buy_mode": "exact", "buy_exact": 110},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["valid"] is True and body["level"] == "good"


def test_validate_band_on_corporate_action_bad(client: TestClient) -> None:
    res = client.post(
        "/api/v2/reconstructions/validate",
        json={"stock_id": "CORP", "buy_month": "03", "buy_mode": "band"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["valid"] is False and body["level"] == "bad"


def test_validate_unknown_stock_404(client: TestClient) -> None:
    res = client.post(
        "/api/v2/reconstructions/validate",
        json={"stock_id": "NOPE", "buy_month": "01", "buy_mode": "band"},
    )
    assert res.status_code == 404
