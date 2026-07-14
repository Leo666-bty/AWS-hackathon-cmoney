# Feature Specification: Confirmed Holdings (consent + persistence)

**Feature Directory**: `V2/docs/api/003-confirmed-holdings`

**Created**: 2026-07-14 | **Status**: Implemented

**Input**: The final docs/09 endpoint — persist a user's "still holding" stocks
after explicit consent. Deployment decision (2026-07-14): PostgreSQL
**self-hosted on the same EC2 instance** as the API (not RDS); market data
stays file-based, only confirmed holdings are persisted.

## Design

- **Stateless re-verification** (no reconstruction/session storage): the client
  re-sends the five trades; the backend re-runs `complete_reconstruction` to
  derive `holding_candidates`, and writes **only those** (Constitution V — a
  client cannot smuggle a watch/sold stock in as a confirmed holding).
- **Persistence**: one table `confirmed_holdings (user_id, stock_id, source
  CHECK 'user_confirmed', confirmed_at)`, upsert on `(user_id, stock_id)`.
  `V2/infra/schema/001_init.sql`. Repository is a Protocol with an in-memory
  impl (dev/tests) and a psycopg3 impl (per-request connection, `connect_timeout=3`).
- **Degradation**: a DB outage raises `HoldingsUnavailable` → HTTP 503 at
  request time; it never crashes startup (Postgres is reached lazily, not at
  boot) and never blocks the reconstruction loop.

## Endpoints

- `POST /api/v2/confirmed-holdings` — body `{user_id, trades[5]}`; re-verifies,
  writes the holding candidates, returns the user's confirmed holdings.
  404 unknown stock · 422 invalid trade / wrong count · 503 DB down.
- `GET /api/v2/users/{user_id}/confirmed-holdings` — list; 503 DB down.

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
- **SC-002**: With the store unavailable, both endpoints return 503 (verified
  with a failing repo).
- **SC-003**: Confirm → list round-trips the confirmed set.

## Assumptions / notes

- `user_id` carries whichever identifier the caller supplies; anonymous vs
  member separation (Constitution V) is a later hardening step.
- Apply the schema on the EC2 Postgres once: `psql "$DATABASE_URL" -f
  V2/infra/schema/001_init.sql`.
