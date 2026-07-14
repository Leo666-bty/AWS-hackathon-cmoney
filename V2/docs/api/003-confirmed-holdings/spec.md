# Feature Specification: Confirmed Holdings (consent + persistence)

**Feature Directory**: `V2/docs/api/003-confirmed-holdings`

**Created**: 2026-07-14 | **Status**: Superseded (endpoints removed; write path
migrated to the retention report-scoped flow)

> **SUPERSEDED (retention P0)**: the two endpoints below were **removed for
> security** — they were unauthenticated and trusted a client-supplied
> `user_id`, a cross-member isolation hole. Confirmed holdings are now written
> only through the session-authenticated, report-scoped
> `POST /api/v2/reports/{report_id}/confirmed-holdings` (see `routers/retention.py`;
> the caller must first `POST /auth/session` and `POST /reports/{id}/claim`). The
> stateless re-verification, Constitution-V candidate gate, and 503-on-DB-down
> behaviour below still hold — only the transport and the identity source changed
> (server-derived `member_id`, never a client `user_id`). The
> `confirmed_holdings` table also gained `source_report_id` and `last_reviewed_at`.

**Input**: The final docs/09 endpoint — persist a user's "still holding" stocks
after explicit consent. Deployment decision (2026-07-14): PostgreSQL
**self-hosted on the same EC2 instance** as the API (not RDS); market data
stays file-based, only confirmed holdings are persisted.

## Design

- **Stateless re-verification**: the backend re-runs `complete_reconstruction`
  to derive `holding_candidates`, and writes **only those** (Constitution V — a
  client cannot smuggle a watch/sold stock in as a confirmed holding). In the
  superseding retention flow the trades come from the claimed
  `reconstruction_reports` row (not re-sent by the client), and the writer key is
  the server-derived `member_id`. (The original 003 design re-sent the five
  trades against an anonymous `user_id`; that path was removed.)
- **Persistence**: table `confirmed_holdings (user_id, stock_id, source
  CHECK 'user_confirmed', confirmed_at, source_report_id, last_reviewed_at)`,
  upsert on `(user_id, stock_id)`. `source_report_id` records the retention
  report the holding was confirmed from; `last_reviewed_at` supports weekly
  review. `V2/infra/schema/001_init.sql` (now a four-table schema alongside
  `reconstruction_reports`, `action_card_feedback`, `interaction_events`).
  Repository is a Protocol with an in-memory impl (dev/tests) and a psycopg3 impl
  (per-request connection, `connect_timeout=3`).
- **Degradation**: a DB outage raises `HoldingsUnavailable` → HTTP 503 at
  request time; it never crashes startup (Postgres is reached lazily, not at
  boot) and never blocks the reconstruction loop.

## Endpoints

> **REMOVED** — both endpoints below no longer exist. See the superseded banner
> above. The replacement is `POST /api/v2/reports/{report_id}/confirmed-holdings`
> (session-authenticated; body `{stock_ids[1..5]}`; re-verifies against the
> claimed report's trades, writes only holding candidates with `source_report_id`,
> returns the member's confirmed holdings; 404 · 422 · 503). Portfolio listing is
> now served inside `GET /api/v2/me/dashboard` (`portfolio` field), not a separate
> per-`user_id` GET.

- ~~`POST /api/v2/confirmed-holdings`~~ — removed (unauthenticated, trusted client `user_id`).
- ~~`GET /api/v2/users/{user_id}/confirmed-holdings`~~ — removed (unauthenticated, trusted client `user_id`).

## Requirements

- **FR-001**: Only stocks the re-run marks `holding` are persisted; watch/sold
  are never written.
- **FR-002**: `source` is DB-CHECK-constrained to `user_confirmed`.
- **FR-003**: Re-submitting confirms idempotently (upsert on user+stock).
- **FR-004**: DB outage → 503; startup and the reconstruction loop are unaffected.
- **FR-005**: `DATABASE_URL` selects Postgres; empty → in-memory (non-persistent,
  dev only).

## Success Criteria

- **SC-001**: 3 holding + 2 sold trades → exactly the 3 holdings confirmed.
- **SC-002**: With the store unavailable, the write path returns 503 (verified
  with a failing repo). Now applies to `POST /reports/{id}/confirmed-holdings`.
- **SC-003**: Confirm → list round-trips the confirmed set.

## Assumptions / notes

- **Resolved by retention P0**: the earlier "no reconstruction/session storage"
  and "anonymous vs member separation is a later hardening step" notes no longer
  hold. `reconstruction_reports` now persists the report; identity is a
  server-derived `member_id` from an invite-code session (never a client
  `user_id`); confirmed holdings are written only after `POST /reports/{id}/claim`
  binds the report to that member.
- Docker Compose mounts `V2/infra/schema/001_init.sql` into
  `/docker-entrypoint-initdb.d/001_init.sql`, so it runs automatically only when
  `pgdata` is first initialized. Existing volumes require an explicit migration;
  manual `psql` is not needed for a fresh Compose deployment.
