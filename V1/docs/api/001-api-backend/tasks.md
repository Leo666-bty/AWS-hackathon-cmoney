# Tasks: Mindfolio API Backend

**Input**: Design documents from `docs/api/001-api-backend/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — TDD is mandatory (Constitution Principle IV). Within every story: write tests, watch them fail, then implement.

**Organization**: Grouped by user story; each story is an independently testable increment. All `src/` and `tests/` paths below are relative to `apps/api/`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold the uv-managed Python project inside `apps/api/`

- [ ] T001 Scaffold uv project in apps/api/: `pyproject.toml` (deps: fastapi, uvicorn, pydantic-settings, psycopg[binary], psycopg-pool, boto3, pyyaml; dev: pytest, pytest-cov, httpx, jsonschema, ruff), `uv.lock` via `uv sync`, and the directory tree from plan.md (src/{routes,services,repositories,models,prompts}/, tests/{unit,integration,contract}/ with `__init__.py`)
- [ ] T002 Implement settings in src/config.py via pydantic-settings (DATABASE_URL, BEDROCK_MODEL_ID, AWS_REGION, DATA_DIR, CORS_ORIGINS, BEDROCK_ENABLED, DATA_MODE=fixed|csv) and commit `.env.example`
- [ ] T003 [P] Configure ruff + pytest (coverage 80% threshold, test paths) in apps/api/pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: App skeleton, DB access, contract-mirroring models, and test harness that every story needs

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement connection pool + per-request transaction helper in src/repositories/db.py (psycopg_pool; DB-unreachable → raises a typed error)
- [ ] T005 Implement app factory in src/main.py: lifespan (init pool, load evidence source per DATA_MODE, fail fast per FR-010), CORS from settings, exception handlers shaping 404/422/503 bodies with `detail`, startup log of base path/port; mount all routes under `/api`
- [ ] T006 [P] Implement contract-mirroring Pydantic models in src/models/api.py (v0.2.0): StockContext (expanded evidence set + `community_bullish_ratio_7d: float | None` + `demo_news: list[NewsItem]`), NewsItem, ActionCard, CardAction, PortfolioRelationship (nullable average_cost/shares), FeedbackRequest (`action` + required `occurred_at`); feedback response IS PortfolioRelationship (no follow_up_card envelope) — field names/enums exactly per apps/api/contracts/openapi.yaml
- [ ] T007 [P] Build test harness in tests/conftest.py: test-database fixture applying infra/schema/001_init.sql (fresh per test), TestClient fixture, fixed-evidence fixture (2382 @ 2025-12-31: 272 / −60265 / 0.939), fake Bedrock client fixture
- [ ] T008 [P] Build contract-validation helper in tests/contract/conftest.py: load apps/api/contracts/openapi.yaml, expose `assert_matches_schema(payload, schema_name)` via jsonschema

**Checkpoint**: `uv run pytest` runs (0 tests is fine), `uv run uvicorn src.main:app` starts and fails fast when misconfigured

---

## Phase 3: User Story 1 - One-Tap Feedback Loop (Priority: P1) 🎯 MVP

**Goal**: cards/next → one-tap feedback → portfolio update, on fixed LEO demo data with the fixed-template card (no Bedrock, no CSV yet)

**Independent Test**: quickstart.md scenario 2 — portfolio [] → divergence card → confirmed_holding → portfolio [2382 holding] → cards/next 204

### Tests for User Story 1 (write first, must fail)

- [ ] T009 [P] [US1] Contract tests in tests/contract/test_cards_contract.py: cards/next 200 body vs ActionCard schema; feedback 200 body vs PortfolioRelationship schema (v0.2.0 — no follow_up envelope); portfolio 200 body vs PortfolioRelationship array
- [ ] T010 [P] [US1] Integration test of the happy loop in tests/integration/test_loop.py: empty portfolio → next card (seeded signal_divergence, 3 actions) → confirmed_holding (with occurred_at) → response is holding relationship → portfolio contains 2382 → cards/next returns 204 (card consumed)
- [ ] T011 [P] [US1] Integration tests of feedback semantics in tests/integration/test_feedback.py: watch_only / irrelevant store relationship, holdings stay 0 (SC-007); duplicate feedback latest-wins updates in place, single card_feedback row (FR-015); unknown user_id/card_id → 404 with detail; invalid action OR missing/malformed occurred_at → 422, nothing stored (FR-017)
- [ ] T012 [P] [US1] Unit tests for eligibility & scoring in tests/unit/test_moment_engine.py: card with feedback excluded; irrelevant history lowers similar-card priority (FR-004); priority formula uses pre-computed inputs only

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement fixed evidence source in src/repositories/evidence.py: `EvidenceSource` protocol (expanded StockContext fields + stock_name for (stock_id, as_of)) + `FixedEvidenceSource` with the pinned 2382 values (272 / −60265 / 0.939 plus the v0.2.0 additional fields)
- [ ] T014 [P] [US1] Implement cards + feedback repositories in src/repositories/cards_repo.py and src/repositories/feedback_repo.py (serve the seeded card + stamp shown_at; eligibility query excluding feedbacked cards; feedback upsert `ON CONFLICT (card_id, user_id) DO UPDATE` persisting occurred_at)
- [ ] T015 [P] [US1] Implement portfolio repository in src/repositories/portfolio_repo.py (upsert relationship latest-wins with source `user_confirmed` only, leaving average_cost/shares null; list by user)
- [ ] T016 [US1] Implement moment engine in src/services/moment_engine.py (relevance × impact × novelty − interruption_cost on pre-computed metrics; eligibility per FR-016)
- [ ] T017 [US1] Implement fixed-template card path in src/services/card_generator.py (serve the seeded signal_divergence card; template = seeded title/summary + evidence strings from evidence values; Bedrock rephrase branch stubbed behind BEDROCK_ENABLED=false; no follow_up_card)
- [ ] T018 [US1] Implement portfolio service in src/services/portfolio_service.py (action→relationship mapping, upsert via repo, feedback recording with occurred_at in one transaction; response = updated relationship)
- [ ] T019 [US1] Implement routes in src/routes/cards.py (GET next → 200 seeded card / 204 consumed / 404; POST feedback → 200 relationship / 404 / 422) and src/routes/portfolio.py (GET → 200/404), wired in src/main.py

**Checkpoint**: T009–T012 green; quickstart scenario 2 passes end-to-end — this is the demoable MVP

---

## Phase 4: User Story 2 - Evidence-Grounded Stock Context (Priority: P2)

**Goal**: GET /v1/stocks/{id}/context serves the pinned evidence (still from the fixed source)

**Independent Test**: quickstart scenario 1 — context for 2382 @ 2025-12-31 returns 272 / −60265 / 0.939 / 廣達

### Tests for User Story 2 (write first, must fail)

- [ ] T020 [P] [US2] Contract + pinned-value tests in tests/contract/test_context_contract.py: 200 body vs StockContext schema (all v0.2.0 fields incl. demo_news, nullable ratio); exact pinned values 272 / −60265 / 0.939 (SC-002)
- [ ] T021 [P] [US2] Negative tests in tests/integration/test_context.py: unknown stock → 404 with detail; missing/malformed as_of → 422

### Implementation for User Story 2

- [ ] T022 [US2] Implement context builder in src/services/context_builder.py (EvidenceSource → StockContext with the expanded evidence set; stock name from DB with CSV fallback; `demo_news` read from the demo_news table, is_demo=true)
- [ ] T023 [US2] Implement route in src/routes/stocks.py (GET context with required `as_of` date param), wired in src/main.py

**Checkpoint**: Stock page data live; US1 + US2 together cover the whole Day-1 demo on fixed data

---

## Phase 5: User Story 3 - Real Computation from Organizer Data (Priority: P3)

**Goal**: Replace fixed evidence with deterministic computation over the CSV package (DATA_MODE=csv)

**Independent Test**: quickstart scenario 1 with DATA_MODE=csv reproduces the pinned values from raw CSVs

### Tests for User Story 3 (write first, must fail)

- [ ] T024 [P] [US3] Unit tests for metrics math in tests/unit/test_csv_metrics.py using small synthetic CSV fixtures under tests/fixtures/: 20-trading-day window (fewer available → shorter window), 7-calendar-day community window, ratio rounding to 3 decimals, ratio null when zero stance posts, net rounding to int, BOM + mixed date formats (YYYYMMDD vs ISO) parsed correctly
- [ ] T025 [P] [US3] Startup fail-fast test in tests/unit/test_csv_loading.py: missing required file → startup error naming the file (FR-010)
- [ ] T026 [P] [US3] Real-package pinned-value test in tests/integration/test_csv_real_data.py, marked `@pytest.mark.realdata` + skipif when data/Delivery_Hackathon_DataPackage_20260624/ is absent: computed 2382 @ 2025-12-31 == 272 / −60265 / 0.939

### Implementation for User Story 3

- [ ] T027 [US3] Implement CSV adapter in src/repositories/csv_adapter.py: load 01/02/10 (+ 03 return, 05 dividend) with utf-8-sig, normalize dates, build (stock,date) indexes, expose `CsvEvidenceSource` implementing the EvidenceSource protocol with the R5 algorithms and the v0.2.0 additional fields (annual_return, institutional_net_1d, institutional_holding_ratio, dividend_yield, community counts) sourced deterministically from the CSV columns
- [ ] T028 [US3] Wire DATA_MODE=csv into the src/main.py lifespan (load once at startup, fail fast, log row counts) — demo default becomes csv, fixed remains the fallback mode

**Checkpoint**: Same API, real numbers; flipping DATA_MODE switches sources with zero route changes

---

## Phase 6: User Story 4 - AI-Narrated Cards with Fallback (Priority: P4)

**Goal**: Bedrock generates card narrative from pre-computed evidence; every failure path lands on the fixed template

**Independent Test**: quickstart scenario 5 — loop passes with BEDROCK_ENABLED=true and false, identical evidence values either way

### Tests for User Story 4 (write first, must fail)

- [ ] T029 [P] [US4] Unit tests in tests/unit/test_card_generator.py with the fake Bedrock fixture: valid draft JSON → narrated card; malformed JSON → fixed template; schema-invalid draft → fixed template; client exception/timeout → fixed template; BEDROCK_ENABLED=false → fixed template without calling client (SC-003)
- [ ] T030 [P] [US4] Guardrail unit tests in tests/unit/test_guardrails.py: drafts containing buy/sell direction, target price, or return-guarantee phrasing are rejected → fixed template; evidence numbers in narrative must equal pre-computed inputs (FR-009)

### Implementation for User Story 4

- [ ] T031 [P] [US4] Implement CardDraft model in src/models/card_draft.py and prompt template in src/prompts/card_prompt.py (evidence values interpolated as given; instructions forbid advice/prediction wording)
- [ ] T032 [US4] Implement Bedrock branch in src/services/card_generator.py: boto3 bedrock-runtime Converse call (model/region from settings, short timeout), JSON parse → CardDraft validation → guardrail check → narrated card; any failure → existing fixed template

**Checkpoint**: Demo works with Bedrock up AND down — degradation ladder rung 1 proven

---

## Phase 7: User Story 5 - Demo Operability (Priority: P5)

**Goal**: /health liveness + per-user reset make the demo repeatable

**Independent Test**: quickstart scenario 3 — loop → reset → portfolio empty → same card served again

### Tests for User Story 5 (write first, must fail)

- [ ] T033 [P] [US5] Tests in tests/integration/test_ops.py: GET /health → 200 {"status":"ok"} (contract-validated); full loop → POST reset → 204 → portfolio [] → cards/next serves the divergence card again (SC-005); reset for unknown user → 404

### Implementation for User Story 5

- [ ] T034 [US5] Implement src/routes/ops.py (GET /health; POST /v1/users/{user_id}/reset deleting the user's card_feedback, action_cards, portfolio_relationships in one transaction) and reset logic in src/services/portfolio_service.py, wired in src/main.py

**Checkpoint**: All 6 contract endpoints live; demo is rehearsal-ready

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T035 [P] DB-down degradation test in tests/integration/test_degradation.py: pool unavailable → 503 with detail on business endpoints (health may still answer)
- [ ] T035a [P] CORS test in tests/integration/test_cors.py: a cross-origin request from a configured origin gets the `Access-Control-Allow-Origin` header (FR-014 coverage)
- [ ] T036 Verify coverage ≥ 80% (`uv run pytest --cov=src --cov-report=term-missing`) and fill gaps; run `uv run ruff check src tests` clean
- [ ] T037 [P] Record verified commands (uv sync / uv run uvicorn / uv run pytest) in CLAUDE.md and apps/api/README.md; note DATA_MODE + BEDROCK_ENABLED switches in docs/10_DEMO_RUNBOOK.md (docs/00~11 sync convention)
- [ ] T038 Run quickstart.md end-to-end manually (all 6 scenario blocks) and tick spec Acceptance/Success criteria; fix anything red

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → user stories
- **US1 (Phase 3)**: only needs Phase 2 — MVP
- **US2 (Phase 4)**: needs Phase 2; independent of US1 (shares evidence source T013 — if run before US1, pull T013 forward)
- **US3 (Phase 5)**: swaps the evidence source; independent of US1/US2 logic but validated through US2's endpoint
- **US4 (Phase 6)**: extends T017's card_generator; needs US1
- **US5 (Phase 7)**: reset semantics reference US1's tables; needs US1
- **Polish (Phase 8)**: needs all desired stories

### Within Each User Story

Tests first (fail) → repositories/models → services → routes → green → next story. Commit after each task or logical group (conventional commits).

### Parallel Opportunities

- T003 ∥ T002; T006/T007/T008 ∥ each other after T005
- All test tasks within a story are [P] (different files)
- T013/T014/T015 are [P]; US4's T031 ∥ T029/T030
- Two-person note: backend is one person (neal) — parallelism here mostly means batching independent files in one pass, not multi-dev

---

## Implementation Strategy

**MVP first**: Phases 1–3 (US1) = demoable closed loop on Day 1, exactly the build order mandated by plan.md/CLAUDE.md (contract on fixed data before any data pipeline). Then US2 (same day), US3 (CSV), US4 (Bedrock), US5 (ops), Polish. Stop-and-validate at every checkpoint; each story leaves the previous ones green.
