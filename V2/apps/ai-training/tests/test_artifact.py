from mindfolio_training.artifact import initialized_artifact_metadata


def test_initialized_artifact_is_not_fake_training_result() -> None:
    metadata = initialized_artifact_metadata("market-regime-kmeans")

    assert metadata.model_version == "untrained"
    assert metadata.sample_count == 0
    assert metadata.metrics == {}
