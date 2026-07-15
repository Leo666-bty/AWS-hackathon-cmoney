from pathlib import Path

from mindfolio_training.features import build_monthly_features


def test_build_monthly_features_from_official_package() -> None:
    data_dir = Path(__file__).parents[4] / "V1/data/Delivery_Hackathon_DataPackage_20260624"
    if not data_dir.exists():
        return
    features = build_monthly_features(data_dir)
    assert len(features) > 3_000
    assert features[["stock_id", "month"]].duplicated().sum() == 0
    assert features["community_bullish_ratio"].between(0, 1).all()
    assert features["institutional_flow_ratio"].notna().all()
