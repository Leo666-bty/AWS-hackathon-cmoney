"""Persistence for report claims, feedback and idempotent interaction events."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mindfolio_api.ai.narrative import NarrativeDraft
from mindfolio_api.schemas.retention import InteractionEventInput, ReportHandle
from mindfolio_core.domain.models import ReconstructionResult

if TYPE_CHECKING:
    from mindfolio_api.schemas.reconstruction import TradeConfig


class RetentionUnavailable(RuntimeError):
    pass


class ReportNotFound(RuntimeError):
    pass


class ReportClaimConflict(RuntimeError):
    pass


class InvalidClaimToken(RuntimeError):
    pass


class ReportExpired(RuntimeError):
    pass


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@runtime_checkable
class RetentionRepository(Protocol):
    def create_report(
        self,
        trades: list[TradeConfig],
        result: ReconstructionResult,
        narrative: NarrativeDraft,
        ttl_hours: int,
    ) -> ReportHandle: ...

    def claim_report(self, report_id: str, claim_token: str, member_id: str) -> dict[str, Any]: ...
    def get_member_report(self, member_id: str, report_id: str | None = None) -> dict[str, Any] | None: ...
    def save_ai_report(
        self, member_id: str, report_id: str, report: dict[str, Any], cache_key: str, generated_at: datetime
    ) -> None: ...
    def save_feedback(self, member_id: str, card_id: str, preference: str) -> datetime: ...
    def get_feedback(self, member_id: str, card_id: str) -> str | None: ...
    def add_events(self, member_id: str | None, events: list[InteractionEventInput]) -> list[str]: ...


class InMemoryRetentionRepository:
    def __init__(self) -> None:
        self._reports: dict[str, dict[str, Any]] = {}
        self._feedback: dict[tuple[str, str], tuple[str, datetime]] = {}
        self._events: set[str] = set()

    def create_report(
        self,
        trades: list[TradeConfig],
        result: ReconstructionResult,
        narrative: NarrativeDraft,
        ttl_hours: int,
    ) -> ReportHandle:
        report_id = secrets.token_urlsafe(18)
        claim_token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=ttl_hours)
        self._reports[report_id] = {
            "report_id": report_id,
            "claim_token_hash": _token_hash(claim_token),
            "trades": [trade.model_dump(mode="json") for trade in trades],
            "result": result.model_dump(mode="json"),
            "narrative": narrative.model_dump(mode="json"),
            "claimed_by": None,
            "created_at": now,
            "claimed_at": None,
            "expires_at": expires_at,
            "ai_report": None,
            "ai_report_cache_key": None,
            "ai_report_generated_at": None,
        }
        return ReportHandle(report_id=report_id, claim_token=claim_token, expires_at=expires_at)

    def claim_report(self, report_id: str, claim_token: str, member_id: str) -> dict[str, Any]:
        report = self._reports.get(report_id)
        if report is None:
            raise ReportNotFound(report_id)
        if report["expires_at"] < datetime.now(UTC):
            raise ReportExpired(report_id)
        if not secrets.compare_digest(report["claim_token_hash"], _token_hash(claim_token)):
            raise InvalidClaimToken(report_id)
        if report["claimed_by"] not in (None, member_id):
            raise ReportClaimConflict(report_id)
        if report["claimed_by"] is None:
            report["claimed_by"] = member_id
            report["claimed_at"] = datetime.now(UTC)
        return report.copy()

    def get_member_report(self, member_id: str, report_id: str | None = None) -> dict[str, Any] | None:
        matches = [
            report for report in self._reports.values()
            if report["claimed_by"] == member_id and (report_id is None or report["report_id"] == report_id)
        ]
        if not matches:
            return None
        return max(matches, key=lambda report: report["created_at"]).copy()

    def save_ai_report(
        self, member_id: str, report_id: str, report: dict[str, Any], cache_key: str, generated_at: datetime
    ) -> None:
        stored = self._reports.get(report_id)
        if stored is None or stored["claimed_by"] != member_id:
            raise ReportNotFound(report_id)
        stored["ai_report"] = report
        stored["ai_report_cache_key"] = cache_key
        stored["ai_report_generated_at"] = generated_at

    def save_feedback(self, member_id: str, card_id: str, preference: str) -> datetime:
        now = datetime.now(UTC)
        self._feedback[(member_id, card_id)] = (preference, now)
        return now

    def get_feedback(self, member_id: str, card_id: str) -> str | None:
        value = self._feedback.get((member_id, card_id))
        return value[0] if value else None

    def add_events(self, member_id: str | None, events: list[InteractionEventInput]) -> list[str]:
        del member_id
        accepted: list[str] = []
        for event in events:
            self._events.add(event.event_id)
            accepted.append(event.event_id)
        return accepted


class PgRetentionRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self):
        import psycopg

        try:
            return psycopg.connect(self._dsn, connect_timeout=3)
        except psycopg.OperationalError as exc:
            raise RetentionUnavailable(str(exc)) from exc

    def create_report(
        self,
        trades: list[TradeConfig],
        result: ReconstructionResult,
        narrative: NarrativeDraft,
        ttl_hours: int,
    ) -> ReportHandle:
        from psycopg.types.json import Jsonb

        report_id = secrets.token_urlsafe(18)
        claim_token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=ttl_hours)
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO reconstruction_reports
                      (report_id, claim_token_hash, trades, result, narrative, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        report_id,
                        _token_hash(claim_token),
                        Jsonb([trade.model_dump(mode="json") for trade in trades]),
                        Jsonb(result.model_dump(mode="json")),
                        Jsonb(narrative.model_dump(mode="json")),
                        now,
                        expires_at,
                    ),
                )
        except RetentionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetentionUnavailable(str(exc)) from exc
        return ReportHandle(report_id=report_id, claim_token=claim_token, expires_at=expires_at)

    def claim_report(self, report_id: str, claim_token: str, member_id: str) -> dict[str, Any]:
        from psycopg.rows import dict_row

        try:
            with self._connect() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT * FROM reconstruction_reports WHERE report_id = %s FOR UPDATE", (report_id,))
                report = cur.fetchone()
                if report is None:
                    raise ReportNotFound(report_id)
                if report["expires_at"] < datetime.now(UTC):
                    raise ReportExpired(report_id)
                if not secrets.compare_digest(report["claim_token_hash"], _token_hash(claim_token)):
                    raise InvalidClaimToken(report_id)
                if report["claimed_by"] not in (None, member_id):
                    raise ReportClaimConflict(report_id)
                if report["claimed_by"] is None:
                    claimed_at = datetime.now(UTC)
                    cur.execute(
                        "UPDATE reconstruction_reports SET claimed_by = %s, claimed_at = %s WHERE report_id = %s",
                        (member_id, claimed_at, report_id),
                    )
                    report["claimed_by"] = member_id
                    report["claimed_at"] = claimed_at
                return dict(report)
        except (ReportNotFound, ReportExpired, InvalidClaimToken, ReportClaimConflict):
            raise
        except RetentionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetentionUnavailable(str(exc)) from exc

    def get_member_report(self, member_id: str, report_id: str | None = None) -> dict[str, Any] | None:
        from psycopg.rows import dict_row

        sql = "SELECT * FROM reconstruction_reports WHERE claimed_by = %s"
        params: list[Any] = [member_id]
        if report_id is not None:
            sql += " AND report_id = %s"
            params.append(report_id)
        sql += " ORDER BY created_at DESC LIMIT 1"
        try:
            with self._connect() as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row else None
        except RetentionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetentionUnavailable(str(exc)) from exc

    def save_ai_report(
        self, member_id: str, report_id: str, report: dict[str, Any], cache_key: str, generated_at: datetime
    ) -> None:
        from psycopg.types.json import Jsonb

        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE reconstruction_reports
                    SET ai_report = %s, ai_report_cache_key = %s, ai_report_generated_at = %s
                    WHERE report_id = %s AND claimed_by = %s
                    """,
                    (Jsonb(report), cache_key, generated_at, report_id, member_id),
                )
                if cur.rowcount != 1:
                    raise ReportNotFound(report_id)
        except ReportNotFound:
            raise
        except RetentionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetentionUnavailable(str(exc)) from exc

    def save_feedback(self, member_id: str, card_id: str, preference: str) -> datetime:
        now = datetime.now(UTC)
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO action_card_feedback (member_id, card_id, preference, saved_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (member_id, card_id)
                    DO UPDATE SET preference = EXCLUDED.preference, saved_at = EXCLUDED.saved_at
                    """,
                    (member_id, card_id, preference, now),
                )
        except RetentionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetentionUnavailable(str(exc)) from exc
        return now

    def get_feedback(self, member_id: str, card_id: str) -> str | None:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT preference FROM action_card_feedback WHERE member_id = %s AND card_id = %s",
                    (member_id, card_id),
                )
                row = cur.fetchone()
                return row[0] if row else None
        except RetentionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetentionUnavailable(str(exc)) from exc

    def add_events(self, member_id: str | None, events: list[InteractionEventInput]) -> list[str]:
        from psycopg.types.json import Jsonb

        accepted: list[str] = []
        try:
            with self._connect() as conn, conn.cursor() as cur:
                for event in events:
                    cur.execute(
                        """
                        INSERT INTO interaction_events
                          (event_id, member_id, session_id, event_type, surface, action,
                           stock_id, occurred_at, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO NOTHING
                        """,
                        (
                            event.event_id,
                            member_id,
                            event.session_id,
                            event.event_type,
                            event.surface,
                            event.action,
                            event.stock_id,
                            event.occurred_at,
                            Jsonb(event.metadata),
                        ),
                    )
                    accepted.append(event.event_id)
        except RetentionUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetentionUnavailable(str(exc)) from exc
        return accepted


def build_retention_repository(database_url: str) -> RetentionRepository:
    return PgRetentionRepository(database_url) if database_url else InMemoryRetentionRepository()
