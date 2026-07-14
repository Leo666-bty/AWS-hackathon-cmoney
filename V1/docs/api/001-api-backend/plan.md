# Implementation Plan: Mindfolio API Backend

**Branch**: `001-api-backend` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `docs/api/001-api-backend/spec.md`

## Summary

Implement the Mindfolio AI FastAPI backend: six contract endpoints (four
business + health + reset) over PostgreSQL, with deterministic Python
computation of all evidence numbers, a startup-loaded CSV adapter over the
organizer package, and Bedrock-generated action cards that are
schema-validated with a fixed-template fallback. Build order: contract runs
end-to-end on fixed LEO demo data first (US1+US2), then the CSV adapter
(US3), then Bedrock generation (US4), then demo operability (US5).

## Technical Context

**Language/Version**: Python 3.11+ (managed by uv)

**Primary Dependencies**: FastAPI, Pydantic v2, pydantic-settings,
psycopg[binary] + psycopg_pool, boto3 (bedrock-runtime), PyYAML +
jsonschema (contract tests)

**Storage**: PostgreSQL (`infra/schema/001_init.sql`, no new migrations);
organizer CSVs loaded read-only into memory at startup

**Testing**: pytest + FastAPI TestClient; unit / integration / contract
layout; coverage target 80%+ (`uv run pytest --cov=src`)

**Target Platform**: local macOS for development/demo; AWS (App Runner or
Lambda+API Gateway) as stretch deployment per docs/05

**Project Type**: web-service (backend of a web app; frontend is a separate
app consuming the contract)

**Performance Goals**: demo-scale — single user, interactive latency;
CSV load at startup < 5 s; no formal throughput target (deferred by
clarify coverage decision)

**Constraints**: contract-first (openapi.yaml **v0.2.0**); LLM never computes
numbers; Bedrock failure must not break the loop (`BEDROCK_ENABLED=false` kill
switch); CSVs never committed; fixed demo baseline 2025-12-31 / stock 2382 /
user LEO. v0.2.0 specifics: the demo card is **seeded** (`action_cards.id`
TEXT); feedback body requires `occurred_at` and the response is the
`PortfolioRelationship` only (no `follow_up_card`); StockContext carries the
expanded evidence set + `demo_news`. `apps/ai-training` is offline and out of
this feature's scope (read-only `MomentSignal` input, deferred).

**Scale/Scope**: 6 endpoints (of 10 in the contract; the other 4 are feature
002), 5 core tables used (schema has 8), 3 CSV sources, ~72k–106k rows per
CSV, one seeded demo card

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Contract-First | All endpoints/fields from openapi.yaml; ops endpoints added to the contract before planning; contract tests validate against the YAML itself | ✅ PASS |
| II. Deterministic Numbers | All algorithms defined in research.md R5 and verified against raw CSVs; Bedrock receives pre-computed evidence only | ✅ PASS |
| III. AI Guardrails | CardDraft Pydantic validation + guardrail wordlist check + fixed-template fallback (research.md R6, contracts/README.md) | ✅ PASS |
| IV. Test-First | tasks.md must order tests before implementation per story; pinned-value, loop, fallback, and negative tests specified in quickstart.md | ✅ PASS |
| V. Privacy-Minimal | Only `user_confirmed` writes (DB CHECK + repository code); no share counts/cost basis anywhere; CSVs stay local | ✅ PASS |
| VI. Demo Degradation | `BEDROCK_ENABLED` kill switch; 503 on DB loss; startup fail-fast on missing CSVs | ✅ PASS |

**Post-Phase-1 re-check (2026-07-14)**: no design element violates a
principle; no Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
docs/api/001-api-backend/
├── plan.md              # This file
├── spec.md              # Feature spec (clarified 2026-07-14)
├── research.md          # Phase 0: decisions R1–R8 (verified algorithms)
├── data-model.md        # Phase 1: entities, lifecycles, validation rules
├── quickstart.md        # Phase 1: end-to-end validation guide
├── contracts/README.md  # Phase 1: pointer to openapi.yaml + Bedrock draft schema
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created by plan)
```

### Source Code (repository root)

```text
apps/api/
├── pyproject.toml            # uv-managed; deps + pytest config
├── uv.lock
├── .env.example              # DATABASE_URL, BEDROCK_MODEL_ID, AWS_REGION,
│                             # DATA_DIR, CORS_ORIGINS, BEDROCK_ENABLED
├── contracts/
│   └── openapi.yaml          # existing — source of truth (do not fork)
├── src/
│   ├── main.py               # app factory, lifespan (CSV load, pool), CORS
│   ├── config.py             # pydantic-settings
│   ├── routes/
│   │   ├── stocks.py         # GET context
│   │   ├── cards.py          # GET next, POST feedback
│   │   ├── portfolio.py      # GET portfolio
│   │   └── ops.py            # GET /health, POST reset
│   ├── services/
│   │   ├── context_builder.py    # merges CSV metrics into StockContext
│   │   ├── moment_engine.py      # scoring + eligibility (feedback consumes)
│   │   ├── card_generator.py     # Bedrock call + validation + fallback
│   │   └── portfolio_service.py  # upserts, reset
│   ├── repositories/
│   │   ├── db.py             # pool, transaction helper
│   │   ├── csv_adapter.py    # startup load, indexes, derived metrics
│   │   ├── cards_repo.py
│   │   ├── feedback_repo.py
│   │   └── portfolio_repo.py
│   ├── models/
│   │   ├── api.py            # contract-mirroring Pydantic models
│   │   └── card_draft.py     # internal Bedrock output schema
│   └── prompts/
│       └── card_prompt.py    # evidence → prompt template (no numbers computed)
└── tests/
    ├── conftest.py           # test DB, fixed demo-data fixtures, fake Bedrock
    ├── unit/                 # metrics math, moment engine, card fallback
    ├── integration/          # endpoint flows against test DB
    └── contract/             # responses vs openapi.yaml components.schemas
```

**Structure Decision**: single backend package under `apps/api/` matching
`apps/api/src/README.md` (main.py, routes/, services/, repositories/,
models/, prompts/) plus `tests/` in the three-layer layout mandated by the
testing rules. Frontend is out of scope for this feature.

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
