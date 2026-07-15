# Frontend / FastAPI Backend Architecture

## Current implementation status

兩階段生命週期已實作：**Time Machine（獲客）→ Portfolio Radar（留存）**。獲客側 React frontend 已串接 FastAPI 的熱門／搜尋、月行情 envelope、逐筆 validation、五檔 complete；留存側新增 invite-code session、報告認領（report claim）、report-scoped 持股確認、Portfolio Radar dashboard、卡片偏好與 event batch。共用 Python core 負責所有正式金融計算。`demo/` 仍是靜態 UX reference，不是正式 runtime。

## Architecture decision

V2 正式版本採前後端分離：

- **Frontend**：使用 React + TypeScript，負責股票搜尋介面、五檔表單、進度、結果呈現、分享與錯誤狀態。
- **Backend**：使用 FastAPI + Python，負責資料存取、驗證、金融計算、Portfolio Fingerprint、AI narrative 與持股保存。
- **Data store**：2025 股票主檔、月份 envelope 與 ML 預先評分由版本化 JSON snapshot 提供；PostgreSQL 保存 confirmed holdings、報告、事件與 AI report cache。
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
│ Structured AI Deep Dive     │
│ Bedrock or safe fallback    │
├──────────────┬──────────────┤
│ Market file  │ Holding repo │
└───────┬──────┴───────┬──────┘
        │              │
┌───────▼──────┐ ┌─────▼────────────┐
│ Catalog + ML │ │ PostgreSQL       │
│ scored JSON  │ │ consent/cache   │
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
│   │   ├── ResultRoute.tsx
│   │   ├── ActivateRoute.tsx        # 邀請碼啟用（/activate）
│   │   ├── PortfolioRadarRoute.tsx  # Portfolio Radar 首頁（/app）
│   │   └── PortfolioRadarRoute.test.tsx
│   ├── features/
│   │   ├── reconstruction/    # cross-route reducer/context
│   │   └── portfolio-radar/   # Portfolio Radar dashboard modules
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
| Durable identity | Invite-code session | `/activate` 以邀請碼換 session token；身份由伺服器端 session 推導（`member_id`），前端不再夾帶 `user_id`。現場設定為 `invite_identities="123456:Neal,000000:Leo"`。|
| Calculated result | 不存本地真相 | 一律使用 FastAPI response |

獲客流程仍以小型 reducer/context 實作，不導入大型 global store；重新整理會回到入口，這是匿名獲客階段的已知取捨。留存側則已有 server-derived 身份：complete 回傳 report handle（`report_id` + `claim_token`），登入後 `/activate` 認領報告即把獲客結果綁定到會員身份，跨階段不再依賴前端夾帶 `user_id`。

## Backend module design

```text
apps/api/
├── Dockerfile
├── pyproject.toml
├── src/mindfolio_api/
│   ├── main.py
│   ├── config.py
│   ├── auth.py               # invite-code 驗證 + session token 簽發/驗證
│   ├── routers/
│   │   ├── health.py
│   │   ├── stocks.py
│   │   ├── reconstructions.py
│   │   ├── retention.py      # 留存／AI 8 端點（auth/session、reports、me、events）
│   │   └── holdings.py       # 僅剩共用 repository dependency（舊 routes 已移除）
│   ├── schemas/
│   │   ├── reconstruction.py
│   │   ├── retention.py      # session/report/dashboard/card/event schemas
│   │   └── ai_report.py      # structured report + fixed question IDs
│   ├── services/
│   │   ├── reconstruction.py
│   │   └── retention.py      # dashboard/action-card 組裝
│   ├── ai/
│   │   ├── deep_dive.py
│   │   ├── narrative.py
│   │   ├── prompts.py
│   │   └── fallback.py
│   └── repositories/
│       ├── market_data.py
│       ├── holdings.py
│       ├── market_context.py # validated pre-scored JSON lookup
│       └── retention.py      # reports / AI cache / feedback / events
└── tests/                     # startup/repository/endpoint/narrative/retention tests
```

Routers 只處理 HTTP、schema 與 status code；留存端點透過 `auth.py` 的
`require_member` dependency 做 session 驗證，身份一律由 server-derived session
推導，絕不信任 client 傳入的 `user_id`。Service 負責 orchestration 與重驗，
純金融規則在 `mindfolio-core`。Repositories 不產生人格或報酬，只做資料存取。

