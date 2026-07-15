# Deployment — Single EC2 with Docker Compose

## 1. Deployment decision

P0／黑客松採單一 EC2 執行三個 Docker Compose services：React/nginx、
FastAPI/Uvicorn、PostgreSQL 16。這是低維運成本、可重現的展示架構，不是
高流量正式環境的最終拓撲。

```text
Internet
  │
  ▼ :80 / :443（TLS 由 ALB、CloudFront 或外部 reverse proxy 終止）
EC2 — Docker Compose
├── web       nginx :80
│   ├── React/Vite static assets
│   ├── SPA fallback
│   └── /api/* → http://api:8000/api/*
├── api       FastAPI/Uvicorn :8000
│   ├── market-catalog.json + market-context-2025-v1.json baked into image
│   ├── DATABASE_URL → postgres:5432
│   ├── retention/session services
│   └── Bedrock：黑客松 workshop 帳號不開 IAM Role，實際以短期 API key
│       （`AWS_BEARER_TOKEN_BEDROCK`，~12h 過期需重產）授權並已實測 live；
│       正式環境改 EC2 IAM Role。失敗時 deterministic fallback
└── postgres  PostgreSQL 16 :5432（Compose internal only）
    ├── ordered SQL files only on first empty-volume initialization
    └── pgdata named volume on EC2 EBS
```

## 2. Versioned deployment assets

- `V2/.dockerignore`
- `V2/apps/api/Dockerfile`
- `V2/apps/web/Dockerfile`
- `V2/apps/web/nginx.conf`
- `V2/docker-compose.yml`
- `V2/infra/schema/001_init.sql`
- `V2/infra/schema/002_ai_report_cache.sql`

Build context 必須是 `V2/`，讓 API image 能安裝本地
`packages/mindfolio-core` 與 `apps/api`，並只複製版本化的
`data/market-catalog.json` 與 `data/market-context-2025-v1.json`。

## 3. Recommended EC2 baseline

黑客松完整一體機建議：

- EC2：`t3.xlarge`（4 vCPU／16 GiB）
- EBS：50 GiB `gp3`
- OS：Amazon Linux 2023 或 Ubuntu 24.04
- Docker Engine + Compose plugin
- 4 GiB swap 作為異常尖峰保護，不取代實體記憶體

`t3.xlarge` 足以同時運行 Web、API、PostgreSQL、模型 inference 與小型
離線 KMeans／IsolationForest training；training 應在離峰執行。若平均 CPU
長期超過 40–50%、CPU credits 持續下降或公開流量成長，改用 M 系列或拆出
RDS。

## 4. Environment contract

在 `V2/` 建立 gitignored `.env`：

```dotenv
DB_PASSWORD=<random-database-password>
DATABASE_URL=postgresql://app:<same-password>@postgres:5432/mindfolio

MINDFOLIO_ENV=production
MINDFOLIO_CORS_ORIGINS=https://your-domain.example
MINDFOLIO_MARKET_DATA_PATH=/app/data/market-catalog.json
MINDFOLIO_MARKET_CONTEXT_PATH=/app/data/market-context-2025-v1.json

MINDFOLIO_INVITE_IDENTITIES=<high-entropy-invite-code>:LEO
MINDFOLIO_REPORT_TTL_HOURS=72
MINDFOLIO_SESSION_SECRET=<at-least-32-random-characters>
MINDFOLIO_SESSION_TTL_HOURS=24

AWS_REGION=us-east-1
MINDFOLIO_BEDROCK_ENABLED=true
MINDFOLIO_BEDROCK_MODEL_ID=openai.gpt-oss-120b-1:0

WEB_PORT=80
API_PORT=8000
```

Rules：

1. `MINDFOLIO_SESSION_SECRET` 在 production 必須至少 32 字元；預設開發值會
   讓 API fail fast。
2. Invite code 是 P0 小批次 identity adapter，不是正式 CMoney SSO。
3. 正式 EC2 使用 IAM Role，不在 `.env` 放 AWS access key 或 bearer token。
4. 本機封閉式驗證可暫時使用 `AWS_BEARER_TOKEN_BEDROCK`，但不得提交。
5. Compose 以 `DB_PASSWORD` 建立 PostgreSQL 與 API `DATABASE_URL`；兩者必須
   一致。
6. `.env.example` 只提供欄位與假值，不得含可使用的 secrets。

## 5. IAM and Bedrock

EC2 instance profile 只授予指定 model／inference profile 所需的最小
Bedrock Runtime 權限。SDK 由 instance metadata 自動取得臨時憑證。

```dotenv
MINDFOLIO_BEDROCK_ENABLED=false
```

是預設安全模式。關閉、timeout、schema invalid、guardrail hit 或 IAM 失敗時，
API 必須回傳 deterministic narrative，不得阻斷 reconstruction 或 Portfolio
Radar。

Health endpoint 只回報設定狀態，不發出付費 Bedrock request。

## 6. Launch

```bash
cd V2
cp .env.example .env
# Replace every placeholder and align production origins/secrets.

docker compose config
docker compose build
docker compose up -d
docker compose ps
```

啟動順序由 health checks 控制：

