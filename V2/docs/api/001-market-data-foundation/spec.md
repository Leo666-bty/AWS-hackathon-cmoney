# Feature Specification: Market Data Foundation & Read Endpoints

**Feature Directory**: `V2/docs/api/001-market-data-foundation`

**Created**: 2026-07-14

**Status**: Implemented (decisions resolved and tasks completed 2026-07-14)

**Input**: First backend vertical slice for Mindfolio V2. Load the 300-stock
2025 market catalog into the FastAPI backend and expose the three read
endpoints the builder needs (popular, search, monthly envelope). Everything
downstream (trade reconstruction) depends on the envelope being queryable, so
this is the foundation. Grounded in the real skeleton the team pushed
(`V2/apps/api`, `V2/packages/mindfolio-core`, Makefile toolchain, `/api/v2`
base path) and in `V2/data/README.md` + `V2/tools/build_market_catalog.py`.

## Why this slice first

The reconstruction engine, persona, and scoring all read from the monthly
price envelope. Standing up the catalog + read endpoints is the smallest
independently-testable increment that unblocks all later backend work and lets
the frontend build search/selection against a frozen contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse & Search the 300-Stock Catalog (Priority: P1)

The builder UI shows popular stocks (ranked by 同學會 view count) and lets the
user search 300 stocks by code, name, or industry, so they can pick five
familiar stocks without a full price dump.

**Independent Test**: Call popular → 12 stocks ordered by views; call
search "台積" → 2330 appears in results.

**Acceptance Scenarios**:

1. **Given** the loaded catalog, **When** `GET /api/v2/stocks/popular?limit=12`
   is called, **Then** it returns up to `limit` stock summaries ordered by view
   count descending (id, name, industry, views).
2. **Given** the catalog, **When** `GET /api/v2/stocks/search?q=台積&limit=20`
   is called, **Then** it returns stock summaries whose code, name, or industry
   matches `q`, capped at `limit`.
3. **Given** an empty or whitespace `q`, **When** search is called, **Then** it
   returns an empty list (not the whole catalog).
4. **Given** the read endpoints, **Then** responses carry only UI-needed
   summary fields — never the full 300-stock month tables in one payload.

---

### User Story 2 - Query a Month's Price Envelope (Priority: P1)

For a chosen stock and month, the builder needs the raw price envelope (low,
high, month-end close, adjustment factor, corporate-action flag) and which
price-input modes are allowed, so the user can enter a plausible price.

**Independent Test**: Call envelope for 2330 / 2025-04 → returns raw low/high,
factor, `corporateAction`, and `allowed_price_modes`.

**Acceptance Scenarios**:

1. **Given** the catalog, **When**
   `GET /api/v2/stocks/{stock_id}/months/{yyyy_mm}/envelope` is called for a
   stock/month that exists, **Then** it returns `stock_id`, `month`, `raw_low`,
   `raw_high`, month-end `close`/`adjusted_close`, `factor`, `corporate_action`,
   `regimes` (pre/post-action raw-price bands + factor), and
   `allowed_price_modes`.
2. **Given** a month **without** a corporate action, **Then**
   `allowed_price_modes = ["band", "exact"]`.
3. **Given** a month **with** a corporate action (`corporate_action = true`),
   **Then** `allowed_price_modes = ["exact"]` — band estimates are refused
   because the merged raw range is distorted (per `V2/data/README.md`).
4. **Given** an unknown `stock_id` or a month with no data, **When** envelope
   is called, **Then** HTTP 404 with a `detail` message.
5. **Given** a malformed `yyyy_mm` (not `YYYY-MM`), **When** called, **Then**
   HTTP 422.

---

### User Story 3 - Reproducible Catalog Build & Startup Load (Priority: P2)

The backend reads a structured JSON catalog (built deterministically from the
organizer CSVs), loaded once at startup, so numbers are reproducible and the
service fails fast if the catalog is missing.

**Independent Test**: Build the catalog from CSVs, start the API, hit
`/api/v2/health` → ok; remove the catalog, start → fails fast with a clear
message.

**Acceptance Scenarios**:

1. **Given** `V2/tools/build_market_catalog.py`, **When** run, **Then** it
   produces a structured JSON catalog covering all 300 stocks and their monthly
   envelopes.
2. **Given** `MINDFOLIO_MARKET_DATA_PATH` pointing at the catalog, **When** the
   API starts, **Then** the catalog is loaded once and held in memory.
