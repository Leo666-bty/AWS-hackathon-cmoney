# Implementation Plan: Market Data Foundation & Read Endpoints

**Feature**: `V2/docs/api/001-market-data-foundation` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

## Summary

Stand up the read foundation for Mindfolio V2: extend the catalog build tool to
emit backend-readable JSON, load it once at startup, and expose three read
endpoints (`popular`, `search`, monthly `envelope`) under `/api/v2`. Pure
shaping (envelope + `allowed_price_modes`) lives in `packages/mindfolio-core`;
HTTP lives in `apps/api`. No database — the file catalog is the fixture.

## Technical Context

**Language/Toolchain**: Python 3.11+, venv + pip + `V2/python-requirements.txt`,
Makefile (`make dev-api`, `make test`) — the team's setup, not uv.

**Backend deps (already present)**: fastapi, uvicorn, pydantic-settings, boto3,
mindfolio-core; test: httpx, pytest. No DB driver needed this slice.

**Data**: catalog JSON built by `V2/tools/build_market_catalog.py` from
`V1/data/…CSV`; read via `MINDFOLIO_MARKET_DATA_PATH`.

**Base path**: `/api/v2`. **Settings prefix**: `MINDFOLIO_`.

**Testing**: pytest (unit in `packages/mindfolio-core/tests`; api unit/contract
in `apps/api/tests`); FastAPI TestClient + a small fixture catalog.

## Constitution Check

| Principle | Gate | Status |
|---|---|---|
| I. Contract-First | 3 endpoints/fields fixed in OpenAPI; contract tests validate | ✅ |
| II. Server-Authoritative Deterministic | numbers come from the built catalog; endpoints only select/shape; shaping in core | ✅ |
| III. AI Guardrails | no AI in this slice | ✅ (n/a) |
| IV. Test-First | core rules + endpoints tested before implementation; envelope/allowed-modes property-ish tests | ✅ |
| V. Confirmed-Holding Gate | no writes/holdings in this slice | ✅ (n/a) |
| VI. Demo Degradation | fail-fast on missing catalog at startup | ✅ |

No violations → no Complexity Tracking entries.

## Code placement

```text
V2/
├── tools/build_market_catalog.py     # + additive --json output
├── data/market-catalog.json          # built artifact (backend fixture)
├── packages/mindfolio-core/src/mindfolio_core/
│   ├── domain/models.py              # StockSummary, MonthEnvelope (pydantic)
│   └── market/envelope.py            # allowed_price_modes + envelope shaping (pure)
└── apps/api/src/mindfolio_api/
    ├── config.py                     # + market_data_path
    ├── repositories/market_data.py   # load JSON at startup, index, query
    ├── routers/stocks.py             # popular / search / envelope
    └── main.py                       # include stocks router; startup load + fail-fast
```

## Structure Decision

Follow the team's monorepo exactly. Pure/deterministic logic and DTOs go to
`mindfolio-core` (shared with training, no FastAPI import); the repository +
routers + startup wiring go to `apps/api`. The build tool change is additive
(new JSON output; existing JS untouched).
