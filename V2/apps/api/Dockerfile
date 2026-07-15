FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MINDFOLIO_MARKET_DATA_PATH=/app/data/market-catalog.json \
    MINDFOLIO_MARKET_CONTEXT_PATH=/app/data/market-context-2025-v1.json

WORKDIR /app

# Install only the deterministic core and the API. Tests and the offline
# training package are intentionally excluded from the production image.
COPY packages/mindfolio-core/ ./packages/mindfolio-core/
COPY apps/api/ ./apps/api/
RUN python -m pip install ./packages/mindfolio-core ./apps/api

COPY data/market-catalog.json ./data/market-catalog.json
COPY data/market-context-2025-v1.json ./data/market-context-2025-v1.json

RUN useradd --create-home --uid 10001 mindfolio \
    && chown -R mindfolio:mindfolio /app
USER mindfolio

EXPOSE 8000

CMD ["uvicorn", "mindfolio_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
