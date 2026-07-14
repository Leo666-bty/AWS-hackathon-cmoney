# Frontend / FastAPI Backend Architecture

## Current implementation status

架構底座已初始化：React frontend、FastAPI application、共用 Python core 與 offline AI training package 均已建立。現在僅實作 `/api/v2/health` 與前端 foundation route；其餘本文件 API 是下一階段 contract，不應被視為已上線能力。

## Architecture decision

V2 正式版本採前後端分離：

- **Frontend**：使用 React + TypeScript，負責股票搜尋介面、五檔表單、進度、結果呈現、分享與錯誤狀態。
- **Backend**：使用 FastAPI + Python，負責資料存取、驗證、金融計算、Portfolio Fingerprint、AI narrative 與持股保存。
- **Database**：保存股票主檔、月份行情 envelope、匿名重建事件與 confirmed holdings。
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
- `async` 適合資料庫與模型呼叫；CPU-heavy 批次工作仍應移到 background job，不阻塞 request。

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
│   │   ├── router.tsx
│   │   └── providers.tsx
│   ├── routes/
│   │   ├── LandingRoute.tsx
│   │   ├── BuilderRoute.tsx
│   │   ├── ReconstructionRoute.tsx
│   │   └── ResultRoute.tsx
│   ├── features/
│   │   ├── stock-search/
│   │   ├── portfolio-builder/
│   │   ├── trade-reconstruction/
│   │   ├── result-report/
│   │   └── holding-consent/
│   ├── shared/
│   │   ├── api/               # OpenAPI generated client
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   └── styles/
└── tests/
```

### React state boundary

| State | 建議位置 | 例子 |
|---|---|---|
| Server state | Query cache | 熱門股票、搜尋結果、price envelope、final result |
| Wizard draft | `useReducer` + Context | 已選五檔、目前步驟、尚未送出的欄位 |
| Field state | Form library／component | 月份、價格模式、實際價格 |
| Durable identity | Backend session | anonymous reconstruction ID、member ID |
| Calculated result | 不存本地真相 | 一律使用 FastAPI response |

不建議一開始導入大型 global store；只有跨 route wizard draft 確實需要時，才以小型 store 取代 Context。

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

Response：

```json
{
  "stock_id": "2330",
  "month": "2025-04",
  "raw_low": 780.0,
  "raw_high": 952.0,
  "corporate_action": false,
  "allowed_price_modes": ["band", "exact"]
}
```

若有公司行動，可回傳多個可輸入 raw-price regime，但不把內部 adjustment calculation 權限交給前端。

### Validate one reconstructed trade

```http
POST /api/v2/reconstructions/validate
```

Request 只含 stock、月份、持有狀態與使用者輸入價格。Response 回傳可顯示的 validation state；不建立 confirmed holding。

### Complete portfolio reconstruction

```http
POST /api/v2/reconstructions/complete
```

FastAPI 必須重新驗證全部五檔，不信任先前 validate response。成功後回傳：

- 每檔重建結果。
- 五檔等權重推估報酬。
- reconstruction confidence。
- Portfolio Fingerprint vector。
- persona code 與 deterministic description key。
- AI narrative 或 fallback narrative。
- 可被確認為仍持有的 candidate list。

### Confirm holdings

```http
POST /api/v2/confirmed-holdings
```

只有使用者完成 consent 後呼叫。Backend 再次確認 candidate 屬於該 reconstruction/session，避免前端任意寫入其他股票。

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

目前 workspace 的 `V2/demo/` 仍是靜態互動 reference，尚未完成此文件描述的 FastAPI 實作與前端 API 串接。這是刻意的文件決策，不應在簡報中宣稱後端已完成。
