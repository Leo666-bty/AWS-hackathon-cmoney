from datetime import UTC, datetime

from mindfolio_core import ModelArtifactMetadata


def test_model_artifact_metadata_contract() -> None:
    metadata = ModelArtifactMetadata(
        model_name="market-regime-kmeans",
        model_version="2025-v1",
        feature_version="monthly-features-v1",
        training_range=("2025-01-01", "2025-12-31"),
        sample_count=3584,
        metrics={"silhouette": 0.0},
        generated_at=datetime.now(UTC),
    )

    assert metadata.sample_count == 3584
