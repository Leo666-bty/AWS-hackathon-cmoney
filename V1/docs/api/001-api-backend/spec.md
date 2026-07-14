# Feature Specification: Mindfolio API Backend

**Feature Directory**: `docs/api/001-api-backend`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "Mindfolio AI FastAPI backend: implement the four-endpoint API defined in apps/api/contracts/openapi.yaml (stock context, next action card, one-tap feedback, portfolio retrieval) with deterministic Python computation of all numbers, Amazon Bedrock only for narrative card generation with schema validation and fixed-template fallback, PostgreSQL persistence per infra/schema/001_init.sql, and a CSV adapter over the organizer data package. Day-1 build order: run the contract end-to-end with fixed LEO demo data before wiring the CSV adapter. Incorporate the EARS requirements draft at .kiro/specs/mindfolio-api-backend/requirements.md. Product source of truth: docs/11_COMPLETE_MVP_SPEC.md."

## Clarifications

### Session 2026-07-14

- Q: 回饋後卡片生命週期與 follow_up_card 行為？ → A: Feedback consumes the
  card (no longer eligible for next-card selection); afterwards `cards/next`
  returns 204 (the demo has a single event). **Superseded 2026-07-14 by
  contract v0.2.0**: the `follow_up_card` was removed — the feedback response
  now returns only the updated `PortfolioRelationship`. The "holding
  perspective of the same event" is rendered by the frontend from the
  portfolio, not returned inline.
- Q: 同一張卡收到第二次回饋時？ → A: Latest-wins update (HTTP 200): the
  existing feedback record and relationship are updated in place; no second
  record is created and no 409 is returned.
- Q: 7 天內無明確多空貼文時 community_bullish_ratio_7d？ → A: The contract
  field becomes nullable; null means "not computable" (never 0, 1, or a
  fabricated neutral value). Frontend hides the community block on null.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-Tap Feedback Loop (Priority: P1)

The web frontend, acting for demo user LEO, fetches the highest-priority
insight card, LEO taps one of the three relationship actions
(是我的持股 / 只是觀察 / 不相關), and the system records the confirmed
relationship so LEO's portfolio reflects it immediately. This is the product's
core closed loop: insight → one-tap confirm → portfolio update.

**Why this priority**: Without this loop there is no demo and no product claim.
Every other capability upgrades this loop; none replaces it.

**Independent Test**: With fixed demo data and a seeded database, call
"next card" → submit feedback `confirmed_holding` → fetch portfolio, and
observe the portfolio go from empty to containing 2382 as a holding. No CSV
data or AI generation required.

**Acceptance Scenarios**:

1. **Given** LEO has no confirmed relationships, **When** the frontend requests
   LEO's next card, **Then** it receives a divergence card for 2382 with title,
   summary, evidence list, and exactly three actions (`confirmed_holding`,
   `watch_only`, `irrelevant`).
2. **Given** a card is displayed, **When** feedback `confirmed_holding` is
   submitted (with `action` and `occurred_at`), **Then** a relationship
   (2382, `holding`, source `user_confirmed`) is stored and returned as the
   response body; the original card is consumed (no longer eligible).
3. **Given** a card is displayed, **When** feedback `watch_only` or
   `irrelevant` is submitted, **Then** the relationship is stored with that
   type, the original card is consumed, and 2382 does NOT appear as a holding.
4. **Given** LEO confirmed 2382 as a holding, **When** the frontend requests
   LEO's portfolio, **Then** the response contains the 2382 relationship with
   `source = user_confirmed` and a confirmation timestamp.
5. **Given** feedback was already submitted for a card, **When** feedback is
   submitted again for the same card, **Then** the system updates the existing
   feedback and relationship in place (latest wins, HTTP 200) without creating
   a second feedback record.
6. **Given** an unknown `user_id` or `card_id`, **When** feedback is submitted,
   **Then** the system responds with a not-found error carrying a `detail`
   message.
7. **Given** a feedback body whose `action` is missing/invalid or whose
   required `occurred_at` timestamp is missing/malformed, **When** it is
   submitted, **Then** the system responds with a validation error (HTTP 422)
   and stores nothing.

---

### User Story 2 - Evidence-Grounded Stock Context (Priority: P2)

