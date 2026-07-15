# FastAPI backend

**已實作完成。** 14 支端點都在 `/api/v2`——獲客 6：`health`、
`stocks/popular｜search｜{id}/months/{yyyy_mm}/envelope`、
`reconstructions/validate｜complete`（complete 另回傳 report handle）；留存 6
（`routers/retention.py`，session 驗證）：`auth/session`、`reports/{id}/claim`、
`reports/{id}/confirmed-holdings`（唯一確認持股寫入路徑）、`me/dashboard`、
`me/action-cards/{id}/feedback`、`events/batch`；AI 2（report-owner-only）：
`reports/{id}/ai-report`（結構化 Deep Dive，PostgreSQL cache）、
`reports/{id}/questions`（三個固定 question ID，無自由聊天）。
deterministic 計算在 `packages/mindfolio-core`；AI 敘事（Bedrock + 固定模板
fallback，絕不 raise）在 `ai/`；預先評分市場情境 artifact 由 `MarketContextRepository`
以 checksum 驗證後 fail-soft 讀取（API 不載入 sklearn/joblib）；持股與
reports/feedback/events 走 PostgreSQL（DB 不可用 → 503）。V2 Python suite 77 tests
綠，並對真實 300 檔 catalog 驗證。

> 已移除（安全性）：舊的未驗證 `POST /confirmed-holdings` 與
> `GET /users/{user_id}/confirmed-holdings`（信任 client `user_id` 的跨會員隔離漏洞）
> 已刪除，改由上方 report-scoped 路徑寫入。

分層：`routers/`（HTTP、狀態碼；留存端點經 `auth.py` 的 `require_member` 驗證
session）→ `services/`（orchestration、重新驗證五檔、dashboard 組裝）→
`repositories/`（`market_data` 檔案 catalog、`holdings`／`retention` DB）→
`mindfolio-core`（純計算，不碰 FastAPI）。合約與資料流見
[`V2/docs/09`](../../docs/09_FRONTEND_BACKEND_ARCHITECTURE.md)。

開發環境由 V2 共用 `.venv` 提供，API 與 AI Training 使用相同 Python dependencies
與 `mindfolio-core`。啟動 `make dev-api`（Swagger 在 `/api/v2/docs`）；
測試 `make test` 或 `.venv/bin/python -m pytest apps/api/tests`。
市場資料走檔案 catalog（`MINDFOLIO_MARKET_DATA_PATH`），持股與留存狀態走
`DATABASE_URL`。
