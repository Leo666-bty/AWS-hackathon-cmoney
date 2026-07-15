import json
from pathlib import Path

from mindfolio_api.repositories.market_context import MarketContextRepository


def test_runtime_artifact_is_ready_and_lookup_is_constant_keyed() -> None:
    path = Path(__file__).parents[3] / "data/market-context-2025-v1.json"
    repository = MarketContextRepository.from_file(path)
    assert repository.status == "ready"
    assert repository.model_version == "2025-v1"
    assert repository.get("2330", "2025-04") is not None


def test_tampered_artifact_fails_soft(tmp_path: Path) -> None:
    source = Path(__file__).parents[3] / "data/market-context-2025-v1.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["contexts"][next(iter(payload["contexts"]))]["regime_label"] = "tampered"
    target = tmp_path / "bad.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    repository = MarketContextRepository.from_file(target)
    assert repository.status == "unavailable"
    assert repository.get("2330", "2025-04") is None
