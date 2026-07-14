"""In-memory market catalog loaded from the built JSON snapshot.

The catalog is a read-only fixture produced by
``V2/tools/build_market_catalog.py`` (no database in the MVP). It is loaded once
at startup and queried for the popular list, search, and month envelopes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mindfolio_core.domain.models import MonthEnvelope, StockSummary
from mindfolio_core.market.envelope import to_month_envelope

_LIMIT_MIN = 1
_LIMIT_MAX = 100


class MarketDataUnavailable(RuntimeError):
    """Raised when the catalog file is missing or unreadable (fail fast)."""


def _clamp_limit(limit: int) -> int:
    return max(_LIMIT_MIN, min(_LIMIT_MAX, limit))


class MarketCatalog:
    """Query interface over the loaded market catalog."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._year = str(data.get("asOf", ""))[:4]
        self._stocks: list[dict[str, Any]] = list(data.get("stocks", []))
        self._by_id: dict[str, dict[str, Any]] = {s["id"]: s for s in self._stocks}
        # Popular/search order is deterministic: highest view count first.
        self._ranked = sorted(
            self._stocks, key=lambda s: s.get("views", 0), reverse=True
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "MarketCatalog":
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise MarketDataUnavailable(
                f"Market catalog not found at {path}. "
                "Run: python3 V2/tools/build_market_catalog.py --json"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise MarketDataUnavailable(
                f"Market catalog at {path} is unreadable: {exc}"
            ) from exc
        return cls(data)

    def popular(self, limit: int = 12) -> list[StockSummary]:
        return [_to_summary(s) for s in self._ranked[: _clamp_limit(limit)]]

    def search(self, q: str, limit: int = 20) -> list[StockSummary]:
        needle = q.strip().casefold()
        if not needle:
            return []
        matches = [
            s
            for s in self._ranked
            if needle in s["id"].casefold()
            or needle in s["name"].casefold()
            or needle in s.get("industry", "").casefold()
        ]
        return [_to_summary(s) for s in matches[: _clamp_limit(limit)]]

    def get_stock(self, stock_id: str) -> dict[str, Any] | None:
        """Raw catalog record for a stock (id, name, industry, views, months)."""
        return self._by_id.get(stock_id)

    def envelope(self, stock_id: str, month: str) -> MonthEnvelope | None:
        stock = self._by_id.get(stock_id)
        if stock is None:
            return None
        year, _, mm = month.partition("-")
        if year != self._year or not mm:
            return None
        raw = stock.get("months", {}).get(mm)
        if raw is None:
            return None
        return to_month_envelope(stock_id, month, raw)


def _to_summary(stock: dict[str, Any]) -> StockSummary:
    return StockSummary(
        id=stock["id"],
        name=stock["name"],
        industry=stock.get("industry", ""),
        views=int(stock.get("views", 0)),
        popular=bool(stock.get("popular", False)),
        available_months=sorted(stock.get("months", {}).keys()),
    )
