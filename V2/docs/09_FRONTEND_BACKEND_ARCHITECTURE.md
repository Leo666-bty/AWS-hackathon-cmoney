# Frontend / FastAPI Backend Architecture

## Current implementation status

V2 vertical slice 已完成：React frontend 已串接 FastAPI 的熱門／搜尋、月行情 envelope、逐筆 validation、五檔 complete 與 confirmed holdings；共用 Python core 負責所有正式金融計算。`demo/` 仍是靜態 UX reference，不是正式 runtime。

## Architecture decision

V2 正式版本採前後端分離：

- **Frontend**：使用 React + TypeScript，負責股票搜尋介面、五檔表單、進度、結果呈現、分享與錯誤狀態。
- **Backend**：使用 FastAPI + Python，負責資料存取、驗證、金融計算、Portfolio Fingerprint、AI narrative 與持股保存。
- **Data store**：2025 股票主檔與月份 envelope 由版本化 JSON snapshot 提供；PostgreSQL 只保存使用者明確同意的 confirmed holdings。
- **AI provider**：由 Python backend 呼叫；前端不直接持有模型憑證或組裝模型 context。

```text
┌─────────────────────────────┐
│ Web Frontend                │
│ React / TypeScript          │
│ Form state / UX / Sharing   │
└──────────────┬──────────────┘
               │ HTTPS JSON
┌──────────────▼──────────────┐
│ FastAPI Backend             │
│ Routers + Pydantic schemas  │
├─────────────────────────────┤
│ Deterministic Services      │
│ Validation / Return / Score │
├─────────────────────────────┤
│ AI Narrative Service        │
│ Bedrock or schema LLM       │
├──────────────┬──────────────┤
│ Repositories │ Event writes │
└───────┬──────┴───────┬──────┘
        │              │
┌───────▼──────┐ ┌─────▼────────────┐
│ PostgreSQL   │ │ CMoney data feed │
└──────────────┘ └──────────────────┘
```

## Why FastAPI

- 計算、資料清理、AI/ML 與 API 都在 Python 生態，不需要跨語言複製公式。
- Pydantic 可作為 request、domain input、AI output schema 的共同驗證層。
- 自動 OpenAPI 方便前端產生 typed client 與評審檢視 contract。
- 同一 runtime 可使用 NumPy/Pandas、傳統模型與 AWS Bedrock SDK。
- 目前 route 為同步函式，deterministic 計算量小且可預測；Bedrock 或高延遲 I/O 正式上線時再改 async／worker，避免黑客松階段引入不必要並行複雜度。

## Why React + TypeScript

- 五檔選股、逐檔表單、非同步驗證與結果頁適合拆成 feature components。
- TypeScript 可直接使用 FastAPI OpenAPI 產生 typed API client，降低前後端 contract 漂移。
- React Query 類型的 server-state layer 可處理搜尋、envelope、validation 與 reconstruction request cache。
- React Hook Form 類型的 form layer 管理欄位與前端基本格式；金融規則仍由後端判定。
- 靜態分享畫面與結果頁可以元件化，不需要把整個流程塞進單一 script。

## Frontend module design

```text
apps/web/
├── package.json
├── vite.config.ts
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── App.tsx
│   │   └── providers.tsx
│   ├── routes/
│   │   ├── LandingRoute.tsx
│   │   ├── BuilderRoute.tsx
│   │   ├── ReconstructionRoute.tsx
│   │   └── ResultRoute.tsx
│   ├── features/
│   │   └── reconstruction/    # cross-route reducer/context
│   ├── shared/
│   │   ├── api/               # Zod runtime validation + typed client
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   └── styles/
└── tests/
```

### React state boundary（已實作）

| State | 建議位置 | 例子 |
|---|---|---|
| Server state | Query cache | 熱門股票、搜尋結果、price envelope、final result |
| Wizard draft | `useReducer` + Context | 已選五檔、每檔 trade draft、complete result |
| Field state | Form library／component | 月份、價格模式、實際價格 |
| Durable identity | Backend session | anonymous reconstruction ID、member ID |
| Calculated result | 不存本地真相 | 一律使用 FastAPI response |

