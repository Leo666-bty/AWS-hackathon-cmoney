from mindfolio_core.domain.models import PriceRegime
from mindfolio_core.market.reconstruction import MonthData
from mindfolio_core.market.validation import validate_exact_price

NORMAL = MonthData(low=780, high=952, close=908, adjusted_close=892, factor=0.98)
CORP = MonthData(
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


def test_zero_or_negative_price_bad() -> None:
    assert validate_exact_price(NORMAL, 0).valid is False
    assert validate_exact_price(NORMAL, -5).level == "bad"
    assert validate_exact_price(NORMAL, None).valid is False


def test_out_of_range_bad() -> None:
    v = validate_exact_price(NORMAL, 1000)
    assert v.valid is False
    assert v.level == "bad"


def test_in_range_good() -> None:
    v = validate_exact_price(NORMAL, 850)
    assert v.valid is True
    assert v.level == "good"


def test_corporate_action_price_in_regime_warn() -> None:
    v = validate_exact_price(CORP, 110)  # inside first regime
    assert v.valid is True
    assert v.level == "warn"


def test_corporate_action_price_between_regimes_bad() -> None:
    v = validate_exact_price(CORP, 90)  # in [low,high] but no regime
    assert v.valid is False
    assert v.level == "bad"
