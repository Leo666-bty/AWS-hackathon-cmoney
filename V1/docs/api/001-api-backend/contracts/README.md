# Contracts

The authoritative API contract for this feature is
[`apps/api/contracts/openapi.yaml`](../../../../apps/api/contracts/openapi.yaml)
— it is deliberately **not copied** here (Constitution Principle I: one
contract, no forks that can drift).

Current contract surface (v0.1.0, amended 2026-07-14):

| Method | Path | Notes |
|---|---|---|
| GET | `/v1/stocks/{stock_id}/context?as_of=` | `community_bullish_ratio_7d` nullable |
| GET | `/v1/users/{user_id}/cards/next` | 200 card / **204 no eligible card** |
| POST | `/v1/users/{user_id}/cards/{card_id}/feedback` | body `action`+`occurred_at`; latest-wins; returns `PortfolioRelationship` only (no follow_up_card in v0.2.0) |
| GET | `/v1/users/{user_id}/portfolio` | user-confirmed only |
| POST | `/v1/users/{user_id}/reset` | demo reset (relationships + feedback + cards) → 204 |
| GET | `/health` | `{"status": "ok"}` |

Contract tests load the YAML directly and validate live responses against
`components.schemas` (see plan.md / research.md R7).

## Internal contract: Bedrock card draft

Bedrock receives pre-computed evidence and must return JSON parseable as:

```json
{
  "title": "string (≤ 40 chars, no advice)",
  "summary": "string (≤ 80 chars)",
  "evidence": ["string", "string"]
}
```

Validated by the `CardDraft` Pydantic model. Numbers in the narrative MUST
match the pre-computed evidence values passed in; any parse/validation
failure or guardrail violation (buy/sell wording, target price) → fixed
template. This internal schema is NOT part of openapi.yaml.
