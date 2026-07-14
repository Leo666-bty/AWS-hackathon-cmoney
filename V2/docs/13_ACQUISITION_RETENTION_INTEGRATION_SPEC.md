# Mindfolio Acquisition-to-Retention Integration Requirements Spec

**Document ID**: `MF-RET-001`
**Created**: 2026-07-14
**Status**: Draft — requirements baseline, implementation not started
**Primary implementation root**: `V2/`
**Reference source**: archived `V1/` product concepts and contracts
**Depends on**: `12_V2_END_TO_END_SPEC.md`, `api/003-confirmed-holdings/spec.md`

## 1. Decision and purpose

Mindfolio is one product with two consecutive lifecycle stages:

```text
Time Machine acquisition experience (current V2)
→ anonymous reconstruction and immediate value
→ registration / report claim / explicit holding consent
→ Portfolio Radar retention experience (selected V1 capabilities)
→ recurring evidence, feedback and return visits
```

The current `V2/` directory remains the only active implementation root. This
spec does **not** authorize reviving `V1/` as a second application, copying its
runtime wholesale, or maintaining two API versions. V1 is a product and domain
reference from which selected retention requirements are re-specified for the
V2 React + FastAPI architecture.

This document is the requirements baseline for later SDD work. Each delivery
slice must produce its own `spec.md`, `plan.md`, `tasks.md`, OpenAPI changes,
schema migration and acceptance trace before implementation begins.

## 2. Problem statement

The Time Machine currently proves anonymous acquisition:

- a stranger can choose five familiar stocks;
- FastAPI validates month and price inputs;
- the reconstruction engine returns portfolio results, confidence and persona;
- the user can share an anonymous personality card;
- explicitly marked holdings can be saved with consent.

If the journey ends at the result page, Mindfolio remains a one-time campaign.
The system still lacks a durable reason to register, return and progressively
improve portfolio data. The retention stage must convert a claimed Time Machine
report and confirmed holdings into a recurring Portfolio Radar without weakening
the acquisition flow or treating inferred interest as a real holding.

## 3. Product boundaries and terminology

| Term | Meaning in the active V2 product |
|---|---|
| Time Machine | Anonymous acquisition surface: five-stock reconstruction, persona, report and share card |
| Member Activation | The explicit transition in which a user authenticates or creates an account and claims an anonymous report |
| Portfolio Radar | Member retention surface: confirmed holdings, prioritized market moments and recurring review |
| Reconstruction candidate | A stock selected in the quiz; it is not a holding by itself |
| Confirmed holding | A holding relationship explicitly approved by the user and revalidated by the backend |
| Market Moment | A deterministic or model-assisted evidence bundle that may deserve attention |
| Action Card | A member-facing explanation generated from a verified Market Moment DTO |
| Concern preference | Explicit reminder preference such as routine or mute; never an inferred psychological state |

External product and pitch language should use **Time Machine** and
**Portfolio Radar**. `V1` and `V2` remain repository-history labels only.

## 4. Goals and success criteria

### 4.1 Goals

1. Preserve the low-friction anonymous V2 acquisition experience.
2. Give the result-page registration CTA a concrete member value exchange.
3. Allow a member to claim an immutable 2025 report across devices.
4. Convert only explicitly approved candidates into confirmed holdings.
5. Use confirmed holdings to select evidence-grounded Action Cards.
6. Provide a compact member home that supports recurring visits.
7. Capture explicit feedback and interaction events for future ranking models.
8. Reuse V1 product lessons without creating a parallel V1 runtime.

### 4.2 Product success metrics

| Stage | Primary metric | Supporting metrics |
|---|---|---|
| Acquisition | reconstruction completion rate | start rate, time-to-result, validation correction rate |
| Referral | anonymous card share rate | share click, download, referred sessions |
| Activation | claimed-report rate | registration CTA rate, claim completion rate |
| Portfolio activation | verified holding activation | consent rate, confirmed holdings per activated member |
| Retention | D7 / D30 Portfolio Radar return | Action Card open, evidence open, weekly review open |
| Data quality | explicit relationship coverage | correction, removal, mute and stale-holding review rates |

Demo sessions prove instrumentation and the end-to-end state transition only;
they must not be presented as achieved market conversion rates.

## 5. End-to-end user journey

### 5.1 Anonymous acquisition

