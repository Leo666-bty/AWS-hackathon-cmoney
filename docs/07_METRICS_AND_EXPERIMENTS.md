# Metrics & Experiments

## North Star

> 至少完成一檔「使用者確認持股」的人數。

這直接對應庫存匯入；聊天次數與停留時間不是北極星。

## MVP Funnel

| Stage | Metric | Event |
|---|---|---|
| 正常研究 | 個股開啟率 | `stock_open / watchlist_view` |
| 看見價值 | 卡片曝光 | `card_impression` |
| 查證 | 證據查看率 | `card_evidence_open / card_impression` |
| 建立關係 | 一鍵回饋率 | `relationship_feedback / card_impression` |
| 完成匯入 | 確認持股人數 | action = `confirmed_holding` |
| 理解需求 | Concern 回覆率 | `concern_feedback / relationship_feedback` |
| 延伸互動 | 情境追問開啟率 | `ai_followup_open / relationship_feedback` |
| 取得價值 | Portfolio 查看率 | `portfolio_view / confirmed_holding` |

## Dashboard Minimum

三天版只顯示：事件數、卡片曝光、關係回饋、已確認持股，以及最近 15 筆事件的 queued/synced 狀態。它用於證明資料真的被收集，不是假裝完整 BI 後台。

## Concern Label

`worried`、`routine`、`mute` 是提醒策略的明確標籤。不得將它報告成焦慮盛行率或醫療指標。可衡量的是「哪一種卡片更常讓使用者要求整理證據或降低提醒」。

## Primary Experiment

- A：先問「你有持有廣達嗎？」
- B：先顯示法人 × 社群背離，再詢問關係。

比較一鍵回饋率、持股確認率、不相關率與 time-to-action。

## Target, Not Result

- 一鍵回饋率 ≥ 25%
- 回饋者中的首檔持股確認率 ≥ 40%
- 完成首檔確認時間 ≤ 5 秒
- 確認後 Portfolio 查看率 ≥ 60%
- Evidence 數字正確率 100%
- 投資建議違規率 0%

以上都是待驗證目標，Demo Dashboard 的單一 LEO session 不可當成成效證明。
