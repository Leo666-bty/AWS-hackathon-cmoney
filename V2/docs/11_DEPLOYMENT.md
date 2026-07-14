# Deployment (decision record)

> This records the **decision + gotchas** so they aren't re-derived later. The
> actual `Dockerfile` / `docker-compose.yml` are written at deploy time (kept
> out of the repo until then to avoid drifting from the code).

## Target

Single EC2 instance running Docker Compose with two containers. The React
frontend is deployed separately (S3 + CloudFront or equivalent) — it is NOT in
this compose.

```text
EC2 (Docker + Docker Compose)
├── api container      :8000 → host :80/8000 (Security Group opens this only)
│     ├─ DATABASE_URL=postgresql://app:***@postgres:5432/mindfolio   (host = service name)
│     ├─ market-catalog.json baked into the image (COPY at build)
│     └─ Bedrock via the EC2 IAM Role (boto3 auto-detects; no AWS keys in compose)
└── postgres container :5432 (compose-internal only, NOT public)
      ├─ /docker-entrypoint-initdb.d/001_init.sql  (auto-applied on first boot)
      └─ named volume pgdata → EC2 EBS disk
```

## Gotchas (get these right or it won't run)

1. **api → postgres host is the service name `postgres`**, not `localhost`
   (same compose network).
2. **Schema auto-applies**: the official postgres image runs
   `/docker-entrypoint-initdb.d/*.sql` on first init (empty volume). Mount
   `V2/infra/schema/001_init.sql` there — no manual `psql`.
3. **Catalog in the image**: `V2/data/market-catalog.json` is committed; `COPY`
   it in the Dockerfile and point `MINDFOLIO_MARKET_DATA_PATH` at it. Raw CSVs
   are gitignored and not needed in the image.
4. **Bedrock via IAM Role** on the EC2 instance — never put AWS keys in compose.
   DB password comes from a `.env` file (gitignored). Set
   `MINDFOLIO_BEDROCK_ENABLED=true` + `MINDFOLIO_BEDROCK_MODEL_ID` to turn on
   real narrative; unset → deterministic fallback (demo still complete).
5. **Postgres port stays internal** — don't open 5432 in the Security Group.
6. **EBS persistence**: the named volume survives container restart/redeploy and
   EC2 stop/start, but EC2 **terminate** destroys the EBS (unless "delete on
   termination" is off). Don't terminate the demo box.
7. **Ordering**: api `depends_on` postgres with a healthcheck. (Our
   `PgHoldingsRepository` connects lazily per request and returns 503 on
   failure, so a race won't crash the api — but the healthcheck is cleaner.)

## Build notes

- Build context is `V2/` so the image can `pip install` the local packages
  (`packages/mindfolio-core`, `apps/api`) — same as `python-requirements.txt`.
- Base `python:3.11-slim`; run `uvicorn mindfolio_api.main:app --host 0.0.0.0 --port 8000`.
- `market_data_path` default is `./data/market-catalog.json` (relative to WORKDIR).
