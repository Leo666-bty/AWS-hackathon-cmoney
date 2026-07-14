# Tasks: Market Data Foundation & Read Endpoints

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · Paths relative to `V2/`.
**Tests**: TDD (Constitution IV) — write failing tests first within each story.

## Phase 1: Catalog build (data foundation)

- [x] T001 Add an additive `--json PATH` option to `tools/build_market_catalog.py` that writes the same `build()` payload as pure JSON (default `data/market-catalog.json`); keep the existing `market-data.js` output unchanged
- [x] T002 Run the tool against `V1/data/…` and verify the JSON: 300 stocks (3584 month-envelopes), 2330 2025-04 reproduces docs/09 (raw_low 780 / raw_high 952), 2382 廣達 present; built `data/market-catalog.json` (fixture, gitignored via data/*.json? — see note)
- [x] T003 Point `MINDFOLIO_MARKET_DATA_PATH` at `data/market-catalog.json` in `.env.example`
- [ ] T000 (pre-req, done) Move organizer CSV package + PDFs from root `data/` → `V1/data/` to match the tool/docs/constitution; removed empty root `data/`

## Phase 2: Core domain (packages/mindfolio-core)

- [ ] T004 [P] Unit tests in `packages/mindfolio-core/tests/test_envelope.py`: `allowed_price_modes(corporate_action=False)==["band","exact"]`, `==True→["exact"]`; envelope shaping maps catalog month dict → MonthEnvelope with all fields
- [ ] T005 [P] Implement `domain/models.py` (StockSummary, MonthEnvelope pydantic models) and `market/envelope.py` (`allowed_price_modes`, `to_month_envelope`) — pure, no FastAPI

## Phase 3: Repository (apps/api)

- [ ] T006 Unit tests in `apps/api/tests/test_market_repo.py`: load a tiny fixture catalog → popular ordered by views & capped; search matches code/name/industry case-insensitively, empty q→[]; envelope lookup hit/miss; missing file → raises typed startup error
- [ ] T007 Implement `repositories/market_data.py`: load JSON once, index by stock_id, expose `popular(limit)`, `search(q, limit)` (clamp limit to [1,100]), `envelope(stock_id, month)`; raise a clear error if the file is missing/unreadable
- [ ] T008 Add `market_data_path` to `config.py`; load the repository in `main.py` startup (fail-fast) and expose it to routers

## Phase 4: Endpoints (apps/api)

- [ ] T009 Contract + behavior tests in `apps/api/tests/test_stocks_endpoints.py` (FastAPI TestClient + fixture catalog): popular 200 ordered/capped (SC-001); search 200 incl. empty-q→[] (SC-002); envelope 200 with `allowed_price_modes` = `["exact"]` on corporate-action month / `["band","exact"]` otherwise (SC-003); unknown stock/month → 404 detail; malformed `yyyy_mm` → 422
- [ ] T010 Implement `routers/stocks.py` (GET popular / search / `{stock_id}/months/{yyyy_mm}/envelope`) with Pydantic response models mirroring the OpenAPI schema; include under `/api/v2` in `main.py`
- [ ] T011 Startup fail-fast test in `apps/api/tests/test_startup.py`: missing catalog path → app creation/startup raises with the path in the message (SC-005)

## Phase 5: Verify

- [ ] T012 `make test` green; add coverage for core + repo + routers; `curl` the three endpoints per spec (popular/search/envelope incl. a corporate-action month) and confirm shapes match the OpenAPI schema
- [ ] T013 Sync the OpenAPI: ensure `apps/api` auto-generated `/api/v2/openapi.json` documents the three endpoints so the frontend can generate its typed client (Constitution I)

## Dependencies

T001→T002→T003 (build first). T004/T005 (core) are independent [P]. T006–T008 (repo) need T005. T009–T011 (endpoints) need T007–T008. T012–T013 last. TDD: tests (T004/T006/T009/T011) before their implementation.