```text
Landing
→ choose five stocks
→ reconstruct five trades
→ receive immutable 2025 report
→ view persona card, radar and AI narrative
→ share anonymously or choose "Save report and open Portfolio Radar"
```

No login is required before the user receives the core result.

### 5.2 Member activation

```text
Result CTA
→ authenticate / create account
→ claim anonymous reconstruction report
→ review "still holding" candidates
→ provide explicit consent
→ backend revalidates candidates
→ create confirmed holdings
→ enter Portfolio Radar
```

Authentication failure or cancellation must not delete the anonymous report or
falsely mark it as claimed.

### 5.3 Retention loop

```text
Member opens Portfolio Radar
→ sees current portfolio snapshot
→ opens highest-priority Action Card
→ reviews deterministic evidence and source date
→ gives relationship / reminder feedback
→ system records an idempotent event
→ future cards and weekly review reflect explicit preferences
```

Historical 2025 reconstruction and current market context are separate data
products. Live context must never silently rewrite the immutable Time Machine
report.

## 6. Information architecture

### 6.1 Required surfaces

| Route / surface | Audience | Responsibility | Delivery priority |
|---|---|---|---|
| `/result` | anonymous | Existing report, share, member-value preview and activation CTA | P0 existing + copy update |
| `/activate` | anonymous → member | Authentication handoff, report claim and holding-consent review | P0 |
| `/app` | member | Portfolio Radar home: fingerprint, portfolio, priority card and weekly review | P0 |
| `/app/portfolio` | member | Confirmed relationships, completeness, correction and removal | P1 |
| `/app/stocks/:stockId` | member | Evidence detail for a confirmed or watch-only stock | P1 |
| Internal funnel view | internal demo / operator | Verify events, activation and holding counts | P2 |

The hackathon P0 may implement `/app` as one route with expandable sections.
It does not require a complete multi-page member application.

### 6.2 Portfolio Radar home requirements

The P0 member home must contain four modules:

1. **Portfolio Fingerprint** — claimed persona, four-axis score, report date and
   reconstruction confidence.
2. **Confirmed Portfolio** — confirmed holdings only, with source and last
   confirmation time; missing share count and cost must remain visibly unknown.
3. **Priority Action Card** — one evidence-grounded market moment for a
   confirmed holding, with source date, evidence and fallback state.
4. **Weekly Review preview** — a compact summary of portfolio events and the
   next value exchange; it may use fixture/current-snapshot data in the demo if
   clearly labelled.

## 7. Functional requirements

### 7.1 Activation and report claim

- **FR-ACT-001**: The system MUST issue an opaque reconstruction/report ID when
  an anonymous reconstruction completes; client-computed persona or result
  values MUST NOT be sufficient to create a claim.
- **FR-ACT-002**: A successful member activation MUST bind the report ID to the
  authenticated member on the backend and MUST be idempotent.
- **FR-ACT-003**: A report already claimed by a different member MUST NOT be
  claimable and MUST return a conflict without exposing the other identity.
- **FR-ACT-004**: The existing hard-coded `LEO` identity is demo-only. The
  retention SDD MUST replace client-supplied arbitrary user IDs with an
  authenticated server identity or an explicit demo identity adapter.
- **FR-ACT-005**: Claiming a report MUST NOT automatically create holdings.
  Holding consent is a distinct, explicit action.
- **FR-ACT-006**: The claimed 2025 reconstruction result MUST remain immutable;
  later market data may add context but MUST NOT alter its historical numbers.
- **FR-ACT-007**: Activation cancellation or provider failure MUST leave the
  anonymous report readable for its configured lifetime and MUST NOT record a
  successful activation event.

### 7.2 Confirmed portfolio

- **FR-POR-001**: Only candidates marked `relation=holding`, explicitly selected
  during consent and successfully revalidated by FastAPI may become confirmed
  holdings.
- **FR-POR-002**: Search, page view, share, reconstruction selection and model
  inference MUST NOT create a confirmed holding.
- **FR-POR-003**: Each relationship MUST record member ID, stock ID, type,
  `source=user_confirmed`, source report ID, confirmation time and latest review
  time.
- **FR-POR-004**: Share count, average cost and broker MUST remain nullable and
  optional; the first activation MUST NOT require them.
- **FR-POR-005**: Members MUST be able to correct a relationship to `watch_only`
  or remove it. The latest explicit response wins and the prior state remains
  auditable.
- **FR-POR-006**: Portfolio UI MUST distinguish confirmed, watch-only and stale
  relationships and MUST never label candidates as holdings.

