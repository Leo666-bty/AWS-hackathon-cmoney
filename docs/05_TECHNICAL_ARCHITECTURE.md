# Technical Architecture

## Three-Day MVP

```text
React Web
├── Watchlist / Stock / Portfolio
├── Contextual AI Card + suggested follow-ups
├── Event Collector
└── Local outbox fallback
        │ REST
        ▼
FastAPI
├── CMoney CSV Adapter
├── Context Builder + Moment Engine
├── Bedrock Narrative Generator
├── Portfolio / Concern Service
└── Event Ingestion + Metrics
        │
        ▼
PostgreSQL
```

離線模型管線獨立於線上請求：

```text
CMoney CSV
  → apps/ai-training
    → features
    → Market Moment Detector
    → MomentSignal JSONL
      → FastAPI Moment Engine
```

`apps/web/prototype` 是可操作的產品 reference 與離線備援；三天 Definition of Done 仍要求 React、FastAPI、PostgreSQL 的 happy path 串通。

## Web Responsibilities

- 自選股與 2382 個股四分頁。
- AI 情境卡與一鍵關係回饋。
- 三個 contextual follow-up，不提供空白 ChatGPT 頁。
- Concern Signal 與個人庫存。
- 事件先寫入 localStorage outbox，再批次送 API。
- API 未確認前顯示 `queued`，不可假裝已同步。

## API Responsibilities

- 提供固定日期的股票 context 與 Action Card。
- 保存已確認 Portfolio Relationship。
- 保存 Concern Feedback。
- 以 `event_id` 冪等接收 `/events/batch`。
- 提供最小漏斗 metrics 與最近事件。
- 呼叫 Bedrock，驗證 schema，失敗時回固定模板。

## AI Training Responsibilities

- 以正規化的市場、法人、社群每日資料建立 rolling features。
- 使用 Isolation Forest 找出異常時點，再以規則標記事件類型。
- 輸出符合 `apps/ai-training/contracts/moment-score.schema.json` 的 MomentSignal。
- 不訓練持股、焦慮或漲跌預測模型。
- 模型不可用時，由 API 使用 validated rules 與固定廣達 evidence 降級。

## Database Scope

`infra/schema/001_init.sql` 包含：

- users、stocks
- portfolio_relationships
- action_cards、card_feedback
- concern_feedback
- interaction_events
- demo_news

股數與成本只保留 nullable 欄位，首次互動不詢問。新聞資料必須標示 `is_demo` 或改接授權來源。

## Event Contract

最小事件集：`watchlist_view`、`stock_open`、`stock_tab_view`、`card_impression`、`card_evidence_open`、`relationship_feedback`、`concern_feedback`、`ai_followup_open`、`portfolio_view`、`holding_removed`、`news_open`。

每筆至少包含 `event_id`、`session_id`、`user_id`、`surface`、`occurred_at`。`metadata` 保存 tab、證據類型、news ID 與 time-to-action 等非敏感資訊。

## AWS Mapping

| 能力 | 選項 |
|---|---|
| Web | Amplify 或 S3 + CloudFront |
| API | Lambda + API Gateway，或 App Runner |
| Database | RDS PostgreSQL；時間不足可用既有託管 PostgreSQL |
| GenAI | Amazon Bedrock |
| CSV | S3 或 API 啟動時載入 validated demo subset |

## Graceful Degradation

1. Bedrock 失敗：固定卡片與固定 follow-up 文案。
2. API 失敗：事件留在 local outbox，畫面明示待同步。
3. Database 失敗：LEO 狀態暫存在瀏覽器，不宣稱伺服器已保存。
4. 新聞來源未完成：保留 Demo Feed 標籤，不影響主閉環。
