# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Mindfolio AI — a CMoney 籌碼 K 線 hackathon prototype (AWS AI Hackathon). Core concept: **Reverse Portfolio Onboarding** — show evidence-grounded market insights first, then let the user confirm their stock relationship with one tap (是我的持股 / 只是觀察 / 不相關). Zero prompt, zero upload, one tap. No chat UI.

**Source of truth**: `docs/11_COMPLETE_MVP_SPEC.md`. If any other doc conflicts with it, the spec wins.

## Current state

Pre-code for the API. `apps/api/` contains only the OpenAPI contract (v0.2.0) and READMEs — no Python package, no `pyproject.toml`, no tests yet. The web prototype (`apps/web/prototype/`, plain HTML/CSS/JS), the DB schema (`infra/schema/001_init.sql`, 8 tables), and an offline `apps/ai-training/` pipeline (see below) exist. Backend development in `apps/api/` is the current focus, in Python with FastAPI (uv-managed, psycopg3). When scaffolding the Python project, also establish the tooling (dependency management, test runner) and record the commands here.

Spec-driven development is in use (GitHub Spec Kit). Feature specs live under `docs/api/<###-feature>/`: **001** is the core one-tap loop; **002** covers interaction events, concern-feedback, and the internal dashboard. `.specify/memory/constitution.md` holds the non-negotiable engineering principles.

## Architecture

```text
apps/web (React target; prototype is static HTML)
  → apps/api (FastAPI)
      ├── CSV Adapter        # reads data/Delivery_Hackathon_DataPackage_20260624/
      ├── Context Builder    # merges market + institutional + community + portfolio context
      ├── Moment Engine      # scores cards: relevance × impact × novelty − interruption_cost
      │                      #   (ranking input: MomentSignal JSONL from apps/ai-training)
      ├── Card Generator     # Bedrock → structured Action Card JSON (schema-validated, with fallback)
      ├── Portfolio Service  # persists one-tap confirmations + concern signal
      └── Event Service      # idempotent interaction-event ingest + funnel metrics (feature 002)
  → PostgreSQL (infra/schema/001_init.sql)

apps/ai-training (OFFLINE, separate)   # unsupervised Market Moment Detector
  CMoney CSV → build_features → train_moment_detector → score_moments → MomentSignal JSONL
```

Planned `apps/api/src/` layout: `main.py`, `routes/`, `services/`, `repositories/`, `models/`, `prompts/`.

Build order (per `apps/api/src/README.md`): Day 1 runs the contract end-to-end with fixed LEO demo data; the CSV adapter comes after — do not build a data pipeline first. `apps/ai-training` is offline; the online API only reads its JSONL output and never trains during a request.

## API contract is law

`apps/api/contracts/openapi.yaml` (v0.2.0) is the authoritative contract between frontend and backend — neither side invents fields. Endpoints:

**Feature 001 — core loop:**
- `GET /v1/stocks/{stock_id}/context?as_of=` — evidence-grounded stock context (close, institutional net 1d/20d, holding ratio, dividend yield, community counts + ratio, `demo_news[]`)
- `GET /v1/users/{user_id}/cards/next` — highest-priority action card; **204** when none eligible
- `POST /v1/users/{user_id}/cards/{card_id}/feedback` — one-tap action (`confirmed_holding` | `watch_only` | `irrelevant`); body requires `action` + `occurred_at`; returns the updated `PortfolioRelationship` (no follow-up card — dropped in v0.2.0)
- `GET /v1/users/{user_id}/portfolio` — user-confirmed relationships only
- `POST /v1/users/{user_id}/reset`, `GET /health` — demo ops

**Feature 002 — telemetry & concern:**
- `POST /v1/users/{user_id}/concern-feedback` — `worried` | `routine` | `mute` (user-stated, never model-inferred)
- `POST /v1/events/batch`, `GET /v1/users/{user_id}/events` — idempotent interaction events (front-end outbox; `event_id` is the idempotency key)
- `GET /v1/dashboard/metrics` — internal funnel counts

The one demo card is **seeded in the schema** (`signal-divergence-2382`, `action_cards.id` is TEXT); `cards/next` serves it, feedback consumes it.

## AI boundaries (hard rules)

- **Deterministic Python computes all numbers** (20-day institutional net, 7-day bullish ratio, scoring). The LLM never does arithmetic or derives figures.
- **Bedrock only** turns pre-computed evidence into narrative + structured card JSON. Validate LLM output against the card schema; on failure, fall back to a fixed template (the demo must still work with Bedrock down).
- LLM output must never contain buy/sell direction, target prices, or return guarantees; community aggregates are never framed as the user's personal emotion/anxiety.
- **One training exception**: `apps/ai-training` is an offline *unsupervised* Market Moment Detector (anomaly/divergence detection over daily aggregates → `MomentSignal`). It must not predict holdings, anxiety, price, or buy/sell; `anomaly_score` is never surfaced as an accuracy figure. Everything else stays out of scope: chat UI, free-text input, screenshot upload, RAG, vector DB, multi-agent frameworks, holding/price prediction.

## Data facts

- Demo baseline date is fixed: **`2025-12-31`**. Demo stock: **2382 廣達** (close 272, institutional_net_20d −60,265, community_bullish_ratio_7d 0.939). Demo user: **LEO** (seeded in the SQL schema).
- Organizer CSVs and PDFs live in `data/` but are **gitignored** (redistribution not cleared) — never commit them; public demos use a minimal validated subset only.
- `community_bullish_ratio_7d` counts only posts with an explicit bullish/bearish stance — not overall sentiment.
- Only `user_confirmed` relationships may be written to the portfolio (enforced by a CHECK constraint in the schema); candidate/unconfirmed relationships must never become holdings.
- `portfolio_relationships` has nullable `average_cost`/`shares` columns, but the one-tap onboarding flow must leave them null — the columns exist for a future opt-in flow, not this one.

## Degradation ladder

Demo must complete the loop (insight → one-tap confirm → portfolio update) under all of: Bedrock down (fixed card copy), DB down (state held in browser), API down (prototype's built-in 2382 evidence JSON).