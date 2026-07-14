<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0 (reconcile with docs/11 v0.2.0 + contract v0.2.0)
- Modified principles:
  - V. Privacy-Minimal Data — cost/shares reframed: schema fields exist but are
    never populated by the onboarding flow (was: "does not collect/store")
- Added guidance:
  - Technical Constraints & Scope — carved out the ONE allowed training exception
    (offline unsupervised Market Moment Detector, apps/ai-training) from the
    blanket "no model training"; noted the expanded contract surface
    (events / concern-feedback / dashboard) is feature 002
  - Development Workflow — feature specs live under docs/api/<###-feature>/
    (project convention), not specs/
- Removed sections: none
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md — generic Constitution Check gate, compatible as-is
  - ✅ .specify/templates/spec-template.md — no constitution-specific sections, compatible as-is
  - ✅ .specify/templates/tasks-template.md — test-first task ordering matches Principle IV
- Follow-up TODOs: none
-->

# Mindfolio AI Constitution

## Core Principles

### I. Contract-First API (NON-NEGOTIABLE)

`apps/api/contracts/openapi.yaml` is the single authoritative contract between
frontend and backend. The API MUST expose exactly the endpoints, field names,
enum values, and base path defined there. Neither side invents fields; any
contract change MUST be made in the YAML first and communicated before code
changes on either side.

Rationale: a two-person team developing web and API in parallel over three days
cannot afford integration drift.

### II. Deterministic Numbers, Generative Narrative

All numeric values (20-day institutional net, 7-day bullish ratio, priority
scores, any rate or ranking) MUST be computed by deterministic Python code from
source data. Amazon Bedrock is used ONLY to turn pre-computed evidence into
narrative text and structured card JSON. The LLM MUST never perform arithmetic,
derive figures, or receive numeric computation tasks via prompt or tool-use.

Rationale: reproducibility and auditability of every number shown to the user;
LLM arithmetic is neither.

### III. AI Output Guardrails

LLM output MUST be validated against the Action Card JSON schema before use;
on validation failure or Bedrock error, a fixed-template card built from the
same evidence MUST be substituted. Generated content MUST never contain buy or
sell direction, target prices, or return guarantees, and MUST never frame
community aggregate data as the user's personal emotion or anxiety. Every card
retains its source date and evidence.

Rationale: financial-context demo; a single hallucinated recommendation
invalidates the product claim.

### IV. Test-First

TDD is mandatory for API code: write the failing test, implement minimally to
pass, then refactor. Target 80%+ coverage with unit tests for computations and
services, and contract/integration tests for every endpoint against the OpenAPI
schemas. Numeric evidence values for the demo (2382 @ 2025-12-31) are pinned by
tests.

Rationale: the demo's acceptance criteria are precise numbers and states;
regressions must be caught mechanically, not by eyeballing the UI.

### V. Privacy-Minimal Data

Only `user_confirmed` relationships may be written to the portfolio; candidate
or inferred relationships MUST NOT become holdings. The onboarding flow MUST
NOT ask for or populate share counts or cost basis: `portfolio_relationships`
carries nullable `average_cost`/`shares` columns, but the one-tap flow leaves
them null. The system MUST never infer broker data, total assets, or personal
anxiety. Organizer CSVs and PDFs in `data/` are local-only and MUST never be
committed; public demos use a minimal validated subset.

Rationale: the product's core promise is minimum-sensitivity onboarding; the
data license is unconfirmed for redistribution. The columns exist so a future
opt-in flow has somewhere to write — not so this flow can.

### VI. Demo-Complete Degradation

The demo loop (insight → one-tap confirm → portfolio update) MUST complete
under every degradation: Bedrock down (fixed card copy), database down
(browser-held state), API down (prototype's built-in 2382 evidence JSON).
Failures MUST be loud at startup (fail fast on missing data files) and graceful
at runtime.

Rationale: a hackathon demo gets one shot; every dependency is allowed to fail
except the loop itself.

## Technical Constraints & Scope

- Stack: Python 3.11+ / FastAPI backend, PostgreSQL (`infra/schema/001_init.sql`),
  Amazon Bedrock for generation, CSV source data loaded at startup.
- Demo baseline date is fixed at `2025-12-31`; demo stock 2382 廣達
  (close 272, institutional_net_20d −60,265, community_bullish_ratio_7d 0.939);
  demo user LEO.
- `community_bullish_ratio_7d` counts only posts with an explicit bullish or
  bearish stance — never described as overall sentiment.
- Out of scope entirely: chat UI, free-text input, screenshot upload, RAG,
  vector databases, multi-agent frameworks, holding-prediction models, price
  prediction, buy/sell recommendations, personal anxiety scores.
- **Training exception (the only one)**: `apps/ai-training` is an OFFLINE,
  unsupervised Market Moment Detector over the organizer's daily aggregates.
  It answers "which time points are anomalous/divergent enough to surface",
  emitting `MomentSignal` JSONL that the online API reads as a ranking input.
  It MUST NOT predict holdings, anxiety, price direction, or buy/sell. The
  online API never trains during a request; if the detector is unavailable the
  API degrades to validated rules and the fixed `examples/2382-2025-12-31.json`.
  `anomaly_score` is never shown to the user as an accuracy figure.
- The contract surface beyond the core loop — interaction events
  (`/v1/events/batch`, `/v1/users/{id}/events`), concern-feedback, and the
  internal `/v1/dashboard/metrics` — is feature **002**; the core one-tap loop
  is feature **001**. Both share `infra/schema/001_init.sql`.
- Planned API layout: `apps/api/src/` with `main.py`, `routes/`, `services/`,
  `repositories/`, `models/`, `prompts/`.

## Development Workflow

- Spec-driven development via Spec Kit: specify → clarify → plan → tasks →
  analyze → implement. Feature specs live in `docs/api/<###-feature>/`
  (`.specify/feature.json` points there); decisions that shift product
  consensus propagate back into `docs/00–11`.
- Product-scope questions defer to `docs/11_COMPLETE_MVP_SPEC.md`; engineering
  practice defers to this constitution. If the two conflict on product scope,
  the MVP spec wins and this constitution is amended.
- Build order: contract runs end-to-end with fixed LEO demo data first; the CSV
  adapter comes after. No data pipeline before the loop works.
- Conventional commit format (`feat:`, `fix:`, `test:`, `docs:`, ...).
- Code review before merge; CRITICAL and HIGH findings block.

## Governance

This constitution supersedes ad-hoc practice for all work in this repository.
Amendments are made by editing this file with a semantic version bump (MAJOR:
principle removal/redefinition; MINOR: new principle or materially expanded
guidance; PATCH: clarification) and noting the change in the Sync Impact
Report comment. Every plan's Constitution Check gate MUST verify compliance
with Principles I–VI; violations require an entry in the plan's Complexity
Tracking table with justification. Runtime agent guidance lives in `CLAUDE.md`
and must stay consistent with this document.

**Version**: 1.1.0 | **Ratified**: 2026-07-14 | **Last Amended**: 2026-07-14
