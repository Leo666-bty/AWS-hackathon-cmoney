from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from mindfolio_core.features import FEATURE_VERSION, MONTHLY_FEATURE_KEYS, WINSOR_QUANTILES
from mindfolio_core.inference import MarketContextArtifact
from mindfolio_training.features import build_monthly_features

MODEL_VERSION = "2025-v1"
SOURCE_AS_OF = "2025-12-31"


def _canonical_hash(contexts: dict[str, object]) -> str:
    payload = json.dumps(contexts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _regime_label(centroid: pd.Series) -> str:
    if centroid["volatility"] > 0.5 and centroid["monthly_return"] < 0:
        return "高波動承壓"
    if centroid["volatility"] > 0.5 and centroid["monthly_return"] >= 0:
        return "高波動修復"
    if centroid["institutional_flow_ratio"] > 0.4:
        return "法人資金偏多"
    if centroid["community_heat"] > 0.5:
        return "社群熱度升溫"
    if centroid["monthly_return"] > 0.3:
        return "趨勢偏強"
    return "盤整觀察"


def train_and_export(features: pd.DataFrame, artifact_path: Path, model_path: Path) -> MarketContextArtifact:
    raw = features.loc[:, MONTHLY_FEATURE_KEYS].astype(float).copy()
    lower = raw.quantile(WINSOR_QUANTILES[0])
    upper = raw.quantile(WINSOR_QUANTILES[1])
    clipped = raw.clip(lower=lower, upper=upper, axis=1)
    scaled = RobustScaler().fit_transform(clipped)

    candidates: list[tuple[int, float, float, KMeans]] = []
    for clusters in range(3, 7):
        model = KMeans(n_clusters=clusters, random_state=42, n_init=20)
        labels = model.fit_predict(scaled)
        score = float(silhouette_score(scaled, labels))
        largest_cluster_ratio = float(pd.Series(labels).value_counts().max() / len(labels))
        candidates.append((clusters, score, largest_cluster_ratio, model))
    balanced = [candidate for candidate in candidates if candidate[2] <= 0.75]
    cluster_count, silhouette, largest_cluster_ratio, kmeans = max(
        balanced or candidates, key=lambda candidate: candidate[1]
    )
    labels = kmeans.labels_

    isolation = IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
    isolation.fit(scaled)
    raw_anomaly = -isolation.score_samples(scaled)
    anomaly_percentile = pd.Series(raw_anomaly).rank(method="average", pct=True).to_numpy()

    distances = kmeans.transform(scaled)
    assigned_distance = distances[np.arange(len(features)), labels]
    distance_percentile = pd.Series(assigned_distance).rank(method="average", pct=True).to_numpy()
    centroids = pd.DataFrame(kmeans.cluster_centers_, columns=MONTHLY_FEATURE_KEYS)
    regime_names = {index: _regime_label(row) for index, row in centroids.iterrows()}

    contexts: dict[str, object] = {}
    for position, row in features.reset_index(drop=True).iterrows():
        anomaly_score = round(float(anomaly_percentile[position]), 4)
        anomaly_level = "significant" if anomaly_score >= 0.95 else "attention" if anomaly_score >= 0.85 else "general"
        match = "strong" if distance_percentile[position] <= 0.4 else "moderate" if distance_percentile[position] <= 0.75 else "weak"
        salient_indexes = np.argsort(np.abs(scaled[position]))[-3:][::-1]
        salient = [MONTHLY_FEATURE_KEYS[index] for index in salient_indexes]
        key = f"{row['stock_id']}:{row['month']}"
        contexts[key] = {
            "stock_id": str(row["stock_id"]),
            "month": str(row["month"]),
            "regime_id": int(labels[position]),
            "regime_label": regime_names[int(labels[position])],
            "regime_match": match,
            "anomaly_level": anomaly_level,
            "anomaly_score": anomaly_score,
            "salient_feature_keys": salient,
            "evidence": {
                "monthly_return": round(float(row["monthly_return"]), 6),
                "volatility": round(float(row["volatility"]), 6),
                "max_drawdown": round(float(row["max_drawdown"]), 6),
                "institutional_net": round(float(row["institutional_net"]), 3),
                "institutional_flow_ratio": round(float(row["institutional_flow_ratio"]), 6),
                "community_posts": int(row["post_count"]),
                "community_replies": int(row["reply_count"]),
                "community_bullish_ratio": round(float(row["community_bullish_ratio"]), 4),
            },
            "feature_version": FEATURE_VERSION,
            "model_version": MODEL_VERSION,
            "source_as_of": SOURCE_AS_OF,
        }

    artifact_data = {
        "metadata": {
            "model_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "training_range": ["2025-01-01", SOURCE_AS_OF],
            "sample_count": len(features),
            "feature_keys": list(MONTHLY_FEATURE_KEYS),
            "preprocessing": {
                "scaler": "RobustScaler",
                "winsor_quantiles": list(WINSOR_QUANTILES),
                "missing_values": "drop incomplete stock-month after documented defaults",
            },
            "metrics": {
                "silhouette": round(silhouette, 6),
                "cluster_count": cluster_count,
                "largest_cluster_ratio": round(largest_cluster_ratio, 6),
                "selection_policy": "highest silhouette among candidates with largest cluster <= 75%",
                "cluster_sizes": {str(key): int(value) for key, value in pd.Series(labels).value_counts().sort_index().items()},
                "anomaly_rate": round(float((anomaly_percentile >= 0.95).mean()), 6),
            },
            "generated_at": datetime.now(UTC).isoformat(),
        },
        "contexts": contexts,
        "content_sha256": _canonical_hash(contexts),
    }
    artifact = MarketContextArtifact.model_validate(artifact_data)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"kmeans": kmeans, "isolation_forest": isolation}, model_path)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Mindfolio monthly features and pre-score market context.")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--features-output", type=Path, required=True)
    parser.add_argument("--artifact-output", type=Path, required=True)
    parser.add_argument("--model-output", type=Path, required=True)
    args = parser.parse_args()
    features = build_monthly_features(args.data_dir)
    args.features_output.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(args.features_output, index=False)
    artifact = train_and_export(features, args.artifact_output, args.model_output)
    print(json.dumps(artifact.metadata.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
