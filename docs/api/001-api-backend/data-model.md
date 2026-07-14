# Data Model: Mindfolio API Backend

**Date**: 2026-07-14 | **Spec**: [spec.md](spec.md) | **Schema source of truth**: `infra/schema/001_init.sql`

## Persistent entities (PostgreSQL)

The five tables are already defined in `infra/schema/001_init.sql`; this
feature adds no migrations. Summary of how the API uses them:

### users
- `id TEXT PK`, `display_name`, `created_at`. Seeded: `LEO`.
- API never creates users; unknown `user_id` → 404.

### stocks
- `id TEXT PK`, `name`, `industry`, `updated_at`. Seeded: `2382 廣達`.
- Stock names for context responses come from here (fallback: CSV `股票名稱`).

### portfolio_relationships
- PK `(user_id, stock_id)` — **one row per user+stock, upserted in place**
  (latest wins, per clarification 2026-07-14).
- `relationship`: enum `holding | watch_only | irrelevant` (feedback action
  `confirmed_holding` maps to `holding`; the other two map 1:1).
- `importance`: defaults `unknown`; one-tap flow never sets it (no UI for it).
- `average_cost NUMERIC(14,4)`, `shares NUMERIC(18,4)`: nullable; the one-tap
  flow **leaves them null** (Principle V). Present for a future opt-in flow.
- `source`: CHECK-constrained to `user_confirmed` — the DB enforces
  Principle V; the API never writes any other source.
- `confirmed_at`, `updated_at`: refreshed on every upsert.

### action_cards
- `id TEXT PK` (not UUID — upstream v0.2.0), `user_id FK`, `stock_id FK`,
  `card_type`, `title`, `summary`, `evidence JSONB`, `source_date`,
  `shown_at`, `created_at`.
- The demo card `signal-divergence-2382` is **seeded by the schema** with a
  fixed title/summary and raw evidence. `cards/next` serves it and stamps
  `shown_at`; US4 rephrases the narrative via Bedrock at serve time, falling
  back to the seeded copy.

### card_feedback
- `id BIGSERIAL PK`, `card_id TEXT FK`, `user_id FK`, `action TEXT`
  (CHECK in `confirmed_holding | watch_only | irrelevant`),
  `occurred_at` (client-supplied), `received_at` (server default);
  `UNIQUE (card_id, user_id)`.
- Duplicate feedback = `ON CONFLICT (card_id, user_id) DO UPDATE`
  (latest-wins), never a second row.

### Tables owned by feature 002 (present in the same schema, untouched by 001)
- `concern_feedback`, `interaction_events`, `demo_news` — 001 reads `demo_news`
  for the context response's `demo_news` field but writes none of these.

## State transitions

### Action card lifecycle

```text
seeded  --cards/next--> served (shown_at stamped; narrative optionally
                        rephrased by Bedrock)
served  --feedback----> consumed (has card_feedback row; excluded from
                        next-card selection). Response = updated relationship
                        only (no follow_up_card in v0.2.0)
any     --reset-------> user's cards/feedback/relationships wiped; seeded
                        card becomes eligible again
```

Eligibility rule (FR-016): a card with any `card_feedback` row is not
eligible for `cards/next`. The demo has one divergence event, so after
feedback `cards/next` → 204.

### Relationship lifecycle

```text
(none) --feedback--> holding | watch_only | irrelevant (source user_confirmed)
any    --feedback--> overwritten by latest action (upsert)
any    --reset-----> deleted
```

## In-memory entities (CSV adapter, loaded at startup)

- **PriceDay**: `(stock_id, date) → close: float`, plus `stock_name`.
  From file 01 (`日期` YYYYMMDD, `收盤價`).
- **InstitutionalDay**: `(stock_id, date) → net: float` (`買賣超合計`).
  Trading-day calendar per stock = the dates present in file 02.
- **CommunityDay**: `(stock_id, date) → (bullish: int, bearish: int)`
  (`看多發文`, `看空發文`). File 10 uses ISO dates.

Derived values (deterministic, Principle II — see research.md R5):

- `close(stock, as_of)` — exact-date lookup; missing → 404 context.
- `institutional_net_20d(stock, as_of)` = round(Σ net over last ≤20 trading
  days ≤ as_of).
- `community_bullish_ratio_7d(stock, as_of)` = round(Σbull/(Σbull+Σbear), 3)
  over the 7 calendar days ending as_of; `None` when denominator is 0.

## API-layer models (Pydantic)

Mirror `components.schemas` of `apps/api/contracts/openapi.yaml` (v0.2.0)
exactly (Principle I):

- `StockContext` — the three pinned metrics plus `annual_return`,
  `institutional_net_1d`, `institutional_holding_ratio`, `dividend_yield`,
  `community_bullish_count_7d`, `community_bearish_count_7d`,
  `community_bullish_ratio_7d: float | None`, and `demo_news: list[NewsItem]`.
- `NewsItem` — `news_id`, `title`, `summary?`, `published_at`, `source_name`,
  `is_demo`.
- `ActionCard`, `CardAction`.
- `PortfolioRelationship` — includes nullable `average_cost`/`shares`
  (serialized as null in this flow).
- `FeedbackRequest` — `action` + required `occurred_at`.
- **Feedback response is `PortfolioRelationship` itself** (v0.2.0 dropped the
  `{relationship, follow_up_card}` envelope).
- Internal `CardDraft` for validating Bedrock output before it becomes an
  `ActionCard` (never exposed).

## Validation rules (from spec FRs)

- `as_of` must parse as ISO date → else 422 (FastAPI/Pydantic default).
- Feedback body: `action` in the three-value enum AND `occurred_at` a valid
  datetime → else 422.
- Unknown `stock_id` / `user_id` / `card_id` → 404 with `detail`.
- DB unreachable at request time → 503 with `detail`.
- Errors never write partial state (single transaction per request).
