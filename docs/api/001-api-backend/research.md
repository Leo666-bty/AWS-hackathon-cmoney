# Phase 0 Research: Mindfolio API Backend

**Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

## R1. Toolchain — uv

- **Decision**: `uv` for dependency management, venv, and task running
  (`uv sync`, `uv run pytest`, `uv run uvicorn ...`). `pyproject.toml` +
  `uv.lock` live in `apps/api/`.
- **Rationale**: user decision 2026-07-14; single fast tool, built-in
  lockfile. Install via `brew install uv`.
- **Alternatives considered**: Poetry (slower, second tool to learn under
  time pressure), pip+venv (no lockfile).

## R2. Web framework — FastAPI, sync endpoints

- **Decision**: FastAPI + Pydantic v2, synchronous route handlers (FastAPI
  runs them in a threadpool).
- **Rationale**: FastAPI is mandated by the architecture docs; sync handlers
  keep the DB layer (psycopg3 sync) and tests simple at demo scale.
- **Alternatives considered**: async handlers + asyncpg — rejected as
  unnecessary concurrency complexity for a single-user demo.

## R3. Database access — psycopg3, hand-written SQL

- **Decision**: `psycopg[binary]` with parameterized SQL inside repository
  classes; one connection pool (`psycopg_pool`) created at startup. Upserts
  use `INSERT ... ON CONFLICT ... DO UPDATE` (latest-wins per clarification).
- **Rationale**: user decision 2026-07-14; 5 fixed tables, transparent SQL,
  schema constraints (CHECK source='user_confirmed', UNIQUE card+user) do the
  guarding.
- **Alternatives considered**: SQLAlchemy 2.0 (abstraction cost > benefit at
  this scale), asyncpg (see R2).

## R4. CSV adapter — stdlib csv, in-memory indexes

- **Decision**: stdlib `csv.DictReader` with `encoding='utf-8-sig'` (files
  carry a BOM), loaded once at startup into dict indexes keyed by
  `(stock_id, date)`. No pandas.
- **Rationale**: 72k–106k rows per file loads in well under a second; zero
  heavy dependencies; deterministic.
- **Verified field mappings** (against the real package, 2026-07-14):

  | File | Date format | Fields used |
  |---|---|---|
  | `01_Price_Valuation_2025.csv` | `YYYYMMDD` | `股票代號`, `股票名稱`, `收盤價` |
  | `02_Institutional_Trading_2025.csv` | `YYYYMMDD` | `股票代號`, `買賣超合計` |
  | `10_Forum_Posts_Replies_Daily_Stats_2025.csv` | `YYYY-MM-DD` (ISO) | `股票代號`, `看多發文`, `看空發文` |

  Date formats differ between files — normalize to `datetime.date` at load.

## R5. Evidence algorithms — verified against raw data

All three pinned demo values reproduce exactly from the organizer package:

- **close**: `收盤價` of the stock on `as_of` from file 01 → `272.0` ✓
- **institutional_net_20d**: sum of `買賣超合計` over the last **20 trading
  days** (dates present in file 02 for that stock) ending at `as_of`,
  rounded to int → `-60265` ✓ (window 2025-12-03…2025-12-31)
- **community_bullish_ratio_7d**: `Σ看多 ÷ (Σ看多 + Σ看空)` over the **7
  calendar days** ending at `as_of`, rounded to 3 decimals → `216/230 =
  0.939` ✓; `null` when the denominator is 0 (per clarification).

**v0.2.0 additional StockContext fields** (contract expanded upstream; all
deterministic column reads, no new algorithm risk): `community_bullish_count_7d`
/ `community_bearish_count_7d` are the 7-day sums already computed above
(216 / 14); `institutional_net_1d` is file 02 `買賣超合計` on `as_of`;
`institutional_holding_ratio` is file 02 `法人持股比率(%)`; `annual_return`
comes from file 03 (Return_Rate); `dividend_yield` from file 05 (Dividend).
`demo_news` is NOT computed — it is read from the seeded `demo_news` table
(is_demo=true) and must be replaced by an authorized source before production.

## R6. Bedrock integration — boto3, model ID from config

- **Decision**: `boto3` `bedrock-runtime` client using the Converse API;
  model ID and AWS region come from environment variables
  (`BEDROCK_MODEL_ID`, `AWS_REGION`) — no hardcoded model. Request asks for
  card JSON; response is parsed and validated with a Pydantic model
  (`CardDraft`: title, summary, evidence phrasing). Any exception or
  validation failure → fixed-template card (Principle III).
- **Rationale**: env-configured model survives hackathon account/model
  availability changes; Converse API is the current uniform Bedrock
  interface. Timeout kept short (a few seconds) so the demo never stalls.
- **Alternatives considered**: LangChain et al. — out of scope by
  constitution (no agent frameworks).

## R7. Contract testing — pytest + TestClient + openapi.yaml schemas

- **Decision**: pytest with FastAPI `TestClient`; contract tests load
  `apps/api/contracts/openapi.yaml` (source of truth), pull `components.schemas`,
  and validate live responses with `jsonschema`. Pinned-value tests assert
  272 / −60265 / 0.939 for 2382 @ 2025-12-31.
- **Rationale**: validates against the real contract file so drift fails
  tests (Principle I); no codegen step.
- **Alternatives considered**: schemathesis (property-based; overkill in the
  time budget — noted as nice-to-have).

## R8. Configuration

- **Decision**: `pydantic-settings` reading environment variables /
  `.env` (gitignored): `DATABASE_URL`, `BEDROCK_MODEL_ID`, `AWS_REGION`,
  `DATA_DIR`, `CORS_ORIGINS`, `BEDROCK_ENABLED` (kill switch for the
  degradation demo).
- **Rationale**: schema-validated config at startup = fail fast with clear
  messages (Principle VI); `.env.example` is committed.