3. **Given** a missing/unreadable catalog, **When** the API starts, **Then**
   startup fails immediately with a message naming the path (no empty
   responses).

---

### Edge Cases

- Stock exists but the requested month has no trading data → 404 (not an empty
  envelope).
- Corporate-action month → band mode refused (US2 scenario 3).
- Search matching is case-insensitive and trims whitespace; numeric `q` matches
  stock codes by prefix/substring.
- `limit` out of range (≤0 or huge) → clamp to a sane bound or 422 (Open
  Decision 3).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backend MUST implement three read endpoints under `/api/v2`
  exactly per the OpenAPI schema (contract-first): `GET /stocks/popular`,
  `GET /stocks/search`, `GET /stocks/{stock_id}/months/{yyyy_mm}/envelope`.
- **FR-002**: Popular MUST rank by 同學會 view count descending, capped at
  `limit` (default 12); search MUST match `q` against code/name/industry
  (case-insensitive), capped at `limit` (default 20); empty `q` → empty list.
- **FR-003**: The envelope response MUST expose raw low/high, month-end raw and
  adjusted close, adjustment factor, `corporate_action`, the pre/post-action
  `regimes`, and `allowed_price_modes`, where corporate-action months allow
  only `["exact"]` and others allow `["band", "exact"]`.
- **FR-004**: All catalog-derived numbers MUST be produced deterministically
  (Constitution II); the read endpoints perform no arithmetic beyond selecting
  and shaping pre-built catalog values. The `allowed_price_modes` rule and any
  envelope shaping live in `packages/mindfolio-core`; routers in `apps/api`.
- **FR-005**: The catalog MUST be built by `V2/tools/build_market_catalog.py`
  from the organizer CSVs in `V2/data/`, output in a backend-readable JSON form
  (resolved JSON delivery decision below), and loaded once at startup via
  `MINDFOLIO_MARKET_DATA_PATH`; a missing catalog fails fast.
- **FR-006**: Unknown `stock_id`/month → 404 with `detail`; malformed
  `yyyy_mm` → 422. No endpoint returns the full month tables for all stocks in
  one payload.

### Key Entities

- **Stock Summary**: id, name, industry, views, popular flag (for popular/search).
- **Month Envelope**: stock_id, month, raw_low, raw_high, close, adjusted_close,
  factor, corporate_action, regimes[], allowed_price_modes.
- **Market Catalog**: the full built snapshot (asOf, stockCount,
  monthEnvelopeCount, popular ids, stocks[]) — read-only, loaded at startup.

## Success Criteria *(mandatory)*

- **SC-001**: popular returns the 12 highest-view stocks in view order.
- **SC-002**: search "台積" returns 2330; search by industry returns members of
  that industry; empty query returns [].
- **SC-003**: envelope for a known corporate-action month returns
  `allowed_price_modes = ["exact"]`; a normal month returns
  `["band", "exact"]`.
- **SC-004**: All three endpoints publish Pydantic response models in generated
  OpenAPI and endpoint tests assert their response shapes. A generated-client
  contract test remains a future hardening item.
- **SC-005**: With the catalog removed, the API fails to start with a clear
  message (no silent empty responses).
- **SC-006**: The built catalog covers 300 stocks and reproduces byte-identical
  envelope numbers on rebuild from the same CSVs.

## Assumptions

- This feature performs no PostgreSQL reads; the read-only file catalog is its
  data source. The wider application uses PostgreSQL only for confirmed holdings.
- The frontend's `demo/market-data.js` stays as the teammate's frontend fixture;
  the backend consumes a separate JSON output (no shared JS import).
- Band representative prices (1/6, 1/2, 5/6 of the month range) and the >5%
  corporate-action threshold are already pinned in `V2/data/README.md` and
  implemented in the build tool; this slice does not re-decide them (they are
  consumed by the later reconstruction slice, not by these read endpoints).

## Resolved decisions (2026-07-14)

1. **Catalog JSON delivery** → add an additive `--json` output to
   `build_market_catalog.py` that writes a pure `.json` alongside the existing
   `market-data.js`; the backend reads the JSON via `MINDFOLIO_MARKET_DATA_PATH`.
   The frontend's `market-data.js` is untouched. (Touches the shared tools file
   — additive only, coordinated.)
2. **Envelope path** → `GET /api/v2/stocks/{stock_id}/months/{yyyy_mm}/envelope`
   (per docs/09; the frozen contract the frontend generates against).
3. **`limit` bounds** → silently clamp `limit` to `[1, 100]`.