1. PostgreSQL 通過 `pg_isready`。
2. FastAPI 載入 market catalog、pre-scored market context、repositories 與 retention services，通過
   `/api/v2/health`。
3. nginx 啟動並提供 React 與 `/api` reverse proxy。

## 7. Network and TLS

Security Group 最小規則：

- TCP 22：僅 operator IP。
- TCP 80／443：Demo audience 或公開流量。
- TCP 8000：僅暫時 Swagger/debug；完成驗證後關閉並移除 Compose port map。
- TCP 5432：永遠不對外開放。

Included nginx 只處理容器內 HTTP。公開部署必須在 ALB、CloudFront 或外部
reverse proxy 終止 TLS，並把 `MINDFOLIO_CORS_ORIGINS` 設成正式 HTTPS
origin。

## 8. Acceptance checks

### 8.1 Health and proxy

```bash
curl -fsS http://127.0.0.1/api/v2/health
curl -fsS http://127.0.0.1:8000/api/v2/health
```

兩者應回 HTTP 200；第一個證明 nginx → API container path 正常。

### 8.2 Five-stock reconstruction

```bash
curl -fsS -X POST http://127.0.0.1/api/v2/reconstructions/complete \
  -H 'Content-Type: application/json' \
  -d '{
    "trades": [
      {"stock_id":"2330","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2317","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2344","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2408","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2603","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"}
    ]
  }'
```

Response 必須包含 `report_id`、`result.persona_code`、
`result.average_return`、`result.scores` 與 `narrative`。

### 8.3 Member activation and Portfolio Radar

1. 以 `MINDFOLIO_INVITE_IDENTITIES` 中的 invite code 呼叫 activation endpoint。
2. 使用回傳 session token 認領 `report_id`。
3. 明確 consent 後建立 confirmed holdings。
4. 呼叫 member dashboard，確認 fingerprint、portfolio、priority Action Card 與
   weekly review modules 可讀。
5. 產生 AI Deep Dive 並點擊固定問題 chips，確認 evidence refs 與 fallback source。
6. 重送相同 AI report request，確認 cache 生效；重送 claim／event request 不產生重複資料。

正式 endpoint 與 payload 以 FastAPI `/api/v2/docs` 為準，不在部署腳本複製
可能漂移的 token 或 identity contract。

### 8.4 Persistence

```bash
docker compose restart postgres
docker compose ps
```

PostgreSQL 恢復 healthy 後，claimed report、confirmed holdings、retention state
與 events 必須仍存在，證明資料位於 `pgdata` 而非 container writable layer。

## 9. Schema and migration policy

`/docker-entrypoint-initdb.d/*.sql` 只會在 `pgdata` 為空時依序執行。新增
`002_ai_report_cache.sql` 不會自動更新既有 volume；既有環境必須手動套用 migration。

在第一個持久環境建立後：

- 新增有序 migration，不覆寫既有 schema history。
- 部署前備份 `pgdata`／PostgreSQL。
- migration 與 application image 同版驗證。
- 失敗時停止 rollout，不用 `docker compose down -v` 解決。

## 10. Operations

更新版本：

```bash
git pull --ff-only
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=200 api web postgres
```

停止服務但保留資料：

```bash
docker compose down
```

除非明確要刪除所有資料，不可執行：

```bash
docker compose down -v
```

EC2 terminate 可能連同 EBS 刪除；正式 Demo 前要確認 delete-on-termination
設定並完成備份。

## 11. Observability

至少監控：

- EC2 `CPUUtilization`、`CPUCreditBalance`、`CPUSurplusCreditBalance`
- memory、swap、disk usage
- EBS latency／queue
- API p95 latency、5xx、Bedrock fallback rate
- PostgreSQL connections、storage、restart count
- activation、claim、confirmed holding、Portfolio Radar open 的漏斗事件

Log 不得包含 session secret、invite code、Authorization、完整 prompt、精確交易
價格或資料庫密碼。

## 12. Trade-offs and scale-out path

### Advantages

- 單一 deploy command，環境容易重現。
- Web/API same-origin，CORS 與 cookie/token 邊界較簡單。
- PostgreSQL 不公開，資料保留在 EBS-backed volume。
- Bedrock 與自訓模型皆有 deterministic fallback，Demo 不依賴外部成功。
- 成本與維運面適合黑客松及小批次邀請測試。

### Limitations

- EC2、API、DB 共用單一 failure domain。
- Training、build 與線上 traffic 競爭 CPU／RAM。
- Schema migration、backup、TLS 與部署切換仍需人工操作。
- 無 rolling deploy、horizontal scaling 或 managed database HA。

### Production evolution

```text
CloudFront + S3       → React static assets
ALB + ECS/App Runner  → FastAPI
RDS PostgreSQL        → reports, portfolio, retention and events
S3                    → model artifacts and immutable exports
Secrets Manager       → runtime secrets
CMoney SSO            → production identity
Bedrock               → narrative inference
```

單機 P0 驗證 activation-to-retention loop 後，再依實測 CPU、DB、流量與可用性
需求拆分；不在黑客松前預先引入不必要的基礎設施。