The frontend requests structured context for a stock on a given date (close
price, 20-day institutional net, 7-day explicit-stance bullish ratio) to render
the individual stock page that hosts the card.

**Why this priority**: The stock page is where the card appears; the loop can
be demonstrated without it, but the demo narrative (evidence first) needs it.

**Independent Test**: Request context for 2382 as of 2025-12-31 and verify the
response carries exactly the pinned evidence values.

**Acceptance Scenarios**:

1. **Given** the demo dataset, **When** context for stock 2382 as of
   2025-12-31 is requested, **Then** the response contains close = 272,
   institutional_net_20d = −60265, community_bullish_ratio_7d = 0.939, and the
   stock name 廣達.
2. **Given** an unknown `stock_id`, **When** context is requested, **Then**
   the system responds with a not-found error carrying a `detail` message.
3. **Given** a missing or malformed `as_of` date, **When** context is
   requested, **Then** the system responds with a validation error (HTTP 422).

---

### User Story 3 - Real Computation from Organizer Data (Priority: P3)

The system computes the evidence numbers (institutional net over 20 trading
days, explicit-stance bullish ratio over 7 days, closing price) from the
organizer CSV package instead of fixed demo values, so any covered stock/date
can be served and the pinned 2382 values are reproduced from raw data.

**Why this priority**: Upgrades the loop from staged data to real data; the
demo claim "numbers are computed, not generated" depends on it.

**Independent Test**: With the CSV package present, request context for 2382
as of 2025-12-31 and verify computed values equal the pinned evidence values.

**Acceptance Scenarios**:

1. **Given** the CSV package is present, **When** the service starts, **Then**
   data is loaded once and held in memory for the process lifetime.
2. **Given** a required CSV file is missing, **When** the service starts,
   **Then** startup fails immediately with a message naming the missing file
   (no silent empty responses).
3. **Given** loaded CSV data, **When** context for 2382 @ 2025-12-31 is
   computed, **Then** the computed values match the pinned evidence values
   exactly.

---

### User Story 4 - AI-Narrated Cards with Fallback (Priority: P4)

Card title, summary, and evidence phrasing are generated by the AI service
from pre-computed evidence, validated against the card schema, and silently
replaced by a fixed-template card when generation fails, so the demo never
blocks on the AI dependency.

**Why this priority**: Generative phrasing is the "Generative Action Card"
value-add, but the fixed template already demos the loop; this is an upgrade
with a mandatory safety net.

**Independent Test**: Run the loop once with AI enabled and once with AI
unreachable; both must return schema-valid cards carrying identical evidence
values.

**Acceptance Scenarios**:

1. **Given** the AI service responds, **When** a card is generated, **Then**
   the output is validated against the card schema before being returned.
2. **Given** the AI response fails schema validation or the service is
   unreachable, **When** a card is requested, **Then** a fixed-template card
   with the same evidence values is returned and the loop completes.
3. **Given** any generated card, **Then** its text contains no buy/sell
   direction, no target price, no return guarantee, and never frames community
   aggregates as the user's personal emotion.

---

### User Story 5 - Demo Operability (Priority: P5)

A demo presenter can verify the service is alive and reset LEO's state
(relationships, feedback, and any generated cards) between rehearsals so the
demo is repeatable from its initial state.

**Why this priority**: Pure operational convenience; the demo can technically
run once without it, but rehearsals and the live pitch need repeatability.

**Independent Test**: Complete the loop, invoke reset, verify LEO's portfolio
is empty and the same card is served again.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** the health check is invoked,
   **Then** it reports healthy.
2. **Given** LEO has confirmed relationships, feedback, and served cards,
   **When** reset is invoked, **Then** all three are cleared and the demo
   replays from its initial state (the seeded card is eligible again).

---

### Edge Cases

- Duplicate feedback for the same card (unique per card+user) — second attempt
  updates the existing record in place, latest wins (see US1 scenario 5).
- Feedback changing an existing relationship (e.g., `watch_only` on a stock
  already confirmed as `holding`) — latest confirmation wins; the relationship
  is updated, not duplicated.
- No eligible cards remain for the user — the "next card" endpoint returns
  **HTTP 204 with no body** (decided 2026-07-14; the OpenAPI contract's 204
  response documents it; frontend branches on status code).