AI training 與 FastAPI 在開發環境共用 Python virtual environment 和 shared contract；production API image 不安裝 sklearn，而是載入離線 pipeline 預先評分的 JSON。詳細見 `10_AI_TRAINING_PLAN.md`。

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
`{ "result": ReconstructionResult, "narrative": NarrativeDraft, "report": ReportHandle | null }`：

- `result.trades` — 每檔重建結果（含 return_pct、confidence）。
- `result.average_return`、`result.confidence`。
- `result.fingerprint` — 五維向量。
- `result.persona_code` / `persona_name` / `persona_headline`（**直接回顯示文案**，前端不需 map key）。
- `result.scores` — `{ outcome, entry, capture, data }`。
- `result.holding_candidates` — 可被確認為仍持有的股票代號。
- `narrative` — `{ headline, summary, insight }`（Bedrock 或固定模板 fallback）。
- `report` — `{ report_id, claim_token, expires_at }`；持久層可用時簽發，供留存側登入後認領（持久層不可用時為 `null`，獲客流程照常完成）。

未知股票 → 404；任一筆無效或非 5 筆 → 422。

## Retention API contract（Portfolio Radar）

留存／AI 側 8 個端點同樣在 `/api/v2` 底下，身份一律由 session token 推導，**不接受**
client 傳入的 `user_id`。

> **已移除（安全性）**：舊的 `POST /api/v2/confirmed-holdings` 與
> `GET /api/v2/users/{user_id}/confirmed-holdings` 為未驗證且信任 client `user_id`
> 的路徑（跨會員隔離漏洞），已刪除。確認持股改由下方經驗證、report-scoped 的
> `POST /api/v2/reports/{report_id}/confirmed-holdings` 寫入。

### Session

```http
POST /api/v2/auth/session
```

`{ "invite_code" }` → `{ access_token, token_type: "bearer", member_id, display_name }`。
邀請碼透過 `invite_identities` adapter 映射到 member（現場設定為
`123456:Neal,000000:Leo`）；
無效碼 → 401。

### Claim report

```http
POST /api/v2/reports/{report_id}/claim
```

需 bearer session。`{ "claim_token" }` → `{ report_id, member_id, claimed_at, holding_candidates }`，
把獲客報告綁定到登入會員。找不到 → 404；token 錯 → 403；過期 → 410；已被別人認領 → 409；持久層不可用 → 503。

### Confirm holdings（唯一寫入路徑）

```http
POST /api/v2/reports/{report_id}/confirmed-holdings
```

需 bearer session。`{ "stock_ids": [ ×1..5 ] }`。後端由已認領報告的原始 trades
**無狀態重新驗證**算出 `holding_candidates`，只有屬於候選集合的股票才寫入（否則 422）；
寫入時記錄 `source_report_id`。回傳該會員確認持股清單。持久層不可用 → 503。

### Member dashboard

```http
GET /api/v2/me/dashboard
```

需 bearer session。回傳 Portfolio Radar 首頁：`{ member_id, display_name, report,
portfolio, priority_card, weekly_review }`。`report` 為已認領報告的人格/fingerprint 摘要；
`priority_card` 為當前優先 action card（含 `narrative_source: bedrock|fallback`）。

### Action-card feedback

```http
POST /api/v2/me/action-cards/{card_id}/feedback
```

需 bearer session。`{ "preference": "review_evidence" | "routine" | "mute" }` →
`{ card_id, preference, saved_at }`。**注意**：`mute` 目前只被記錄，尚未改變下一張卡片
的排序（Moment-Engine ranking 為未來 Feature 006）。

### Event batch

```http
POST /api/v2/events/batch
```

`{ "events": [ InteractionEventInput × 1..50 ] }` → `{ accepted_event_ids }`。
以 `event_id` 做 idempotent 寫入，重送不重複記錄。

### AI Deep Dive

```http
POST /api/v2/reports/{report_id}/ai-report
POST /api/v2/reports/{report_id}/questions
```

