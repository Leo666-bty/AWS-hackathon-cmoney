import json

import pytest

from mindfolio_api.repositories.market_data import (
    MarketCatalog,
    MarketDataUnavailable,
)

CATALOG = {
    "asOf": "2025-12-31",
    "stockCount": 3,
    "popular": ["2330", "2317"],
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
            "id": "2317",
            "name": "鴻海",
            "industry": "電子–其他",
            "views": 120000,
            "popular": True,
            "months": {},
        },
        {
            "id": "2382",
            "name": "廣達",
            "industry": "電子–電腦及週邊設備",
            "views": 96032,
            "popular": False,
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
def catalog() -> MarketCatalog:
    return MarketCatalog(CATALOG)


def test_popular_ordered_by_views_and_capped(catalog: MarketCatalog) -> None:
    ids = [s.id for s in catalog.popular(limit=2)]
    assert ids == ["2330", "2317"]


def test_popular_clamps_limit(catalog: MarketCatalog) -> None:
    assert len(catalog.popular(limit=0)) == 1  # clamped to >= 1
    assert len(catalog.popular(limit=999)) == 3  # clamped to <= 100, capped by size


def test_search_matches_code_name_industry(catalog: MarketCatalog) -> None:
    assert [s.id for s in catalog.search("台積", limit=20)] == ["2330"]
    assert [s.id for s in catalog.search("2382", limit=20)] == ["2382"]
    # industry substring matches all three "電子–…" members
    assert {s.id for s in catalog.search("電子", limit=20)} == {"2330", "2317", "2382"}


def test_search_empty_query_returns_empty(catalog: MarketCatalog) -> None:
    assert catalog.search("", limit=20) == []
    assert catalog.search("   ", limit=20) == []


def test_envelope_hit_normal_month(catalog: MarketCatalog) -> None:
    env = catalog.envelope("2330", "2025-04")
    assert env is not None
    assert env.raw_low == 780.0
    assert env.raw_high == 952.0
    assert env.corporate_action is False
    assert env.allowed_price_modes == ["band", "exact"]


def test_envelope_corporate_action_month(catalog: MarketCatalog) -> None:
    env = catalog.envelope("2382", "2025-06")
    assert env is not None
    assert env.corporate_action is True
    assert env.allowed_price_modes == ["exact"]


def test_envelope_miss_returns_none(catalog: MarketCatalog) -> None:
    assert catalog.envelope("2330", "2025-07") is None  # no such month
    assert catalog.envelope("9999", "2025-04") is None  # no such stock
    assert catalog.envelope("2330", "2024-04") is None  # wrong catalog year


def test_from_file_roundtrip(tmp_path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    loaded = MarketCatalog.from_file(path)
    assert [s.id for s in loaded.popular(limit=2)] == ["2330", "2317"]


def test_from_file_missing_raises(tmp_path) -> None:
    with pytest.raises(MarketDataUnavailable) as excinfo:
        MarketCatalog.from_file(tmp_path / "does-not-exist.json")
    assert "does-not-exist.json" in str(excinfo.value)