- Database unavailable at runtime — respond with a service-unavailable error
  (HTTP 503 + `detail`), never a hang or a stack trace; the frontend falls
  back to browser-held state per the degradation plan.
- `as_of` date with insufficient history (fewer than 20 trading days / 7 days
  of community data) — compute over the available window and stay
  deterministic; never fabricate values.
- Stock exists in one CSV source but not another (e.g., price present, no
  community posts) — context is served with the computable fields; ratio over
  zero explicit-stance posts is undefined and is returned as null (contract
  field is nullable; decided 2026-07-14), never as 0, 1, or a fabricated
  neutral value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: This feature (001) MUST implement its six endpoints from the
  OpenAPI contract (v0.2.0) — stock context, next card, card feedback,
  portfolio, `GET /health`, `POST /v1/users/{user_id}/reset` — with matching
  methods, paths, parameters, field names, and enum values; no invented or
  renamed fields. The contract also defines the events / concern-feedback /
  dashboard endpoints, which belong to feature 002 and are out of scope here.
- **FR-002**: All numeric values (closing price, institutional_net_20d,
  community_bullish_ratio_7d, priority scores) MUST be produced by
  deterministic computation; the AI service MUST never perform or be asked to
  perform arithmetic.
- **FR-003**: `institutional_net_20d` MUST be the sum of institutional
  buy/sell volumes over the 20 **trading** days ending on `as_of`;
  `community_bullish_ratio_7d` MUST be bullish ÷ (bullish + bearish) counting
  only posts with an explicit stance over the 7 **calendar** days ending on
  `as_of`. The context response also carries the raw counts
  (`community_bullish_count_7d`, `community_bearish_count_7d`) and the
  additional evidence fields in FR-003a.
- **FR-003a**: The StockContext response (v0.2.0) MUST include, alongside the
  three pinned metrics: `annual_return`, `institutional_net_1d`,
  `institutional_holding_ratio`, `dividend_yield`, the two community counts,
  and a `demo_news` array. Every one of these numbers MUST be computed
  deterministically (Principle II); `demo_news` items MUST carry
  `is_demo = true` and a `MVP Demo Feed` source until an authorized news
  source is wired in.
- **FR-004**: The next-card selection MUST rank candidates by
  `relevance × impact × novelty − interruption_cost` using only pre-computed
  metrics, and MUST lower the priority of cards similar to those the user
  marked `irrelevant`.
- **FR-005**: Feedback MUST persist a relationship with source
  `user_confirmed` mapping actions to relationship types (`confirmed_holding`
  → `holding`, `watch_only` → `watch_only`, `irrelevant` → `irrelevant`);
  only user-confirmed relationships may ever be stored — candidate or inferred
  relationships MUST NOT be written.
- **FR-006**: The portfolio endpoint MUST return only user-confirmed
  relationships, as an empty list (HTTP 200) when none exist, each record
  carrying user, stock, relationship type, importance, source, and
  confirmation timestamp.
- **FR-007**: Unknown `stock_id`, `user_id`, or `card_id` MUST yield a
  not-found error (HTTP 404) with a `detail` message; missing or malformed
  input (dates, enum values, request bodies) MUST yield a validation error
  (HTTP 422) with structured details; neither may store anything.
- **FR-008**: AI-generated card output MUST be schema-validated before use;
  on validation failure or AI-service error, a fixed-template card built from
  the same evidence MUST be substituted so the loop completes.
- **FR-009**: Generated card content MUST never contain buy/sell direction,
  target prices, or return guarantees, and MUST never describe community
  aggregate data as the user's personal emotion; every card MUST carry its
  evidence and source date.
- **FR-010**: The system MUST load the organizer CSV package once at startup,
  hold it in memory, and fail fast at startup with a message naming any
  missing/unreadable required file.
- **FR-011**: The system MUST serve correct results for the seeded demo state
  (user LEO, stock 2382) and reproduce the pinned evidence values for 2382 as
  of 2025-12-31: close = 272, institutional_net_20d = −60265,
  community_bullish_ratio_7d = 0.939.
- **FR-012**: The reset endpoint MUST clear the target user's relationships,
  feedback, and generated cards, restoring the demo's initial state for that
  user.
- **FR-013**: The system MUST answer a liveness/health question distinguishing
  "service up" from "service down" for demo operations.
- **FR-014**: The system MUST accept requests from the web frontend served on
  a different origin (browser cross-origin access).
