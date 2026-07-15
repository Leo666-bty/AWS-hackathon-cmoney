# Implementation Plan

## 已完成的 Demo vertical slice

- 從三份官方 CSV 生成 300 檔月行情 database snapshot。
- 依同學會瀏覽人數產生熱門排行。
- 支援股票代號、名稱、產業搜尋。
- 支援任選五檔、月份、區間或實際價格。
- 支援仍持有／已賣出與賣出月份。
- 實際價格超出月行情時阻擋。
- 使用 adjustment factor 重建可比較報酬。
- 產生資料可信度、Fingerprint vector、人格與漏斗 CTA。

## 已初始化目錄

```text
V2/
├── apps/
│   ├── web/                    # React + TypeScript；只呼叫 API
│   ├── api/                    # FastAPI + Python
│   │   ├── src/mindfolio_api/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   ├── schemas/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   └── ai/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── ai-training/            # Python offline training commands
├── packages/
│   └── mindfolio-core/         # API/Training 共用 features 與 domain calculation
├── python-requirements.txt     # 共用 Python virtual environment 安裝入口
├── package.json               # pnpm workspace scripts
├── docs/
└── demo/                       # 現有靜態 UX reference，非正式架構
```

以上骨架已建立。**兩階段 MVP vertical slice 與 AI P0 已完成**：14 支 API（獲客 6 + 留存／AI 8）、deterministic 重建引擎、AI 敘事 fallback、Postgres 四表持久層（confirmed
holdings + reconstruction_reports + action_card_feedback + interaction_events）、
邀請碼 session 與 report-scoped confirmed holdings，以及 React 六 route 串接
（含 `/activate`、`/app` Portfolio Radar）。Docker Compose 已包含 nginx web、API
與 PostgreSQL，已實際部署於單機 EC2（Compose）。**尚未完成**：HTTPS／自訂網域、
真實 Bedrock 權限驗證（`bedrock_enabled` 預設 false，目前走 fallback）、真正的註冊登入（目前為邀請碼 adapter）、
action card `mute` 尚未影響排序（Feature 006）、以及 `docs/api/004..007` per-feature
SDD 資料夾尚未補齊（paper-trail 缺口）。

## Initialization checkpoint

- [x] React + TypeScript + Vite workspace
- [x] Router、Query provider、API health client
- [x] FastAPI application factory、CORS、OpenAPI、health route
- [x] API／Training 共用 `mindfolio-core`
- [x] Offline training package 與無假數據 artifact contract
- [x] Frontend build／test 與 Python test baseline
- [x] 股票與月份行情 repositories
- [x] reconstruction／holding API contracts
- [x] deterministic return／fingerprint services
- [x] React 選股、逐檔重建、結果與持股同意流程
- [x] 單一 EC2 用 Docker Compose（web + api + PostgreSQL）部署定義與本機驗收
- [x] 第一版 regime／anomaly model training 與 pre-scored runtime artifact
- [ ] 實際 EC2／IAM Role／HTTPS runtime 驗收

## 已完成：FastAPI backend

- 將 `market-data.js` 改成後端讀取版本化 `market-catalog.json`；黑客松不把只讀行情搬入 PostgreSQL。
- 建立 `/stocks/popular`、`/stocks/search`、`/stocks/{id}/months/{ym}/envelope`、`/reconstructions/validate`、`/reconstructions/complete` API。
- 由後端重算報酬與可信度，前端結果不可作為可信來源。
- 留存側已加入 6 端點（`routers/retention.py`）：`auth/session`、
  `reports/{id}/claim`、`reports/{id}/confirmed-holdings`、`me/dashboard`、
  `me/action-cards/{id}/feedback`、`events/batch`。身份由邀請碼 adapter 發出的
  server-derived session 推導，不再沿用 client 傳入的 `user_id` 作授權邊界；
  anonymous session 與 member 使用不同識別與資料表。舊的未驗證
  `POST /confirmed-holdings` 與 `GET /users/{user_id}/confirmed-holdings` 已移除。
- 將 deterministic calculation、AI narrative 與 API 放在同一個 Python environment，但保持不同 module。

## 已完成：React Frontend Phase

- 使用 React + TypeScript 建立 route 與 feature-based structure。
- 以 strict TypeScript + Zod 建立 typed API client；後續 CI 可再改為 OpenAPI codegen。
- server state 與 wizard draft 分離，避免把 API response 複製成多份 local state。
- 前端只保存尚未送出的表單草稿與畫面狀態。
- 股票搜尋、熱門清單與月份 envelope 全部由 FastAPI 提供。
- 逐檔價格可先呼叫 validate endpoint；最終 complete endpoint 必須再驗證一次。
- Result 完整使用後端 response，不在瀏覽器重算人格、報酬或可信度。
- API failure 時顯示可恢復錯誤，不降級成未驗證的前端結果。

## AI Training Phase

- `apps/ai-training` 與 `apps/api` 使用同一個 Python environment。
- feature definitions 放在 `packages/mindfolio-core`，避免 training-serving skew。
- 先實作不需要個人標籤的 market regime clustering 與 anomaly detector。
- 使用者 persona 先保持 deterministic；有足夠明確回饋後才訓練 ranking／clustering。
- model artifact 必須保存 feature version、training data range、metrics 與 generated_at。
- FastAPI 只載入已核准的 pre-scored JSON，不安裝 sklearn，也不在 request 中重新訓練。

## Phase 2：資料品質

- Rate limit、bot detection、重複輸入 pattern。
- 公司行動日級處理，不只使用月末 factor。
- 支援分批買進、分批賣出與部位權重。
- 提供刪除、撤回與資料匯出。

## Phase 3：CMoney 個人化（留存 P0 已完成）

已完成（依 `13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md`）：

- Time Machine 獲客銜接 Portfolio Radar 留存的 P0 閉環已上線。
- 匿名報告認領、server-derived 身份邊界與 report-scoped confirmed holding
  consent handoff 皆已實作（invite session → report claim → confirmed-holdings）。
- 在 V2 以 `me/dashboard` + action card 重新實作所需的 Moment／Action Card 能力，
  不恢復第二套 V1 runtime。

尚未完成 / roadmap：

- 加入法人、估值、社群與基本面訊號，依持股與使用者偏好產生每週 Portfolio Radar
  （目前 weekly review 為 snapshot/fixture，action card `mute` 尚未影響排序——
  Moment-Engine ranking 為 Feature 006）。
- A/B Test「人格分享」與「挑戰大盤」獲客訊息。
- **Paper-trail 缺口**：留存程式碼直接出貨，`docs/13` §12 承諾的 per-feature SDD
  資料夾 `docs/api/004 member activation`、`005 Portfolio Radar home`、
  `006 market moments`、`007 events/preferences` 尚未建立，仍待補回。

## 三天黑客松切割線

不可砍：前後端分離、FastAPI、300 檔搜尋、價格驗證、月份重建、公司行動調整、confirmed holding 邊界、技術結果頁。

優先砍：真登入、真推播、圖片分享、排行榜、自由聊天、券商串接與多次分批交易。
