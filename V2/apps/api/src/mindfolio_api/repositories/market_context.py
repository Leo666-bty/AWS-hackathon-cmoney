from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mindfolio_core.features import FEATURE_VERSION
from mindfolio_core.inference import MarketContextArtifact, MarketContextEvidence


class MarketContextRepository:
    def __init__(self, artifact: MarketContextArtifact | None = None, error: str | None = None) -> None:
        self._artifact = artifact
        self.error = error

    @classmethod
    def from_file(cls, path: str | Path) -> "MarketContextRepository":
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            artifact = MarketContextArtifact.model_validate(payload)
            if artifact.metadata.feature_version != FEATURE_VERSION:
                raise ValueError("feature version mismatch")
            canonical = json.dumps(
                {key: value.model_dump(mode="json") for key, value in artifact.contexts.items()},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if checksum != artifact.content_sha256:
                raise ValueError("content checksum mismatch")
            return cls(artifact=artifact)
        except Exception as exc:  # noqa: BLE001 - market context is fail-soft.
            return cls(error=str(exc))

    @property
    def status(self) -> str:
        return "ready" if self._artifact is not None else "unavailable"

    @property
    def model_version(self) -> str | None:
        return self._artifact.metadata.model_version if self._artifact else None

    @property
    def content_sha256(self) -> str | None:
        return self._artifact.content_sha256 if self._artifact else None

    def get(self, stock_id: str, month: str) -> MarketContextEvidence | None:
        if self._artifact is None:
            return None
        return self._artifact.contexts.get(f"{stock_id}:{month}")