- **FR-015**: Duplicate feedback for the same card and user MUST NOT create a
  second feedback record; repeated confirmations update the existing
  relationship rather than duplicating it.
- **FR-016**: A card that has received feedback MUST be excluded from
  next-card selection (feedback consumes the card). The feedback response body
  is the updated `PortfolioRelationship` only — contract v0.2.0 removed the
  inline `follow_up_card`.
- **FR-017**: The feedback request body MUST require both `action` and an
  `occurred_at` timestamp; `occurred_at` is persisted with the feedback record.
- **FR-018**: The single demo card is seeded in `infra/schema/001_init.sql`
  (`id = "signal-divergence-2382"`, TEXT). `cards/next` serves the seeded card
  when eligible; the Card Generator (US4) rephrases its narrative via Bedrock
  at serve time, falling back to the seeded title/summary. The API MUST NOT
  invent a second demo card.

### Key Entities

- **User**: A demo identity (LEO) that owns relationships, cards, and
  feedback; pre-seeded, no self-registration.
- **Stock**: A listed security (id, name, industry); 2382 廣達 pre-seeded.
- **Stock Context**: Point-in-time evidence for a stock (as-of date, close,
  institutional net 1d/20d, holding ratio, dividend yield, community
  bullish/bearish counts and ratio, `demo_news`); all computed, never stored
  as user data.
- **Action Card**: A structured insight (TEXT id, type, stock, title, summary,
  evidence list, three actions, source date); the demo card is seeded, served
  by cards/next, persisted with its shown/created timestamps.
- **Portfolio Relationship**: The user-confirmed link between a user and a
  stock (`holding` / `watch_only` / `irrelevant`, importance, source
  `user_confirmed`, confirmed-at); one per user+stock, updated in place.
  Nullable `average_cost`/`shares` columns exist but stay null in this flow.
- **Card Feedback**: The one-tap action a user took on a card, with the
  client-supplied `occurred_at`; at most one per card+user (latest wins).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full demo loop (fetch card → one tap → portfolio updated)
  completes through the API alone — LEO's portfolio goes from 0 to 1 holdings
  with no manual data edits.
- **SC-002**: Context for 2382 as of 2025-12-31 returns exactly the pinned
  evidence values (272 / −60265 / 0.939) — byte-identical numbers on every
  call.
- **SC-003**: With the AI service disabled or failing, 100% of card requests
  still return a schema-valid card and the demo loop completes.
- **SC-004**: Every 001 endpoint response validates against the OpenAPI
  contract schemas in automated contract tests (6/6 of this feature's
  endpoints covered).
- **SC-005**: After reset, a rerun of the demo produces the same initial card
  and the same end state, at least 3 consecutive times in rehearsal.
- **SC-006**: No malformed request (bad date, bad enum, unknown ids) produces
  an unstructured error or a stored side effect — 100% of negative tests
  return structured 404/422/503 errors.
- **SC-007**: `watch_only` and `irrelevant` feedback never increase holdings
  count — 0 occurrences across all tests.

## Assumptions

- Single pre-seeded demo user (LEO); authentication/authorization is out of
  scope for the hackathon demo.
- The demo card is seeded in the schema (`signal-divergence-2382`); `cards/next`
  serves it and Bedrock rephrases its narrative at serve time (US4). The demo
  has effectively one divergence card for 2382; no batch pre-generation.
- Interaction events, concern-feedback, and dashboard metrics are feature 002;
  001 assumes their tables exist (same schema file) but implements none of
  their endpoints.
- The portfolio endpoint returns all user-confirmed relationship types
  (holding / watch_only / irrelevant); the frontend filters for display
  (holdings count uses `holding` only).
- The organizer CSV package is present locally under
  `data/Delivery_Hackathon_DataPackage_20260624/`; it is never committed.
- Demo baseline date 2025-12-31; dates outside CSV coverage are served
  best-effort deterministically (see edge cases), demo flows always use the
  baseline date.
- PostgreSQL schema `infra/schema/001_init.sql` is the storage model; the
  Kiro draft at `.kiro/specs/mindfolio-api-backend/requirements.md` is
  superseded by this spec once accepted.
- Product-scope conflicts defer to `docs/11_COMPLETE_MVP_SPEC.md`.
