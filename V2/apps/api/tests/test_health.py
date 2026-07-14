from fastapi.testclient import TestClient

from mindfolio_api.main import app


def test_health() -> None:
    response = TestClient(app).get("/api/v2/health")

    assert response.status_code == 200
    assert response.json()["service"] == "mindfolio-api"
    assert response.json()["model_status"] == "not_loaded"
    assert response.json()["narrative_status"] == "fallback_ready"
