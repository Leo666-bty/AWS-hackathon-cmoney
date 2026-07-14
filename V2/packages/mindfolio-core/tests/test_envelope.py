from mindfolio_core.domain.models import MonthEnvelope, PriceRegime
from mindfolio_core.market.envelope import allowed_price_modes, to_month_envelope


def test_allowed_price_modes_normal_month() -> None:
    assert allowed_price_modes(corporate_action=False) == ["band", "exact"]


def test_allowed_price_modes_corporate_action_month() -> None:
    assert allowed_price_modes(corporate_action=True) == ["exact"]


def _raw(**overrides: object) -> dict:
    base = {
        "low": 174.0,
        "high": 248.0,
        "close": 238.5,
        "adjustedClose": 227.66,
        "factor": 0.95446541,
        "corporateAction": False,
        "regimes": [{"low": 174.0, "high": 248.0, "factor": 0.95446541}],
    }
    base.update(overrides)
    return base


def test_to_month_envelope_maps_all_fields() -> None:
    env = to_month_envelope("2382", "2025-04", _raw())

    assert isinstance(env, MonthEnvelope)
    assert env.stock_id == "2382"
    assert env.month == "2025-04"
    assert env.raw_low == 174.0
    assert env.raw_high == 248.0
    assert env.close == 238.5
    assert env.adjusted_close == 227.66
    assert env.factor == 0.95446541
    assert env.corporate_action is False
    assert env.allowed_price_modes == ["band", "exact"]
    assert env.regimes == [PriceRegime(low=174.0, high=248.0, factor=0.95446541)]


def test_to_month_envelope_corporate_action_disables_band() -> None:
    raw = _raw(
        corporateAction=True,
        regimes=[
            {"low": 100.0, "high": 120.0, "factor": 1.0},
            {"low": 60.0, "high": 72.0, "factor": 0.5},
        ],
    )

    env = to_month_envelope("9999", "2025-06", raw)

    assert env.corporate_action is True
    assert env.allowed_price_modes == ["exact"]
    assert len(env.regimes) == 2
