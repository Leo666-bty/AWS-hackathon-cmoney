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
│ Market file  │ Holding repo │
└───────┬──────┴───────┬──────┘
        │              │
┌───────▼──────┐ ┌─────▼────────────┐
│ Catalog JSON │ │ PostgreSQL       │
│ snapshot     │ │ confirmed only  │
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
- TypeScript 搭配 Zod 在 runtime 驗證 FastAPI response；目前 client 為手寫，
  後續可由 OpenAPI codegen 取代以進一步降低 contract 漂移。
- React Query 管理搜尋、envelope query 與 validation／reconstruction mutation
  lifecycle。
- 目前以 component `useState` 管理欄位與前端基本格式；雖已安裝
  React Hook Form，但尚未導入。金融規則仍由後端判定。
- 靜態分享畫面與結果頁可以元件化，不需要把整個流程塞進單一 script。

## Frontend module design

```text
apps/web/
├── package.json
├── Dockerfile
├── nginx.conf
├── vite.config.ts
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   └── providers.tsx
│   ├── routes/
│   │   ├── LandingRoute.tsx
│   │   ├── LandingRoute.test.tsx
│   │   ├── BuilderRoute.tsx
│   │   ├── ReconstructionRoute.tsx
│   │   └── ResultRoute.tsx
│   ├── features/
│   │   └── reconstruction/    # cross-route reducer/context
│   ├── shared/
│   │   ├── api/               # Zod runtime validation + typed client/error
│   │   └── components/        # shared header
│   ├── assets/personality-cards/
│   └── styles/
```

### React state boundary（已實作）

| State | 建議位置 | 例子 |
|---|---|---|
| Server state | Query cache／mutation | 熱門股票、搜尋結果、price envelope、validation request |
| Wizard state | `useReducer` + Context | 已選五檔、每檔 trade draft、後端 complete response |
| Field state | Component `useState` | 月份、價格模式、實際價格 |
| Durable identity | 尚未實作 | 目前 confirmed holdings 固定使用 Demo `LEO` |
| Calculated result | 不存本地真相 | 一律使用 FastAPI response |

目前以小型 reducer/context 實作，不導入大型 global store。重新整理會回到入口，這是匿名 MVP 的已知取捨；正式產品可加入 server-side draft session。

## Backend module design

```text
apps/api/
├── Dockerfile
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
│   │   └── reconstruction.py
│   ├── services/
│   │   └── reconstruction.py
│   ├── ai/
│   │   ├── narrative.py
│   │   ├── prompts.py
│   │   └── fallback.py
│   └── repositories/
│       ├── market_data.py
│       └── holdings.py
└── tests/                     # startup/repository/endpoint/narrative tests
```

Routers 只處理 HTTP、schema 與 status code；目前沒有 authentication layer。
Service 負責 orchestration 與重驗，純金融規則在 `mindfolio-core`。
Repositories 不產生人格或報酬，只做資料存取。

AI training 與 FastAPI 共用 Python virtual environment 和 shared feature package，但 training command 不在 Web request 內執行。詳細見 `10_AI_TRAINING_PLAN.md`。

## Frontend responsibilities

前端可以做：

- debounce 搜尋與顯示熱門股票。
- 暫存尚未送出的五檔表單。
- 顯示 API 回傳的 envelope、validation message 與 result。
- loading、retry、empty 與 consent UI。
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
`{ status, service, version, model_status, narrative_status }`。其中
`narrative_status` 只表示 `bedrock_enabled` 或 `fallback_ready` 的設定模式，
不會由 health endpoint 發出可計費的模型探測請求；實際生成來源由
`narrative.source` 回傳 `bedrock` 或 `fallback`。

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
  "adjusted_close": 892.27,
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

1. `services/reconstruction.py` 重驗輸入並呼叫 `mindfolio-core`。
2. Core 同一次 deterministic 計算產生 trade result、vector、persona 與 scores。
3. `ai/narrative.py` 只接收上述 verified DTO。
4. AI output 必須通過 Pydantic schema。
5. Timeout、schema error 或 provider failure 時回傳 deterministic fallback。

LLM 不得接收資料庫 credential、完整匿名 event history、未驗證價格或可識別個資。

## Runtime and deployment

### Local development

```text
Browser → Vite :5173 /api/* proxy → FastAPI/Uvicorn :8000
FastAPI → data/market-catalog.json
FastAPI → in-memory holdings store（DATABASE_URL 未設定時）
```

由 FastAPI 設定明確 CORS allowlist；不使用 `*` 搭配 credentials。

### Deployment target（已建立 Compose 定義）

- 一台 EC2 執行 Docker Compose：`web`（nginx）、`api`（Uvicorn）、
  `postgres`（PostgreSQL 16）。
- nginx 對外提供 React static build，並將 `/api/*` proxy 到 API container。
- API 從 image 內的 `market-catalog.json` 讀市場資料，以 Compose service name
  `postgres` 連資料庫。
- PostgreSQL 不發布 5432；named volume `pgdata` 落在 EC2 EBS。
- Bedrock 為可選功能，只能由 API 經 EC2 IAM Role 存取；不得在 `.env` 放 AWS key。

完整啟動、驗收、安全組與備份注意事項見 `11_DEPLOYMENT.md`。目前已完成本機
Compose 驗收；實際 EC2、IAM Role、網域與 HTTPS 仍需在目標主機驗證。

## Testing and verification

- **目前 Python suite**：core envelope／validation／reconstruction、artifact
  metadata、market/holding repository、FastAPI endpoint、startup 與 narrative fallback。
- **目前 React test**：Landing route smoke；production TypeScript +
  Vite build是主要整合檢查。
- **目前部署驗收**：Compose build、nginx proxy health、五檔 complete 與
  PostgreSQL volume persistence。
- **後續補強**：OpenAPI-generated client contract test、完整 wizard React
  integration、瀏覽器 E2E、真實 Bedrock IAM／timeout 測試與 EC2 smoke test。

## Current status

**React × FastAPI vertical slice 已完成**（8 支端點：health、stocks
popular/search/envelope、reconstructions validate/complete、confirmed-holdings
POST/list；V2 Python suite 58 tests 與 React production build 通過）。市場資料走檔案
catalog、確認持股走 Postgres。`V2/demo/` 是靜態互動 reference；
`apps/ai-training/` 仍是離線模型 scaffold（狀態 stub，尚未訓練）。
