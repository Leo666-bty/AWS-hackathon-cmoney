# FastAPI backend

**已實作完成。** 8 支端點都在 `/api/v2`：`health`、
`stocks/popular｜search｜{id}/months/{yyyy_mm}/envelope`、
`reconstructions/validate｜complete`、`confirmed-holdings`（POST + 列表）。
deterministic 計算在 `packages/mindfolio-core`；AI 敘事（Bedrock + 固定模板
fallback，絕不 raise）在 `ai/`；確認持股走 PostgreSQL（`repositories/holdings.py`，
DB 不可用 → 503）。V2 Python suite 58 tests 綠，並對真實 300 檔 catalog 驗證。

分層：`routers/`（HTTP、狀態碼）→ `services/`（orchestration、重新驗證五檔）→
`repositories/`（`market_data` 檔案 catalog、`holdings` DB）→ `mindfolio-core`
（純計算，不碰 FastAPI）。合約與資料流見
[`V2/docs/09`](../../docs/09_FRONTEND_BACKEND_ARCHITECTURE.md)。

開發環境由 V2 共用 `.venv` 提供，API 與 AI Training 使用相同 Python dependencies
與 `mindfolio-core`。啟動 `make dev-api`（Swagger 在 `/api/v2/docs`）；
測試 `make test` 或 `.venv/bin/python -m pytest apps/api/tests`。
市場資料走檔案 catalog（`MINDFOLIO_MARKET_DATA_PATH`），確認持股走 `DATABASE_URL`。
