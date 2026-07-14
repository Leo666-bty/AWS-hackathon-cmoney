from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def _moment_type(row: pd.Series) -> str:
    if row["institution_community_divergence"] >= 1:
        return "institution_community_divergence"
    if max(row["post_count_z20"], row["reply_count_z20"]) >= 2:
        return "discussion_heat_spike"
    if abs(row["institutional_net_z20"]) >= 2:
        return "institution_flow_anomaly"
    if max(abs(row["return_1d"]), abs(row["return_5d"])) >= 0.05:
        return "price_momentum_anomaly"
    return "mixed_anomaly"


def score(features: pd.DataFrame, bundle: dict) -> list[dict]:
    columns = bundle["features"]
    raw = -bundle["model"].decision_function(features[columns])
    minimum, maximum = float(raw.min()), float(raw.max())
    normalized = np.full_like(raw, 0.5) if maximum == minimum else (raw - minimum) / (maximum - minimum)

    results: list[dict] = []
    for (_, row), anomaly_score in zip(features.iterrows(), normalized):
        value = round(float(anomaly_score), 4)
        severity = "significant" if value >= 0.9 else "attention" if value >= 0.8 else "info"
        results.append(
            {
                "stock_id": str(row["stock_id"]),
                "as_of": str(row["date"]),
                "moment_type": _moment_type(row),
                "anomaly_score": value,
                "severity": severity,
                "evidence": {
                    "institutional_net_20d": int(row["institutional_net_20d"]),
                    "community_bullish_ratio_7d": round(float(row["community_bullish_ratio_7d"]), 4),
                    "return_5d": round(float(row["return_5d"]), 4),
                },
                "model_version": bundle["version"],
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Score features and write MomentSignal JSONL.")
    parser.add_argument("features_csv", type=Path)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    args = parser.parse_args()

    moments = score(pd.read_csv(args.features_csv), joblib.load(args.model_path))
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8") as output:
        for moment in moments:
            output.write(json.dumps(moment, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
