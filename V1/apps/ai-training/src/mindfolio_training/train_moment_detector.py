from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from . import FEATURE_COLUMNS


def train(features: pd.DataFrame) -> Pipeline:
    missing = set(FEATURE_COLUMNS).difference(features.columns)
    if missing:
        raise ValueError(f"Missing feature columns: {sorted(missing)}")

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
            (
                "detector",
                IsolationForest(
                    n_estimators=200,
                    contamination=0.08,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    return pipeline.fit(features[FEATURE_COLUMNS])


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the offline market moment detector.")
    parser.add_argument("features_csv", type=Path)
    parser.add_argument("model_output", type=Path)
    args = parser.parse_args()

    features = pd.read_csv(args.features_csv)
    model = train(features)
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_COLUMNS, "version": "moment-detector-v1"}, args.model_output)


if __name__ == "__main__":
    main()
