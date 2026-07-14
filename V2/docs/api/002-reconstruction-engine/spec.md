# Feature Specification: Portfolio Reconstruction Engine

**Feature Directory**: `V2/docs/api/002-reconstruction-engine`

**Created**: 2026-07-14

**Status**: Draft — constants pinned from `V2/demo/script.js` (the de-facto oracle)

**Input**: The deterministic core of Mindfolio V2. Given five stocks, each with a
buy month + price (band or exact) and a still-holding/sold state, rebuild
returns, the Portfolio Fingerprint, a four-axis persona, a data-confidence
score, and the 2025 decision score. Backend recomputes everything (Constitution
II); it MUST reproduce the demo's formulas exactly so frontend and backend agree.
The AI narrative is generated from the verified result DTO only (isolated).

## Pinned formulas (source of truth: `demo/script.js`, verified 2026-07-14)

**Band representative price** (`priceAtBand`, spread = high − low):
`低 = low + spread/6`, `中 = low + spread/2`, `高 = low + spread·5/6`.

**Factor for a raw price** (`factorForRawPrice`): the regime whose `[low,high]`
contains the price → its `factor`; else the month `factor`.

**Per trade** (`configValues`):
- `exitMonth` = holding ? "12" : sellMonth
- `buyRaw` = exact ? buyExact : band price; `exitRaw` = (sold & exact) ? sellExact : exitData.close
- `buyAdjusted` = buyRaw × factorForRawPrice(buyData, buyRaw)
- `exitAdjusted` = (holding | sellMode=estimate) ? exitData.adjustedClose : exitRaw × factorForRawPrice(exitData, exitRaw)
- `entryPosition` = (buyRaw − buyData.low) / max(buyData.high − buyData.low, 1e-4)
- `duration` = exitMonth − buyMonth (integer months)
- `confidence`: base = exact ? 100 : 78; if sold&estimate −8; if sold&exact → (c+100)/2; if buy or exit month has corporateAction −15; final = max(45, round(c))
- `return` = (exitAdjusted / buyAdjusted − 1) × 100