### 7.3 Market Moment and Action Card

- **FR-MOM-001**: Action Card candidates MUST be created from verified market,
  institutional, valuation or community aggregate evidence with an `as_of`
  date and source keys.
- **FR-MOM-002**: Candidate ranking MUST be deterministic and inspectable before
  AI narration. The baseline is `relevance × impact × novelty −
  interruption_cost`.
- **FR-MOM-003**: Confirmed holdings may increase relevance; `watch_only`,
  `irrelevant` and `mute` feedback MUST change priority according to documented
  rules.
- **FR-MOM-004**: Market Regime or anomaly-model results may enrich a moment,
  but MUST include model version, feature version and evidence hints.
- **FR-MOM-005**: Raw anomaly scores MUST NOT be presented as prediction
  accuracy or a buy/sell signal. UI uses understandable levels and evidence.
- **FR-MOM-006**: If model artifacts are unavailable or incompatible, the
  service MUST fall back to deterministic evidence without blocking the member
  home.
- **FR-MOM-007**: P0 requires at most one priority card on the member home; a
  full feed and notification scheduler are not required.

### 7.4 Bedrock narrative

- **FR-AI-001**: Bedrock MUST receive only a verified DTO; it MUST NOT calculate
  returns, assign holdings, alter model classifications or query credentials.
- **FR-AI-002**: AI output MUST pass a typed schema and prohibited-language
  checks before display.
- **FR-AI-003**: Provider timeout, refusal, invalid schema or unavailable AWS
  credentials MUST result in a deterministic fallback card with identical
  numeric evidence.
- **FR-AI-004**: Output MUST NOT contain buy/sell direction, target price,
  return guarantee, psychological diagnosis or claims that community aggregates
  represent the member's personal emotion.
- **FR-AI-005**: The UI MUST expose evidence date and a fallback/generated
  provenance state without presenting the LLM as the source of financial facts.

### 7.5 Feedback, preferences and events

- **FR-EVT-001**: The system MUST capture activation, report claim, portfolio
  view, card impression, evidence open, relationship feedback, reminder
  preference and holding removal as typed events.
- **FR-EVT-002**: Client events MUST use a stable event ID and batch ingest MUST
  be idempotent; retries MUST NOT increase metrics.
- **FR-EVT-003**: Events are behavioral signals, not holding truth. Only explicit
  relationship feedback may update portfolio relationships.
- **FR-EVT-004**: Reminder feedback such as `routine` or `mute` MUST be described
  as a content preference, not an inferred emotional condition.
- **FR-EVT-005**: A queued client event becomes synced only after API acceptance;
  offline or API failure MUST remain visible to the client retry mechanism.
- **FR-EVT-006**: Future supervised ranking may use explicit labels, but viewed
  or ignored content MUST remain unlabeled unless the label policy says
  otherwise.

## 8. Proposed service and API boundaries

The exact OpenAPI surface is decided in each SDD feature. The following is the
required capability map, not yet a frozen HTTP contract.

| Capability | Candidate endpoint | Authority |
|---|---|---|
| Create durable anonymous report | `POST /api/v2/reports` | Reconstruction service |
| Claim report | `POST /api/v2/reports/{report_id}/claim` | Activation service + authenticated identity |
| Read claimed report | `GET /api/v2/me/reports/{report_id}` | Report repository |
| Confirm report holdings | `POST /api/v2/reports/{report_id}/confirmed-holdings` | Holding service |
| Member home aggregate | `GET /api/v2/me/dashboard` | Portfolio Radar query service |
| List relationships | `GET /api/v2/me/portfolio` | Portfolio repository |
| Get priority Action Card | `GET /api/v2/me/action-cards/next` | Moment ranking service |
| Submit card feedback | `POST /api/v2/me/action-cards/{card_id}/feedback` | Feedback service |
| Submit reminder preference | `POST /api/v2/me/reminder-preferences` | Preference service |
| Batch events | `POST /api/v2/events/batch` | Event service |

`/me` means the server derives identity from authentication. The current
`/users/{user_id}` and request-body `user_id` patterns must not become the
production member authorization boundary.

## 9. Data model requirements

### 9.1 Required entities

