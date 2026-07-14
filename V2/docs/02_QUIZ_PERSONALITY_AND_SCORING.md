# Reconstruction, Personality & Scoring

> Aligned with the implemented engine (`packages/mindfolio-core/market/reconstruction.py`),
> which mirrors the shipped reference `V2/demo/script.js` exactly. All rounding
> is **round-half-up** (JS `Math.round` / Python `floor(x + 0.5)`) — banker's
> rounding would drift scores by 1. Where a number is pinned below, the backend
> and the frontend compute it identically.

## Portfolio Fingerprint

Five-dimensional vector (raw floats, not rounded):

```text
[entry_position, holding_duration, sector_diversity, input_precision, normalized_return]
```

- `entry_position` — mean of each trade's `(buy_raw − month_low) / (month_high − month_low)`, clamped to [0,1].
- `holding_duration` — mean of `(exit_month − buy_month) / 11`.
- `sector_diversity` — `1 − Σ(industry_count / 5)²` (1 − HHI over the five industries).
- `input_precision` — share of trades entered with an exact price.
- `normalized_return` — `clamp((portfolio_return + 50) / 150, 0, 1)` (visualization only).

## Persona — four axes (with pinned cut-offs)

Names come from the first three axes; the fourth describes data precision. This
is an explainable product label, **not** a psychological scale.

| Axis | Low → High | Rule |
|---|---|---|
| L / T | Low-entry 低接 → Trend-confirmed 順勢 | `L` if `entry_position ≤ 0.5` else `T` |
| H / A | Hold 長抱 → Active 主動 | `H` if `holdings ≥ 3` **or** `holding_duration ≥ 0.55` else `A` |
| D / C | Diversified 分散 → Concentrated 集中 | `D` if `sector_diversity ≥ 0.65` else `C` |
| X / E | Exact 精準 → Estimated 估算 | `X` if `input_precision ≥ 0.5` else `E` |

`persona_code` = the four letters (e.g. `LHDX`). The API returns `persona_code`,
`persona_name`, and `persona_headline` (the display copy) directly — the frontend
does not map a key.

## Eight personas (keyed by the first three axes)

| Prefix | Name | Prefix | Name |
|---|---|---|---|
| LHD | 低接收藏家 | THD | 趨勢配置師 |
| LHC | 深潛集中派 | THC | 主題領航員 |
| LAD | 低點輪動者 | TAD | 動能輪動者 |
| LAC | 逆勢狙擊手 | TAC | 趨勢突擊手 |

## Price reconstruction

Band representative price (buy in "band" mode), `spread = high − low`:
`低 = low + spread/6`, `中 = low + spread/2`, `高 = low + spread·5/6`.

Each raw price × its month adjustment factor (regime-specific in a
corporate-action month), then:

```text
return = adjusted_exit / adjusted_entry − 1        (shown as %)
portfolio_return = equal-weight mean of the five returns
```

- Holding → exit is December's month-end adjusted close.
- Sold without an exact sell price → the sell month's month-end adjusted close.

## Data confidence (per trade, then averaged; min 45)

- Exact buy price: base **100**. Band estimate: base **78**.
- Sold with month-end **estimate**: **−8**.
- Sold with an **exact** sell price: `confidence = (confidence + 100) / 2`.
- Buy or exit month has a corporate action: **−15**.
- Per trade: `max(45, round(confidence))`; result shows the five-trade mean.

Confidence measures reconstruction-data precision, not trade authenticity.

## 2025 情境決策力 (pinned formulas)

| 維度 | 上限 | 公式 |
|---|---:|---|
| 報酬結果 | 40 | `clamp(round(20 + portfolio_return × 0.45), 0, 40)` |
| 進場位置 | 25 | `round((1 − entry_position) × 25)` |
| 報酬捕捉 | 20 | per trade: no future months → 10; else `6 + (exit_adjusted − min)/(max − min) × 14` over the buy-month's later months' adjusted closes; portfolio = `round(clamp(mean, 0, 20))` |
| 資料完整 | 15 | `round(confidence / 100 × 15)` |

Scores apply only to this hindsight scenario; never framed as real investing skill.