**Portfolio (5 trades)** (`computeResultData`):
- `averageReturn` = mean(return)
- `entryAverage` = mean(clamp(entryPosition, 0, 1))
- `durationAverage` = mean(duration / 11)
- `diversity` = 1 − Σ(industryCount/5)² (HHI over the five stocks' industries)
- `exactRatio` = count(buyMode=exact) / 5
- `confidence` = round(mean(trade.confidence))
- **persona code** = axis1+axis2+axis3+precision:
  - axis1 `L` if entryAverage ≤ 0.5 else `T`
  - axis2 `H` if holdings ≥ 3 OR durationAverage ≥ 0.55 else `A`
  - axis3 `D` if diversity ≥ 0.65 else `C`
  - precision `X` if exactRatio ≥ 0.5 else `E`
  - name/headline from the 8-entry personaMap (LHD…TAC) keyed by axis1+2+3
- **fingerprint vector** = [entryAverage, durationAverage, diversity, exactRatio, clamp((averageReturn+50)/150, 0, 1)]
- **scores**:
  - outcome = clamp(round(20 + averageReturn·0.45), 0, 40)
  - entry = round((1 − entryAverage)·25)
  - capture (per trade): future = adjustedClose of months after buyMonth; none → 10; else `6 + (exitAdjusted − min)/max(max−min,1e-4)·14`; portfolio = round(clamp(mean, 0, 20))
  - data = round(confidence/100·15)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate one reconstructed trade (Priority: P1)

The builder validates a single stock/month/price input and gets a displayable
validation state, without creating any holding.

**Acceptance Scenarios**:
1. Exact price inside the month range → valid; outside → invalid with the range
   in the message.
2. Corporate-action month + exact price: valid only if the price falls in a
   regime; the response names the regime factor that will apply. Band mode is
   rejected for a corporate-action month.
3. Missing/negative price → invalid. Unknown stock/month → 404.

### User Story 2 - Complete five-stock reconstruction (Priority: P1)

Submit five trades; the backend re-validates all five from raw input (never
trusting prior validate calls), then returns per-trade results, the equal-weight
average return, confidence, the fingerprint vector, the persona code+name, the
four scores, and the confirmable "still holding" candidates.

**Acceptance Scenarios**:
1. Given five valid trades, the result reproduces the demo formulas exactly
   (same inputs → same persona, vector, scores, returns).
2. Any invalid trade in the batch → 422 with which trade failed; nothing is
   treated as confirmed.
3. `holdings` candidates = the trades marked `holding`; watch/sold never appear
   as confirmed holdings (that is a separate consent step, feature 003).

### User Story 3 - AI narrative from the verified result (Priority: P2)

The result DTO is turned into a short narrative by Bedrock, schema-validated,
with a deterministic fixed-template fallback so the result always returns.

**Acceptance Scenarios**:
1. Valid Bedrock JSON → narrated result. 2. Timeout/schema-fail/provider-error
   → fixed-template narrative, result still returned. 3. Narrative never
   contains buy/sell direction, target price, return guarantee, or a
   psychological diagnosis; never recomputes a number or overwrites the persona.

### Edge Cases
- `sellMonth ≤ buyMonth` → invalid (a sold trade must exit after entry).
- Fewer than five trades, or a stock repeated → 422.
- Reproducibility: identical input yields byte-identical persona/scores (property test).

## Requirements *(mandatory)*

- **FR-001**: The engine MUST implement the pinned formulas above in
  `packages/mindfolio-core` (pure, shared with training). Endpoints in
  `apps/api` orchestrate and serve; they compute no numbers themselves.
- **FR-002**: `POST /api/v2/reconstructions/validate` validates one trade and
  returns a display state; it MUST NOT create a holding.
- **FR-003**: `POST /api/v2/reconstructions/complete` MUST re-validate all five
  trades from raw input (never trust a prior validate), then return the full
  result DTO; any invalid trade → 422.
- **FR-004**: Only trades marked `holding` are eligible confirmable candidates;
  the engine never writes confirmed holdings (that is feature 003 + consent).
- **FR-005**: The AI narrative service receives ONLY the verified result DTO
  (no raw prices, credentials, or PII), validates Bedrock output against a
  Pydantic schema, and falls back to a fixed template on any failure; content
  guardrails per Constitution III.
- **FR-006**: Identical input MUST produce identical output (property tests).

### Result DTO (the contract the AI narrative consumes)

```text
ReconstructionResult:
  trades: [ { stock_id, name, industry, buy_month, exit_month, relation,
              buy_raw, exit_raw, return_pct, confidence } ]
  average_return: float
  confidence: int
  persona_code: str          # e.g. "LHDX"
  persona_name: str
  persona_headline: str
  fingerprint: [float x5]    # entry, duration, diversity, exact_ratio, norm_return
  scores: { outcome:int, entry:int, capture:int, data:int }
  holding_candidates: [stock_id]
```

## Success Criteria *(mandatory)*

- **SC-001**: `complete` reproduces the demo's persona/vector/scores for a fixed
  five-stock scenario (deterministic oracle).
- **SC-002**: 100% of card requests return a schema-valid result with the AI
  provider disabled (fixed-template narrative).
- **SC-003**: Invalid trades never yield a confirmed holding; watch/sold never
  appear in `holding_candidates`.
- **SC-004**: Both endpoints validate against the OpenAPI schema in contract tests.

## Assumptions

- `confirmed-holdings` (consent + persistence) is feature 003, not here.
- No DB; the engine is pure over the file catalog (feature 001 repository).
- The demo (`V2/demo/script.js`) is the formula oracle; where docs/02 and the
  demo differ, the demo wins (it is what the frontend ships) and docs/02 is
  updated.
