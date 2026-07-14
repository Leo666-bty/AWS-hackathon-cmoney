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
make test
make build
.venv/bin/mindfolio-training-status
```

training status 只顯示 feature contract 與預計模型；在真正完成資料切割、訓練與評估前，不會發布模型版本或 metrics。
