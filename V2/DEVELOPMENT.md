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

training status 只顯示 feature contract 與預計模型；在真正完成資料切割、訓練與評估前，不會發布模型版本或 metrics。

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
