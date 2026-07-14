from datetime import UTC, datetime

from mindfolio_core import ModelArtifactMetadata
from mindfolio_core.features import FEATURE_VERSION


def initialized_artifact_metadata(model_name: str) -> ModelArtifactMetadata:
    return ModelArtifactMetadata(
        model_name=model_name,
        model_version="untrained",
        feature_version=FEATURE_VERSION,
        training_range=("2025-01-01", "2025-12-31"),
        sample_count=0,
        metrics={},
        generated_at=datetime.now(UTC),
    )
