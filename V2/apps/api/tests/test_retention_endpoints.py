from fastapi.testclient import TestClient

from mindfolio_api.main import create_app
from mindfolio_api.repositories.holdings import InMemoryHoldingsRepository
from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_api.repositories.retention import InMemoryRetentionRepository


def _month(close: float = 110.0):
    return {
        "low": 100,
        "high": 120,
        "close": close,
        "adjustedClose": close,
        "factor": 1.0,
        "corporateAction": False,
        "regimes": [{"low": 100, "high": 120, "factor": 1.0}],
    }


def _stock(stock_id: str, name: str):
    return {
        "id": stock_id,
        "name": name,
        "industry": "電子",
        "views": 100,
        "popular": True,
        "months": {f"{month:02d}": _month() for month in range(1, 13)},
    }


CATALOG = {
    "asOf": "2025-12-31",
    "stocks": [
        _stock("2382", "廣達"),
        _stock("S2", "S2"),
        _stock("S3", "S3"),
        _stock("S4", "S4"),
        _stock("S5", "S5"),
    ],
}


def _holding(stock_id: str):
    return {
        "stock_id": stock_id,
        "relation": "holding",
        "buy_month": "01",
        "buy_mode": "band",
        "buy_band": "mid",
    }


def _client() -> TestClient:
    return TestClient(
        create_app(
            catalog=MarketCatalog(CATALOG),
            holdings_repo=InMemoryHoldingsRepository(),
            retention_repo=InMemoryRetentionRepository(),
        )
    )


def _complete(client: TestClient):
    response = client.post(
        "/api/v2/reconstructions/complete",
        json={"trades": [_holding(stock) for stock in ("2382", "S2", "S3", "S4", "S5")]},
    )
    assert response.status_code == 200
    return response.json()["report"]


def _auth(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v2/auth/session", json={"invite_code": "demo-leo"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_invite_code_is_exchanged_for_a_session_token() -> None:
    client = _client()
    session = client.post("/api/v2/auth/session", json={"invite_code": "demo-leo"})
    assert session.status_code == 200
    assert session.json()["access_token"] != "demo-leo"
    assert client.get(
        "/api/v2/me/dashboard",
        headers={"Authorization": "Bearer demo-leo"},
    ).status_code == 401


def test_report_claim_to_dashboard_happy_path() -> None:
    client = _client()
    report = _complete(client)
    headers = _auth(client)

    claim = client.post(
        f"/api/v2/reports/{report['report_id']}/claim",
        json={"claim_token": report["claim_token"]},
        headers=headers,
    )
    assert claim.status_code == 200
    assert claim.json()["member_id"] == "LEO"

    confirmed = client.post(
        f"/api/v2/reports/{report['report_id']}/confirmed-holdings",
        json={"stock_ids": ["2382", "S2"]},
        headers=headers,
    )
    assert confirmed.status_code == 200
    assert {item["stock_id"] for item in confirmed.json()} == {"2382", "S2"}

    dashboard = client.get("/api/v2/me/dashboard", headers=headers)
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["report"]["report_id"] == report["report_id"]
    assert len(body["portfolio"]) == 2
    assert body["priority_card"] is not None
    assert body["priority_card"]["narrative_source"] == "fallback"
    assert body["weekly_review"]["source"] == "snapshot"
    assert body["weekly_review"]["data_as_of"] == "2025-12-31"


def _sold(stock_id: str):
    return {
        "stock_id": stock_id,
        "relation": "sold",
        "buy_month": "01",
        "buy_mode": "band",
        "buy_band": "mid",
        "sell_month": "06",
    }


def test_confirm_rejects_non_holding_candidate() -> None:
    """Consent gate: a sold (non-holding) stock can never be confirmed, even
    through a validly claimed report — the server re-derives candidates."""
    client = _client()
    trades = [_holding(s) for s in ("2382", "S2", "S3")] + [_sold("S4"), _sold("S5")]
    report = client.post(
        "/api/v2/reconstructions/complete", json={"trades": trades}
    ).json()["report"]
    headers = _auth(client)
    client.post(
        f"/api/v2/reports/{report['report_id']}/claim",
        json={"claim_token": report["claim_token"]},
        headers=headers,
    )

    rejected = client.post(
        f"/api/v2/reports/{report['report_id']}/confirmed-holdings",
        json={"stock_ids": ["S4"]},  # sold → not a holding candidate
        headers=headers,
    )
    assert rejected.status_code == 422

    accepted = client.post(
        f"/api/v2/reports/{report['report_id']}/confirmed-holdings",
        json={"stock_ids": ["2382"]},
        headers=headers,
    )
    assert accepted.status_code == 200
    assert {item["stock_id"] for item in accepted.json()} == {"2382"}


def test_identity_and_claim_are_isolated() -> None:
    client = _client()
    report = _complete(client)
    assert client.get("/api/v2/me/dashboard").status_code == 401
    headers = _auth(client)
    invalid = client.post(
        f"/api/v2/reports/{report['report_id']}/claim",
        json={"claim_token": "x" * 32},
        headers=headers,
    )
    assert invalid.status_code == 403


def test_feedback_and_event_batch_are_retry_safe() -> None:
    client = _client()
    report = _complete(client)
    headers = _auth(client)
    client.post(
        f"/api/v2/reports/{report['report_id']}/claim",
        json={"claim_token": report["claim_token"]},
        headers=headers,
    )
    client.post(
        f"/api/v2/reports/{report['report_id']}/confirmed-holdings",
        json={"stock_ids": ["2382"]},
        headers=headers,
    )
    dashboard = client.get("/api/v2/me/dashboard", headers=headers).json()
    card_id = dashboard["priority_card"]["card_id"]
    feedback = client.post(
        f"/api/v2/me/action-cards/{card_id}/feedback",
        json={"preference": "mute"},
        headers=headers,
    )
    assert feedback.status_code == 200
    assert client.get("/api/v2/me/dashboard", headers=headers).json()["priority_card"]["current_preference"] == "mute"

    payload = {
        "events": [{
            "event_id": "event-retry-safe-001",
            "session_id": "session-1",
            "event_type": "portfolio_view",
            "surface": "portfolio_radar",
            "occurred_at": "2026-07-15T00:00:00Z",
            "metadata": {},
        }]
    }
    first = client.post("/api/v2/events/batch", json=payload, headers=headers)
    second = client.post("/api/v2/events/batch", json=payload, headers=headers)
    assert first.json() == second.json() == {"accepted_event_ids": ["event-retry-safe-001"]}