兩者都需要 bearer session 並驗證 report ownership。第一支回傳結構化摘要、優勢、
觀察點、歷史市場時刻與三個問題 chips；相同 context/model/prompt version 讀取 cache。
第二支只接受 `why-persona`、`most-influential-trade`、`why-anomalous-month`，不接受自由文字。
AI report 的使用者可見文案固定為台灣繁體中文；Bedrock 只生成文案，問題標籤、
`source`、版本與時間由 server 組裝。模型只接收 backend 格式化的 `display_facts`
與 evidence key，不接收原始精度數字。英文／混合語言、未知 evidence ref、過長或
語意 guardrail 不合格時會記錄拒絕原因並修復重試一次，仍不合格才使用
deterministic fallback。prompt/context version 變更會自動使舊 cache 失效。

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
FastAPI → Frontend: final result + fallback-safe narrative + report handle
--- retention（登入後）---
Frontend → FastAPI: POST /auth/session（邀請碼換 session token）
Frontend → FastAPI: POST /reports/{id}/claim（認領獲客報告）
Frontend → FastAPI: POST /reports/{id}/confirmed-holdings（consent 後寫入）
Frontend → FastAPI: GET /me/dashboard（Portfolio Radar 首頁）
Frontend → FastAPI: POST /reports/{id}/ai-report（cache or generate）
Frontend → FastAPI: POST /reports/{id}/questions（固定 question_id）
```

## AI in the same Python environment

AI 與計算共用 Python environment，不代表兩者混成同一函式：

1. `services/reconstruction.py` 重驗輸入並呼叫 `mindfolio-core`。
2. Core 同一次 deterministic 計算產生 trade result、vector、persona 與 scores。
3. `market_context.py` 以 `stock_id:YYYY-MM` 查詢離線預先評分 context。
4. `ai/narrative.py` 與 `ai/deep_dive.py` 只接收上述 verified DTO／context。
5. AI output 必須通過內部 Pydantic schema、繁中比例、數字與 evidence guardrail；
   public response 的 metadata 與問題標籤由 server 補上。
6. Timeout、英文／混合語言、schema error、provider failure 或 guardrail 不合格時
   回傳 deterministic fallback。

LLM 不得接收資料庫 credential、完整匿名 event history、未驗證價格或可識別個資。

## Runtime and deployment

### Local development

```text
Browser → Vite :5173 /api/* proxy → FastAPI/Uvicorn :8000
FastAPI → data/market-catalog.json + market-context-2025-v1.json
FastAPI → in-memory holdings store（DATABASE_URL 未設定時）
```

由 FastAPI 設定明確 CORS allowlist；不使用 `*` 搭配 credentials。

### Deployment target（已建立 Compose 定義）

- 一台 EC2 執行 Docker Compose：`web`（nginx）、`api`（Uvicorn）、
  `postgres`（PostgreSQL 16）。
- nginx 對外提供 React static build，並將 `/api/*` proxy 到 API container。
- API 從 image 內的 `market-catalog.json` 與 pre-scored context JSON 讀市場資料，以 Compose service name
  `postgres` 連資料庫。
- PostgreSQL 不發布 5432；named volume `pgdata` 落在 EC2 EBS。
- Bedrock 為可選功能，由 API 端授權，不把憑證放前端。Demo（workshop 帳號無法建 IAM Role）以短期 Bedrock API key（bearer token）授權；正式環境改用 EC2 IAM Role，不在 `.env` 放長期 AWS key。

完整啟動、驗收、安全組與備份注意事項見 `11_DEPLOYMENT.md`。目前已部署並上線於
單機 EC2（Docker Compose），真實 Bedrock 已於該機實測 live（短期 API key）；
尚未完成的是正式 IAM Role 授權、自訂網域與 HTTPS。

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

**React × FastAPI + AI P0 已完成**（14 支端點：獲客 6、留存 6、AI 2；
V2 Python 77 tests、React 6 tests、production build 與 lint 通過）。市場資料與
pre-scored context 走版本化檔案，確認持股與 reports/cache/feedback/events 走 Postgres
四表 schema。`V2/demo/` 是靜態互動 reference；`apps/ai-training/` 已完成離線模型 pipeline。

真實 Bedrock 已於 EC2 實測 live：Deep Dive 回傳「Bedrock 生成」、evidence-grounded
的解讀（Converse，`openai.gpt-oss-120b-1:0`，短期 API key 授權）；repo 預設
`bedrock_enabled=false`，部署以環境變數開啟，任何失敗仍走 deterministic fallback。

尚未完成（roadmap，勿誇大）：正式 IAM Role 授權（demo 走 bearer token）；action-card `mute` 偏好已儲存但尚未
影響下一張卡片排序（Feature 006）；留存程式碼已上線，但 `docs/api/004..007` 的
per-feature SDD spec/plan/tasks 資料夾尚未補齊，屬未結清的 paper-trail 缺口。