| Entity | Required purpose |
|---|---|
| Reconstruction Report | Immutable verified result, anonymous owner token, claim state and expiry |
| Report Claim | Idempotent report-to-member binding with claimed time |
| Portfolio Relationship | Confirmed/watch-only relationship, source, status and review timestamps |
| Market Moment | Deterministic/model evidence, source date, feature/model version and severity |
| Action Card | Moment reference, member context, narrative provenance and served state |
| Relationship Feedback | Explicit latest-wins response plus audit history |
| Reminder Preference | Routine/mute or later frequency values; never emotion |
| Interaction Event | Idempotent telemetry with occurred and received timestamps |

### 9.2 State transitions

```text
anonymous report:
created → completed_unclaimed → claimed
                         ↘ expired

holding candidate:
candidate → consented → backend_revalidated → confirmed
                                      ↘ rejected

portfolio relationship:
confirmed ↔ watch_only → removed
     ↘ stale_review_required
```

Every transition that changes identity or holding truth must be server-side,
idempotent where retry is expected, and auditable.

### 9.3 Data minimization

- The immutable report may store verified reconstruction outputs needed for
  replay, but exact trade input persistence requires explicit retention policy.
- Confirmed holdings do not require price, share count, broker or total assets.
- Public share cards never contain stock IDs, prices, report IDs or returns by
  default.
- Model-training exports must replace direct identity with scoped pseudonymous
  identifiers and document consent and label origin.
- A later production phase must provide report/relationship deletion, export
  and consent withdrawal.

## 10. Non-functional requirements

- **NFR-001 — Security**: Member endpoints must derive identity server-side and
  prevent cross-member report or portfolio access.
- **NFR-002 — Reliability**: Bedrock/model failure must not block deterministic
  portfolio and evidence views.
- **NFR-003 — Reproducibility**: Historical reports and model artifacts carry
  data range, feature version, model version and generation time.
- **NFR-004 — Performance**: P0 member-home aggregate target is p95 under 1.5 s
  excluding an optional asynchronous AI refresh; cached/fallback narrative may
  render first.
- **NFR-005 — Accessibility**: Cards, scores and charts require textual
  equivalents and keyboard-operable actions.
- **NFR-006 — Observability**: Activation, claim, card selection, AI fallback
  and persistence failures require structured logs without sensitive inputs.
- **NFR-007 — Privacy**: Logs and analytics must not record exact trade prices,
  authentication tokens or full generated prompts containing personal data.
- **NFR-008 — Compatibility**: The retention implementation remains inside the
  existing React, FastAPI, PostgreSQL and shared Python package boundaries.

## 11. Acceptance scenarios

### AS-01 — Anonymous value remains first

**Given** a stranger has not authenticated, **when** all five trades pass
validation, **then** the complete personality report and share card are shown
before any registration is required.

### AS-02 — Claim does not imply holding consent

**Given** a user claims a report, **when** holding consent has not been
submitted, **then** the member account owns the report but has no new confirmed
holdings.

### AS-03 — Explicit handoff creates portfolio value

**Given** a claimed report contains three `holding` candidates, **when** the
member selects two and consents, **then** FastAPI revalidates the report and
creates exactly two confirmed holdings with `source=user_confirmed`.

### AS-04 — Member home is personalized from confirmed truth

**Given** a member has two confirmed holdings, **when** `/app` opens, **then**
the portfolio module lists those two relationships and the priority card is
selected only from eligible evidence; an unconfirmed quiz selection is not
labelled as a holding.

### AS-05 — AI failure is fail-soft

**Given** Bedrock times out and the model artifact is unavailable, **when** the
member opens Portfolio Radar, **then** deterministic portfolio/evidence content
and a fixed-template Action Card still render with no fabricated values.

### AS-06 — Feedback changes future interruption, not history

**Given** a member marks an Action Card `mute`, **when** the next card is
selected, **then** interruption cost reflects the preference, while the claimed
2025 report and confirmed relationship history remain unchanged.

### AS-07 — Identity isolation

**Given** report A belongs to member A, **when** member B requests or claims it,
**then** the API rejects the operation without exposing member A's identity or
report content.

### AS-08 — Instrumentation is retry-safe

**Given** the same event batch is submitted twice after a network retry,
**when** the dashboard metrics are recomputed, **then** every event is counted
once.

## 12. Delivery slices for later SDD

The recommended feature sequence extends the existing V2 API SDD numbering:

