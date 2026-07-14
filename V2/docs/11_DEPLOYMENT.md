# Deployment — Single EC2 with Docker Compose

> The deployment target is deliberately small: one EC2 instance, one Docker
> Compose project, and three containers. No separate frontend hosting, managed
> database, custom VPC design, queue, or service mesh is required for the demo.

## Topology

```text
Internet
  │
  ▼ :80
EC2 instance (Docker Compose)
├── web       nginx :80
│   ├── serves the React/Vite static build
│   └── proxies /api/* → http://api:8000/api/*
├── api       FastAPI/Uvicorn :8000
│   ├── market-catalog.json baked into the image
│   ├── DATABASE_URL → postgres:5432
│   └── optional Bedrock access through the EC2 IAM Role
└── postgres  PostgreSQL 16 :5432 (Compose network only)
    ├── 001_init.sql runs on the first empty-volume startup
    └── pgdata named volume persists on the EC2 EBS disk
```

Public ingress is normally only port 80. Port 8000 is mapped by the supplied
Compose file for direct Swagger/API debugging and can be removed after
verification. PostgreSQL port 5432 is never published.

## Files

- `apps/api/Dockerfile` — Python 3.11 image containing only `mindfolio-core`,
  the API, and `data/market-catalog.json`.
- `apps/web/Dockerfile` — pnpm/Vite build stage followed by nginx.
- `apps/web/nginx.conf` — SPA fallback plus `/api` reverse proxy.
- `docker-compose.yml` — web, api, PostgreSQL, health checks, and `pgdata`.
- `.dockerignore` — keeps virtual environments, dependencies, tests, raw CSVs,
  local secrets, and development artifacts out of the build context.

## EC2 preparation

Install Docker Engine with the Compose plugin, clone the repository, then work
from `V2/`:

```bash
cd V2
cp .env.example .env
```

Before starting the stack, replace `change-this-before-deploy` in `DB_PASSWORD`
with a long random password. Compose constructs the API container's
`DATABASE_URL` from that value, so `DB_PASSWORD` is the deployment authority.
The `DATABASE_URL` line in `.env.example` is only a container-network reference;
Compose does not inject that line into the API service. If you manually use it
from a process attached to the Compose network, update its password too.

Do not commit `.env`. AWS access keys do not belong in this file either.

## Start and inspect

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f api web postgres
```

The dependency order is health-based:

1. PostgreSQL starts and passes `pg_isready`.
2. FastAPI starts, loads the catalog, and passes `/api/v2/health`.
3. nginx starts and exposes the web application on port 80.

Useful URLs:

- Web: `http://EC2_PUBLIC_IP/`
- Health through nginx: `http://EC2_PUBLIC_IP/api/v2/health`
- Swagger through nginx: `http://EC2_PUBLIC_IP/api/v2/docs`
- Optional direct API: `http://EC2_PUBLIC_IP:8000/api/v2/health`

## Minimal security group

No custom network architecture is needed. The EC2 security group only needs:

- TCP 22 from the operator's IP for SSH.
- TCP 80 from the intended demo audience.
- TCP 8000 only while direct API debugging is desired; otherwise omit it.

Never add an inbound rule for 5432. The API reaches PostgreSQL by the Compose
service name `postgres` on the internal network.

## Acceptance checks

### 1. Health and nginx proxy

```bash
curl -fsS http://127.0.0.1/api/v2/health
curl -fsS http://127.0.0.1:8000/api/v2/health
```

Both should return HTTP 200 and the same JSON health response. The first call
proves nginx can reach the API container.

### 2. Five-stock reconstruction

January is a normal band-enabled month for all five stocks in this fixture.

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

The response must contain `result.persona_code`, `result.average_return`,
`result.scores`, and `narrative`. With Bedrock disabled, `narrative` is the
deterministic fallback and the core flow remains complete.

### 3. Confirmed-holding persistence

Use the same five trades after explicit user consent:

```bash
curl -fsS -X POST http://127.0.0.1/api/v2/confirmed-holdings \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id":"deploy-smoke-user",
    "trades": [
      {"stock_id":"2330","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2317","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2344","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2408","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"},
      {"stock_id":"2603","relation":"holding","buy_month":"01","buy_mode":"band","buy_band":"mid"}
    ]
  }'

docker compose restart postgres
docker compose ps

curl -fsS --retry 12 --retry-delay 2 --retry-all-errors \
  http://127.0.0.1/api/v2/users/deploy-smoke-user/confirmed-holdings
```

After PostgreSQL becomes healthy again, the GET response must still contain the
five rows. This proves persistence is backed by the `pgdata` volume rather than
container storage.

## Bedrock (optional)

The default is deliberately offline-safe:

```dotenv
MINDFOLIO_BEDROCK_ENABLED=false
MINDFOLIO_BEDROCK_MODEL_ID=
AWS_REGION=ap-northeast-1
```

To enable a real narrative provider, attach an EC2 IAM Role with the minimum
required Bedrock inference permission and set:

```dotenv
MINDFOLIO_BEDROCK_ENABLED=true
MINDFOLIO_BEDROCK_MODEL_ID=your-model-id
```

Never put AWS access keys in Compose or `.env`. The SDK discovers the EC2 IAM
Role automatically. Provider failure must still fall back to deterministic
copy and never block reconstruction.

## Operations

Rebuild after pulling changes:

```bash
git pull
docker compose up -d --build
```

Inspect state without exposing PostgreSQL:

```bash
docker compose exec postgres \
  psql -U app -d mindfolio -c 'TABLE confirmed_holdings;'
```

Stop containers while preserving data:

```bash
docker compose down
```

Do not use `docker compose down -v` unless confirmed holdings are intentionally
being deleted. Back up the named volume before replacing or terminating the EC2
instance.

## Gotchas

1. **Use `postgres`, not `localhost`, in the API database URL.** Containers
   resolve one another by Compose service name.
2. **The schema runs only on first initialization.** Files in
   `/docker-entrypoint-initdb.d/` are applied only when `pgdata` is empty.
   Later schema changes need an explicit migration.
3. **The catalog is baked into the API image.** The build context is `V2/`, and
   `MINDFOLIO_MARKET_DATA_PATH=/app/data/market-catalog.json`.
4. **Raw organizer CSVs and PDFs never enter the image.** `.dockerignore`
   permits only the built `data/market-catalog.json` snapshot.
5. **The web build uses a relative `/api/v2` base URL.** nginx preserves the
   request path while proxying `/api/*` to the API container.
6. **PostgreSQL is internal only.** Do not publish 5432 or open it in the EC2
   security group.
7. **The volume lives on EC2 storage.** It survives container recreation,
   Compose restart, and normal EC2 stop/start, but EC2 termination can destroy
   the underlying EBS volume depending on its delete-on-termination setting.
8. **Bedrock uses the EC2 IAM Role.** `MINDFOLIO_BEDROCK_ENABLED=false` is the
   safe default and requires no AWS model access.
9. **The React vertical slice is connected.** Landing, stock selection,
   reconstruction, result and consent all use `/api/v2` through nginx. The
   remaining product gap is identity: confirmed holdings still use the fixed
   Demo user `LEO`; registration/report claim/Portfolio Radar are later work.
10. **Root `.env` is not a Vite build input.** The production image intentionally
    builds with the client's default relative `/api/v2`; do not bake
    `http://localhost:8000` into an `apps/web/.env*` file.
