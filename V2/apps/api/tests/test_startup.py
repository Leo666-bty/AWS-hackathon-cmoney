import pytest

from mindfolio_api.config import get_settings
from mindfolio_api.main import create_app
from mindfolio_api.repositories.market_data import MarketDataUnavailable


def test_startup_fails_fast_on_missing_catalog(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MINDFOLIO_MARKET_DATA_PATH", str(tmp_path / "missing.json"))
    get_settings.cache_clear()
    try:
        with pytest.raises(MarketDataUnavailable) as excinfo:
            create_app()
        assert "missing.json" in str(excinfo.value)
    finally:
        get_settings.cache_clear()
