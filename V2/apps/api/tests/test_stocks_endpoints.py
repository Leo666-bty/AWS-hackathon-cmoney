import pytest
from fastapi.testclient import TestClient

from mindfolio_api.main import create_app
from mindfolio_api.repositories.market_data import MarketCatalog

CATALOG = {
    "asOf": "2025-12-31",
    "stocks": [
        {
            "id": "2330",
            "name": "台積電",
            "industry": "電子–半導體",
            "views": 253191,
            "popular": True,
            "months": {
                "04": {
                    "low": 780.0,
                    "high": 952.0,
                    "close": 908.0,
                    "adjustedClose": 892.0,
                    "factor": 0.98,
                    "corporateAction": False,
                    "regimes": [{"low": 780.0, "high": 952.0, "factor": 0.98}],
                }
            },
        },
        {
            "id": "2382",
            "name": "廣達",
            "industry": "電子–電腦及週邊設備",
            "views": 96032,
            "popular": True,
            "months": {
                "06": {
                    "low": 100.0,
                    "high": 120.0,
                    "close": 110.0,
                    "adjustedClose": 55.0,
                    "factor": 0.5,
                    "corporateAction": True,
                    "regimes": [
                        {"low": 100.0, "high": 120.0, "factor": 1.0},
                        {"low": 60.0, "high": 72.0, "factor": 0.5},
                    ],
                }
            },
        },
    ],
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(catalog=MarketCatalog(CATALOG)))


def test_popular_ordered_and_capped(client: TestClient) -> None:
    res = client.get("/api/v2/stocks/popular", params={"limit": 1})
    assert res.status_code == 200
    body = res.json()
    assert [s["id"] for s in body] == ["2330"]
    assert set(body[0]) >= {"id", "name", "industry", "views", "popular"}


def test_search_and_empty_query(client: TestClient) -> None:
    assert [s["id"] for s in client.get("/api/v2/stocks/search", params={"q": "台積"}).json()] == ["2330"]
    assert client.get("/api/v2/stocks/search", params={"q": "   "}).json() == []


def test_envelope_normal_month(client: TestClient) -> None:
    res = client.get("/api/v2/stocks/2330/months/2025-04/envelope")
    assert res.status_code == 200
    body = res.json()
    assert body["stock_id"] == "2330"
    assert body["raw_low"] == 780.0
    assert body["raw_high"] == 952.0
    assert body["corporate_action"] is False
    assert body["allowed_price_modes"] == ["band", "exact"]


def test_envelope_corporate_action_month(client: TestClient) -> None:
    res = client.get("/api/v2/stocks/2382/months/2025-06/envelope")
    assert res.status_code == 200
    assert res.json()["allowed_price_modes"] == ["exact"]


def test_envelope_unknown_stock_or_month_404(client: TestClient) -> None:
    assert client.get("/api/v2/stocks/9999/months/2025-04/envelope").status_code == 404
    r = client.get("/api/v2/stocks/2330/months/2025-07/envelope")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_envelope_malformed_month_422(client: TestClient) -> None:
    assert client.get("/api/v2/stocks/2330/months/2025-4/envelope").status_code == 422
    assert client.get("/api/v2/stocks/2330/months/April/envelope").status_code == 422
