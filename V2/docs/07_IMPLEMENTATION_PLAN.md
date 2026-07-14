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

以上骨架已建立。**正式 MVP API 與金融規則已完成**：8 支端點、deterministic 重建引擎（區間驗證、公司行動還原、人格／分數）、AI 敘事 fallback、確認持股（Postgres），58 tests 綠並對真實 300 檔 catalog 端到端驗證。**尚未完成**：前端 React 與 API 的串接、離線模型訓練（`apps/ai-training` 仍是 scaffold）、AWS/Docker 部署（藍圖見 `11_DEPLOYMENT.md`）。

## Initialization checkpoint

- [x] React + TypeScript + Vite workspace
- [x] Router、Query provider、API health client
- [x] FastAPI application factory、CORS、OpenAPI、health route
- [x] API／Training 共用 `mindfolio-core`
- [x] Offline training package 與無假數據 artifact contract
- [x] Frontend build／test 與 Python test baseline
- [ ] 股票與月份行情 repositories
- [ ] reconstruction／holding API contracts
- [ ] deterministic return／fingerprint services
- [ ] 第一版 regime／anomaly model training
- [ ] PostgreSQL 與 AWS runtime

## 正式 MVP Phase 1：FastAPI backend

- 將 `market-data.js` 改成 PostgreSQL `stock_master` 與 `monthly_price_envelope`。
- 建立 `/stocks/popular`、`/stocks/search`、`/price-envelope`、`/reconstructions/validate`、`/reconstructions/complete` API。
- 由後端重算報酬與可信度，前端結果不可作為可信來源。
- anonymous session 與 member profile 使用不同識別與資料表。
- 將 deterministic calculation、AI narrative 與 API 放在同一個 Python environment，但保持不同 module。

## Frontend Phase

- 使用 React + TypeScript 建立 route 與 feature-based structure。
- 由 FastAPI OpenAPI 產生 typed API client。
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
- FastAPI 只載入已核准 artifact 做 inference，不在 request 中重新訓練。

## Phase 2：資料品質

- Rate limit、bot detection、重複輸入 pattern。
- 公司行動日級處理，不只使用月末 factor。
- 支援分批買進、分批賣出與部位權重。
- 提供刪除、撤回與資料匯出。

## Phase 3：CMoney 個人化

- confirmed holding 接 V1 Moment Engine。
- 加入法人、估值、社群與基本面訊號。
- 依持股與使用者偏好產生每週 Portfolio Radar。
- A/B Test「人格分享」與「挑戰大盤」獲客訊息。

## 三天黑客松切割線

不可砍：前後端分離、FastAPI、300 檔搜尋、價格驗證、月份重建、公司行動調整、confirmed holding 邊界、技術結果頁。

優先砍：真登入、真推播、圖片分享、排行榜、自由聊天、券商串接與多次分批交易。
