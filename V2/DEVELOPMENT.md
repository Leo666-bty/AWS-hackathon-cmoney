# V2 Local Development

## Requirements

- Node.js 22.13+
- pnpm 11
- Python 3.11+

## Install

```bash
cd V2
make install
```

只有要使用 Docker Compose 時才需要 `cp .env.example .env`。根目錄 `.env`
主要供 Compose 讀取；`make dev-api` 與 Vite 都不會自動載入它。
本機開發不設定 `DATABASE_URL` 時，確認持股使用記憶體 store（重啟即清空）。
若要讓本機 API 連 PostgreSQL，請自行啟動可從 host 存取的資料庫並在啟動前
匯出正確的 `DATABASE_URL`；Compose 內的主機名 `postgres` 無法直接由 host 解析。

若本機預設 Python 低於 3.11，可明確指定版本：

```bash
make install PYTHON=python3.12
```

## Start

在兩個終端機分別執行：

```bash
cd V2
make dev-api
```

```bash
cd V2
make dev-web
```

- React：`http://localhost:5173`
- FastAPI health：`http://localhost:8000/api/v2/health`
- FastAPI docs：`http://localhost:8000/api/v2/docs`

Vite 會將 `/api` 轉送到 FastAPI，因此前端不需寫死完整 backend URL。
前端預設 API base 是 `/api/v2`；只有刻意跨網域部署時才需要覆寫
`VITE_API_BASE_URL`。

Docker Compose 與 EC2 操作請改看
[`docs/11_DEPLOYMENT.md`](docs/11_DEPLOYMENT.md)，不要把本機雙程序流程當成正式部署。

## Verify

```bash
cd V2
make lint
make test
make build
.venv/bin/mindfolio-training-status
```

封測邀請登入使用 `.env` 的 `MINDFOLIO_INVITE_IDENTITIES`。正式環境還必須設定至少 32 字元的隨機 `MINDFOLIO_SESSION_SECRET`；API 會拒絕使用 development default 啟動 production。

正式 runtime artifact 已發布於 `data/market-context-2025-v1.json`。重新訓練時使用
`apps/ai-training/README.md` 的 pipeline 指令；API request 不執行 training。

## Manual P0 validation

啟動 API 與 Web 後，不重新整理 wizard 頁面，依序操作：

1. 開啟 `http://localhost:5173`，進入 Time Machine。
2. 選五檔股票並完成月份／價格區間與持有關係；至少一檔標記「仍持有」。
3. Result 確認人格、重建報酬與 AI narrative，並看到 AI Deep Dive 解鎖 teaser。
4. 進入 `/activate`，輸入開發邀請碼 `demo-leo`，認領報告並確認至少一檔持股。
5. 進入 `/app`，確認 Portfolio Radar 顯示同一份 report 與本人確認持股。
6. 點擊「產生 AI 深度解讀」，確認 summary、strength、watchout、market moment 與 source badge。
7. 點擊三個固定問題之一，確認前端只送 `question_id`，沒有自由文字欄位。
8. 再次產生同一報告，確認 API 回傳 cache，不建立第二份內容。

DevTools Network 應看到：

```text
POST /api/v2/reconstructions/complete
POST /api/v2/auth/session
POST /api/v2/reports/{report_id}/claim
POST /api/v2/reports/{report_id}/confirmed-holdings
GET  /api/v2/me/dashboard
POST /api/v2/reports/{report_id}/ai-report
POST /api/v2/reports/{report_id}/questions
```

`GET /api/v2/health` 的 `model_status` 應為 `ready`。Bedrock 未啟用時 report
`source` 為 `fallback` 是預期行為，不代表前後端未接通。

## Bedrock narrative

本機或黑客松環境可在 gitignored 的 `V2/.env` 啟用 Bedrock API key：

```dotenv
AWS_REGION=us-east-1
AWS_BEARER_TOKEN_BEDROCK=<rotated-bedrock-api-key>
MINDFOLIO_BEDROCK_ENABLED=true
MINDFOLIO_BEDROCK_MODEL_ID=openai.gpt-oss-120b-1:0
```

`make dev-api` 會由 boto3 自動讀取 `AWS_BEARER_TOKEN_BEDROCK`。若金鑰、網路、模型或輸出 schema 發生問題，API 仍會回傳 deterministic fallback，不中斷重建流程。

正式 AWS 環境不要配置 API key；改由 EC2／ECS Task IAM Role 授權 `bedrock:InvokeModel`，其餘設定不變。