| Feature | Proposed directory | Scope | Depends on |
|---|---|---|---|
| 004 | `docs/api/004-member-activation` | durable report, claim, identity adapter, consent handoff | existing 002/003 |
| 005 | `docs/api/005-portfolio-radar-home` | `/app` aggregate, claimed fingerprint and confirmed portfolio | 004 |
| 006 | `docs/api/006-market-moments-action-cards` | V1 Moment Engine concepts, ranking, Bedrock narrative and fallback | 005 + AI artifact |
| 007 | `docs/api/007-events-preferences` | idempotent events, relationship feedback, reminder preference, metrics | 004–006 |

Each SDD feature must include:

1. clarified user stories and failure cases;
2. frozen OpenAPI request/response schemas;
3. database migration and ownership rules;
4. frontend route/component and loading/empty/error states;
5. service/repository/AI boundaries;
6. unit, integration, contract and acceptance tests;
7. requirement-to-test traceability;
8. explicit rollback and demo fallback behavior.

Implementation must not begin merely from this umbrella document. Feature 004
is the first alignment gate because identity, report ownership and consent affect
all later retention work.

## 13. Scope by delivery horizon

### Hackathon P0

- Result-page value preview and activation CTA.
- Explicit demo authentication or identity adapter.
- Claim one reconstruction report.
- Confirm selected holding candidates after backend revalidation.
- One `/app` Portfolio Radar page with four required modules.
- One evidence-grounded Action Card with deterministic fallback.
- Minimum activation, portfolio-view and card-open events.

### P1 after the hackathon

- Production authentication integration.
- Portfolio relationship correction/removal and stale review.
- Stock evidence detail route.
- Event outbox/retry and internal funnel metrics.
- Scheduled weekly review and reminder preferences.
- Real-time/current-data adapter isolated from 2025 reconstruction.

### Explicit non-goals for this spec baseline

- Reviving or deploying the archived V1 application.
- Maintaining separate V1 and V2 databases or APIs.
- Free-form investment chatbot.
- Brokerage connection, mandatory share count/cost or total-asset upload.
- Price prediction, buy/sell advice, target prices or return guarantees.
- Full notification infrastructure in the first slice.
- Training a holding-prediction or emotion model without valid labels.
- A large multi-page dashboard before the one-page retention loop is proven.

## 14. Reuse and migration guidance

V1 may be reused as a requirements and interaction reference for:

- Market Moment evidence contracts;
- deterministic card ranking;
- Action Card schema and fallback behavior;
- explicit relationship and reminder feedback;
- confirmed Portfolio and event-pipeline semantics.

Before any code is reused, SDD planning must verify compatibility with the
current V2 domain models, `/api/v2` contracts, React state, PostgreSQL schema and
privacy rules. V1 route names, demo identity, database schema and generated
artifacts are not automatically authoritative.

## 15. Open decisions for SDD clarification

1. Which authentication mechanism is used in the hackathon demo and which is
   the production target?
2. How long does an anonymous completed report remain claimable?
3. Which exact reconstruction inputs are persisted for report replay, and for
   how long?
4. Does P0 create a report before or during `/reconstructions/complete`?
5. Is holding consent part of activation or the first action on `/app`?
6. Which current market dataset can legally and technically power the first
   Portfolio Radar card?
7. Is Bedrock narration synchronous, cached or generated asynchronously?
8. What makes a holding relationship stale and when is reconfirmation required?
9. Which event definitions and funnel metrics are required for judging versus
   production analytics?
10. Which P0 sections use clearly labelled fixtures when current data is absent?

## 16. Decision log and development record

| Date | Decision | Consequence |
|---|---|---|
| 2026-07-14 | V2 remains the active project root | All new runtime code and SDD artifacts live under `V2/` |
| 2026-07-14 | Time Machine owns acquisition; Portfolio Radar owns retention | V1 and V2 concepts become consecutive product stages, not competing versions |
| 2026-07-14 | V1 is an archived reference, not a second runtime | Selected capabilities are re-specified against React + FastAPI + PostgreSQL |
| 2026-07-14 | This document is requirements-only | No retention implementation is considered authorized or complete |

## 17. Definition of requirements-ready

This umbrella requirement is ready to enter feature-level SDD when:

- product owner confirms the Time Machine → Portfolio Radar handoff;
- P0 versus P1 scope is accepted;
- identity and report-claim strategy is selected;
- current-data source and demo-fixture policy are selected;
- feature 004 receives its own spec with no unresolved ownership or consent
  ambiguity.

Until then, current V2 acquisition behavior remains the implementation source
of truth and V1 remains read-only reference material.
