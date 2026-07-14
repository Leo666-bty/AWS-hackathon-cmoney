# V2 Local Development

## Requirements

- Node.js 22.13+
- pnpm 11
- Python 3.11+

## Install

```bash
cd V2
cp .env.example .env
make install
```

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

## Verify

```bash
cd V2
make test
make build
.venv/bin/mindfolio-training-status
```

training status 只顯示 feature contract 與預計模型；在真正完成資料切割、訓練與評估前，不會發布模型版本或 metrics。
