"""Shared Mindfolio V2 contracts and deterministic domain logic."""

from mindfolio_core.domain.models import ModelArtifactMetadata
from mindfolio_core.inference import (
    MarketContextArtifact,
    MarketContextArtifactMetadata,
    MarketContextEvidence,
)

__all__ = [
    "MarketContextArtifact",
    "MarketContextArtifactMetadata",
    "MarketContextEvidence",
    "ModelArtifactMetadata",
]
__version__ = "0.1.0"
