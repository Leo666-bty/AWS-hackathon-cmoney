"""Confirmed-holdings persistence.

Market data is file-based; only user-confirmed holdings are persisted. In
production this is PostgreSQL self-hosted on the EC2 instance (per-request
connections keep it simple and robust for the hackathon). A DB outage raises
``HoldingsUnavailable`` which the router turns into HTTP 503 — it never crashes
startup or blocks the reconstruction loop. Local dev/tests use the in-memory
implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from mindfolio_core.domain.models import ConfirmedHolding


class HoldingsUnavailable(RuntimeError):
    """The persistence backend is unreachable (→ HTTP 503)."""


@runtime_checkable
class HoldingsRepository(Protocol):
    def add_holdings(
        self,
        user_id: str,
        stock_ids: list[str],
        source_report_id: str | None = None,
    ) -> list[ConfirmedHolding]: ...
    def list_holdings(self, user_id: str) -> list[ConfirmedHolding]: ...


class InMemoryHoldingsRepository:
    """Non-persistent store for local dev and tests."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], ConfirmedHolding] = {}

    def add_holdings(
        self,
        user_id: str,
        stock_ids: list[str],
        source_report_id: str | None = None,
    ) -> list[ConfirmedHolding]:
        del source_report_id
        now = datetime.now(UTC)
        for stock_id in stock_ids:
            self._data[(user_id, stock_id)] = ConfirmedHolding(
                user_id=user_id, stock_id=stock_id, confirmed_at=now
            )
        return self.list_holdings(user_id)

    def list_holdings(self, user_id: str) -> list[ConfirmedHolding]:
        holdings = [h for (uid, _), h in self._data.items() if uid == user_id]
        return sorted(holdings, key=lambda h: (h.confirmed_at, h.stock_id), reverse=True)


class PgHoldingsRepository:
    """PostgreSQL-backed store using a fresh connection per request."""

    _INSERT = (
        "INSERT INTO confirmed_holdings (user_id, stock_id, source_report_id) VALUES (%s, %s, %s) "
        "ON CONFLICT (user_id, stock_id) DO UPDATE SET confirmed_at = NOW(), "
        "source_report_id = EXCLUDED.source_report_id, last_reviewed_at = NOW()"
    )
    _SELECT = (
        "SELECT user_id, stock_id, source, confirmed_at FROM confirmed_holdings "
        "WHERE user_id = %s ORDER BY confirmed_at DESC, stock_id"
    )

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def add_holdings(
        self,
        user_id: str,
        stock_ids: list[str],
        source_report_id: str | None = None,
    ) -> list[ConfirmedHolding]:
        import psycopg

        try:
            with psycopg.connect(self._dsn, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    for stock_id in stock_ids:
                        cur.execute(self._INSERT, (user_id, stock_id, source_report_id))
                conn.commit()
        except psycopg.OperationalError as exc:
            raise HoldingsUnavailable(str(exc)) from exc
        return self.list_holdings(user_id)

    def list_holdings(self, user_id: str) -> list[ConfirmedHolding]:
        import psycopg
        from psycopg.rows import dict_row

        try:
            with psycopg.connect(self._dsn, connect_timeout=3) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(self._SELECT, (user_id,))
                    rows = cur.fetchall()
        except psycopg.OperationalError as exc:
            raise HoldingsUnavailable(str(exc)) from exc
        return [ConfirmedHolding(**row) for row in rows]


def build_holdings_repository(database_url: str) -> HoldingsRepository:
    if not database_url:
        return InMemoryHoldingsRepository()
    return PgHoldingsRepository(database_url)
