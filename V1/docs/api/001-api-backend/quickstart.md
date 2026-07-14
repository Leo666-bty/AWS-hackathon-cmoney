# Quickstart: Mindfolio API Backend

Validation guide — proves the feature works end-to-end. See
[plan.md](plan.md) for design, [contracts/](contracts/README.md) for the
API surface.

## Prerequisites

- macOS with Homebrew; `brew install uv` (Python 3.11+ managed by uv)
- PostgreSQL (either local install or Docker):
  `docker run -d --name mindfolio-pg -e POSTGRES_PASSWORD=dev -p 5432:5432 postgres:16`
- Organizer CSV package present at `data/Delivery_Hackathon_DataPackage_20260624/`
- AWS credentials with Bedrock access (optional — the loop must also pass
  with `BEDROCK_ENABLED=false`)

## Setup

```bash
cd apps/api
uv sync                                        # install deps from pyproject/uv.lock
createdb mindfolio || true                     # or docker exec
psql "$DATABASE_URL" -f ../../infra/schema/001_init.sql
cp .env.example .env                           # fill DATABASE_URL etc.
```

## Run

```bash
cd apps/api
uv run uvicorn src.main:app --reload --port 8000
# startup must log the base path/port and fail fast if CSVs are missing
```

## Validation scenarios

All paths are under the `/api` base path (contract `servers`).

```bash
BASE=http://localhost:8000/api

# 0. liveness
curl -s $BASE/health                           # → {"status":"ok"}

# 1. US2: pinned evidence (SC-002)
curl -s "$BASE/v1/stocks/2382/context?as_of=2025-12-31"
# → close=272, institutional_net_20d=-60265, community_bullish_ratio_7d=0.939

# 2. US1: the loop (SC-001)
curl -s $BASE/v1/users/LEO/portfolio           # → []
CARD=$(curl -s $BASE/v1/users/LEO/cards/next)  # → signal_divergence card, 3 actions
CARD_ID=$(echo "$CARD" | python3 -c 'import sys,json;print(json.load(sys.stdin)["card_id"])')
curl -s -X POST $BASE/v1/users/LEO/cards/$CARD_ID/feedback \
  -H 'content-type: application/json' \
  -d '{"action":"confirmed_holding","occurred_at":"2025-12-31T10:00:00Z"}'
# → PortfolioRelationship (2382 holding); v0.2.0 has no follow_up_card
curl -s $BASE/v1/users/LEO/portfolio           # → [2382 holding, source user_confirmed]
curl -s -i $BASE/v1/users/LEO/cards/next | head -1   # → HTTP 204 (card consumed)

# 3. US5: reset & rerun (SC-005)
curl -s -X POST $BASE/v1/users/LEO/reset -i | head -1  # → 204
curl -s $BASE/v1/users/LEO/portfolio           # → [] again; loop replays

# 4. negatives (SC-006)
curl -s -i "$BASE/v1/stocks/9999/context?as_of=2025-12-31" | head -1   # → 404
curl -s -i "$BASE/v1/stocks/2382/context?as_of=bad-date" | head -1     # → 422
curl -s -i -X POST $BASE/v1/users/LEO/cards/$CARD_ID/feedback \
  -H 'content-type: application/json' -d '{"action":"buy"}' | head -1  # → 422

# 5. degradation (SC-003): restart with BEDROCK_ENABLED=false and rerun step 2
#    — cards must come from the fixed template, loop still completes
```

## Tests

```bash
cd apps/api
uv run pytest                                   # unit + integration + contract
uv run pytest tests/contract -q                 # contract-only (openapi.yaml conformance)
uv run pytest --cov=src --cov-report=term-missing   # coverage, target 80%+
```

Expected: pinned-value tests (SC-002), loop test (SC-001), fallback test
(SC-003), negative tests (SC-006/007) all green before demo rehearsal.