目前以小型 reducer/context 實作，不導入大型 global store。重新整理會回到入口，這是匿名 MVP 的已知取捨；正式產品可加入 server-side draft session。

## Backend module design

```text
apps/api/
├── pyproject.toml
├── src/mindfolio_api/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── stocks.py
│   │   ├── reconstructions.py
│   │   └── holdings.py
│   ├── schemas/
│   │   ├── stock.py
│   │   ├── reconstruction.py
│   │   └── holding.py
│   ├── services/
│   │   ├── price_validation.py
│   │   ├── reconstruction.py
│   │   ├── fingerprint.py
│   │   └── holding.py
│   ├── ai/
│   │   ├── narrative.py
│   │   ├── prompts.py
│   │   └── fallback.py
│   └── repositories/
│       ├── stocks.py
│       ├── market_data.py
│       └── portfolios.py
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

Routers 只處理 HTTP、authentication、schema 與 status code；所有金融規則放在 services。Repositories 不產生人格或報酬，只做資料存取。

AI training 與 FastAPI 共用 Python virtual environment 和 shared feature package，但 training command 不在 Web request 內執行。詳細見 `10_AI_TRAINING_PLAN.md`。

## Frontend responsibilities

前端可以做：

- debounce 搜尋與顯示熱門股票。
- 暫存尚未送出的五檔表單。
- 顯示 API 回傳的 envelope、validation message 與 result。
- loading、retry、empty、expired session 與 consent UI。
- 產生不含敏感明細的分享畫面。

前端不可以做：

- 決定價格是否合理。
- 選擇 adjustment factor。
- 計算正式報酬、可信度、score 或 persona。
- 自行把「測驗選股」寫成 confirmed holding。
- 直接呼叫 Bedrock／LLM。

## API contract

All under base path `/api/v2`. OpenAPI schema at `/api/v2/openapi.json`;
interactive docs at `/api/v2/docs`. Liveness: `GET /api/v2/health` →
`{ status, service, version, model_status }`.

### Popular and search

```http
GET /api/v2/stocks/popular?limit=12
GET /api/v2/stocks/search?q=台積&limit=20
```

只回傳 UI 所需的股票摘要，不回傳 300 檔完整行情。

### Monthly envelope

```http
GET /api/v2/stocks/{stock_id}/months/{yyyy_mm}/envelope
```

Response（實作為超集，含還原/factor/regime 供除錯與 UI）：

```json
{
  "stock_id": "2330",
  "month": "2025-04",
  "raw_low": 780.0,
  "raw_high": 952.0,
  "close": 908.0,
  "adjusted_close": 892.0,
  "factor": 0.98267621,
  "corporate_action": false,
  "regimes": [{ "low": 780.0, "high": 952.0, "factor": 0.98267621 }],
  "allowed_price_modes": ["band", "exact"]
}
```

公司行動月 `corporate_action=true` 且 `allowed_price_modes=["exact"]`（區間估算被拒），`regimes` 列出前後段 raw-price 區段與其 factor；adjustment 計算不交給前端。未知股票/月份 → 404，月份格式錯（非 `YYYY-MM`）→ 422。

### Validate one reconstructed trade

```http
POST /api/v2/reconstructions/validate
```

Request 只含 stock、月份、持有狀態與使用者輸入價格。Response 回傳可顯示的 validation state；不建立 confirmed holding。

### Complete portfolio reconstruction

```http
POST /api/v2/reconstructions/complete
```

Request：`{ "trades": [ TradeConfig × 5 ] }`（`TradeConfig`：`stock_id`、`relation`
holding/sold、`buy_month` "01".."12"、`buy_mode` band/exact、`buy_band`
low/mid/high、`buy_exact`、`sell_month`、`sell_mode` estimate/exact、`sell_exact`）。

FastAPI 必須重新驗證全部五檔，不信任先前 validate response。回傳
`{ "result": ReconstructionResult, "narrative": NarrativeDraft }`：

- `result.trades` — 每檔重建結果（含 return_pct、confidence）。
- `result.average_return`、`result.confidence`。
- `result.fingerprint` — 五維向量。
- `result.persona_code` / `persona_name` / `persona_headline`（**直接回顯示文案**，前端不需 map key）。
- `result.scores` — `{ outcome, entry, capture, data }`。
- `result.holding_candidates` — 可被確認為仍持有的股票代號。
- `narrative` — `{ headline, summary, insight }`（Bedrock 或固定模板 fallback）。

未知股票 → 404；任一筆無效或非 5 筆 → 422。

### Confirm holdings

```http
POST /api/v2/confirmed-holdings
GET  /api/v2/users/{user_id}/confirmed-holdings
```

POST：`{ "user_id", "trades": [ ×5 ] }`。使用者 consent 後呼叫；後端**無狀態重新驗證**——重跑重建算出 `holding_candidates`，**只寫入這些**（前端無法夾帶非持有股票）。回傳該使用者的確認持股清單。GET 列出某使用者已確認持股。持久層（Postgres）不可用 → 503。

## Request sequence

```text
Frontend → FastAPI: search/popular
Frontend → FastAPI: get monthly envelope
Frontend → FastAPI: validate trade input
Frontend → FastAPI: complete five-stock reconstruction
FastAPI → Services: validate all inputs again
Services → Repository: load market data
Services → Fingerprint: calculate vector/persona
FastAPI → AI Service: generate narrative from verified result
FastAPI → Frontend: final result + fallback-safe narrative
Frontend → FastAPI: confirm holdings after explicit consent
```

## AI in the same Python environment

AI 與計算共用 Python environment，不代表兩者混成同一函式：

1. `reconstruction` 完成 deterministic result。
2. `fingerprint` 產生固定 vector 與 persona code。
3. `ai_narrative` 只接收上述 verified DTO。
4. AI output 必須通過 Pydantic schema。
5. Timeout、schema error 或 provider failure 時回傳 deterministic fallback。

LLM 不得接收資料庫 credential、完整匿名 event history、未驗證價格或可識別個資。

## Runtime and deployment

### Local development

```text
Frontend dev server → http://localhost:8000/api/v2
FastAPI/Uvicorn     → PostgreSQL or local read-only fixture
```

由 FastAPI 設定明確 CORS allowlist；不使用 `*` 搭配 credentials。

### AWS-oriented target

- Frontend：S3 + CloudFront，或既有 Web hosting。
- FastAPI：App Runner 或 ECS Fargate container。
- Database：RDS PostgreSQL／Aurora PostgreSQL。
- AI：Amazon Bedrock，由 backend IAM role 存取。
- Secrets：AWS Secrets Manager；不得打包進前端。

黑客松 Demo 可先以單一 FastAPI process＋唯讀資料 fixture 執行，不必為了展示技術力加入不必要的 queue 或 microservices。

## Testing strategy

- **Unit**：價格 envelope、regime、adjustment、報酬、confidence、fingerprint。
- **Property tests**：賣出月不得早於買進月；異常價格不得通過；相同輸入產生相同 deterministic result。
- **Integration**：FastAPI + repository + database fixture。
- **Contract**：OpenAPI response 與前端 typed client。
- **React unit**：表單狀態、錯誤呈現、loading 與 consent gate。
- **React integration**：mock FastAPI contract，驗證選股到結果流程。
- **E2E**：React frontend + FastAPI test database 的關鍵 happy path 與異常價格 path。
- **AI tests**：schema、guardrail、timeout fallback；不拿 LLM 文案 snapshot 當金融計算測試。

## Current status

**React × FastAPI vertical slice 已完成**（8 支端點：health、stocks
popular/search/envelope、reconstructions validate/complete、confirmed-holdings
POST/list；V2 Python suite 58 tests 與 React production build 通過）。市場資料走檔案
catalog、確認持股走 Postgres。`V2/demo/` 是靜態互動 reference；
`apps/ai-training/` 仍是離線模型 scaffold（狀態 stub，尚未訓練）。
