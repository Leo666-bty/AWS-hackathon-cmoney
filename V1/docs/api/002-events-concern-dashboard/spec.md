# Feature Specification: Interaction Events, Concern Feedback & Dashboard

**Feature Directory**: `docs/api/002-events-concern-dashboard`

**Created**: 2026-07-14

**Status**: Draft (spec skeleton — clarify/plan/tasks pending co-design)

**Input**: The `apps/api/contracts/openapi.yaml` v0.2.0 surface beyond the core
loop, plus `docs/11_COMPLETE_MVP_SPEC.md` sections 8–13. This feature is the
telemetry / concern-signal / internal-dashboard layer that sits on top of the
feature 001 core loop. It shares `infra/schema/001_init.sql` (tables
`interaction_events`, `concern_feedback`, `demo_news`).

## Relationship to feature 001

001 owns the core loop (context, cards, feedback, portfolio, health, reset).
002 depends on 001's tables (users, stocks, action_cards) existing but the 001
loop does not depend on 002. 002 adds four contract endpoints:
`POST /v1/events/batch`, `GET /v1/users/{user_id}/events`,
`POST /v1/users/{user_id}/concern-feedback`, `GET /v1/dashboard/metrics`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Idempotent Interaction Event Ingest (Priority: P1)

The web front-end records interaction events into a local outbox and flushes
them in batches; the API persists each event exactly once, keyed by
`event_id`, so a re-sent batch (offline retry, double-flush) never
double-counts. Events only move from `queued` to `synced` after the API
accepts them (docs/11 §10: never simulate success).

**Independent Test**: POST a batch of events → all `event_id`s returned as
accepted; POST the same batch again → still accepted, but the stored row count
is unchanged.

**Acceptance Scenarios**:

1. **Given** a batch of 1–100 well-formed events, **When** `POST /v1/events/batch`
   is called, **Then** each is persisted once and the response returns the
   accepted `event_id`s (HTTP 202).
2. **Given** a batch containing `event_id`s already stored, **When** it is
   re-posted, **Then** duplicates are absorbed idempotently (no second row,
   still 202).
3. **Given** a batch with an unknown `event_type`, empty batch, or > 100
   events, **When** posted, **Then** the API responds with a validation error
   (HTTP 422) [NEEDS CLARIFICATION: reject the whole batch, or accept the valid
   subset and report rejected ids? The outbox retry model favors all-or-nothing
   per batch — confirm].
4. **Given** stored events, **When** `GET /v1/users/{user_id}/events?limit=`
   is called, **Then** recent events for that user are returned newest-first
   (demo inspection).

---

### User Story 2 - Concern Signal (Priority: P2)

After seeing a card, the user may state a low-friction reminder preference —
`worried` / `routine` / `mute` — which is recorded as an explicit signal
(docs/11: this is a user statement, never a model-inferred emotion).

**Independent Test**: POST concern-feedback `worried` for a card → 202; the
record is stored with its `occurred_at` and is retrievable/aggregated.

**Acceptance Scenarios**:

1. **Given** a valid `{stock_id, card_id, concern, occurred_at}`, **When**
   `POST /v1/users/{user_id}/concern-feedback` is called, **Then** it is
   persisted (HTTP 202) with `concern ∈ {worried, routine, mute}`.
2. **Given** an invalid `concern` value or missing field, **When** posted,
   **Then** HTTP 422, nothing stored.
3. **Given** the system, **Then** concern data MUST never be surfaced or
   framed as the user's emotional/psychological state — it is a reminder
   preference only.

---

### User Story 3 - Internal Funnel Dashboard (Priority: P3)

An internal viewer sees the minimum operational funnel — event count, card
impressions, relationship-feedback count, confirmed holdings — to verify the
demo is producing real interaction data (docs/11 §4: internal verification
plane, kept off the front-facing pages).

**Independent Test**: Run the 001 loop + emit events → `GET /v1/dashboard/metrics`
reflects the increments.

**Acceptance Scenarios**:

1. **Given** stored events and feedback, **When** `GET /v1/dashboard/metrics`
   is called, **Then** it returns `event_count`, `card_impressions`,
   `relationship_feedback_count`, `confirmed_holdings` [NEEDS CLARIFICATION:
   exact definition of each metric — e.g. is `card_impressions` counted from
   `card_impression` events, or from served cards? Is the dashboard global or
   per-user? docs/11 shows it as a global demo funnel].

---

### Edge Cases

- Event referencing an unknown `user_id`/`stock_id`/`card_id` — [NEEDS
  CLARIFICATION: FK-reject (422/409) or accept with null FK? interaction_events
  has nullable stock_id/card_id but non-null user_id FK].
- Clock skew: client `occurred_at` far in the future/past — store as given
  (client truth for ordering), `received_at` is server truth.
- Partial batch failure mid-transaction — batch is one transaction; on any
  hard error nothing is committed (consistent with idempotent retry).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement the four 002 contract endpoints exactly
  per `apps/api/contracts/openapi.yaml` v0.2.0 (event batch, event read,
  concern-feedback, dashboard metrics) — no invented fields.
- **FR-002**: Event ingest MUST be idempotent on `event_id` (PK); re-posting
  stored events MUST NOT create duplicates and MUST still return 202.
- **FR-003**: A batch MUST accept 1–100 events; violations → 422.
- **FR-004**: Concern-feedback MUST persist `{stock_id, card_id, concern,
  occurred_at}` with `concern ∈ {worried, routine, mute}` and MUST NOT be
  framed as inferred emotion (Constitution III).
- **FR-005**: The dashboard MUST return the four funnel counts computed
  deterministically from stored rows (Constitution II).
- **FR-006**: `occurred_at` is client-supplied truth for ordering;
  `received_at` is the server default and MUST be set on write.
- **FR-007**: All writes for a single request MUST be one transaction; DB
  unreachable → 503 with `detail`.

### Key Entities

- **Interaction Event**: `event_id` (UUID PK, idempotency key), `session_id`,
  `event_type` (12-value enum), `user_id` FK, nullable `stock_id`/`card_id`
  FKs, `surface`, `action?`, `source_date?`, `metadata JSONB`, `occurred_at`,
  `received_at`.
- **Concern Feedback**: user's `worried`/`routine`/`mute` on a card, with
  `occurred_at`/`received_at`.
- **Dashboard Metrics**: derived aggregate (not stored) — event count, card
  impressions, relationship-feedback count, confirmed holdings.
- **Demo News**: seeded `is_demo=true` items (read by 001's context endpoint;
  002 owns the table and any `news_open` telemetry).

## Success Criteria *(mandatory)*

- **SC-001**: Re-posting an identical event batch leaves the stored event count
  unchanged (idempotency proven).
- **SC-002**: 100% of the 12 `event_type` values are accepted and readable back.
- **SC-003**: Dashboard counts equal the underlying row counts after a scripted
  demo run (deterministic, reproducible).
- **SC-004**: Concern-feedback of each of the three values is stored and
  aggregated; no code path labels it as emotion.

## Assumptions

- Feature 001 (core loop + schema applied) exists first; 002 builds on it.
- Front-end owns the outbox/queue; the API is the sync authority.
- Dashboard is internal-only; no auth in the hackathon demo (same as 001).

## Open decisions (resolve in /speckit-clarify before planning)

1. Batch validation: all-or-nothing vs valid-subset (FR-003 / US1 scenario 3).
2. Exact metric definitions + global vs per-user dashboard (US3).
3. Unknown-FK event handling: reject vs accept-with-null (edge cases).
