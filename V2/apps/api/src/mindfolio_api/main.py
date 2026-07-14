from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mindfolio_api.config import get_settings
from mindfolio_api.repositories.holdings import (
    HoldingsRepository,
    build_holdings_repository,
)
from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_api.routers import health, holdings, reconstructions, stocks


def create_app(
    catalog: MarketCatalog | None = None,
    holdings_repo: HoldingsRepository | None = None,
) -> FastAPI:
    settings = get_settings()
    if catalog is None:
        # Fail fast at startup if the market catalog is missing/unreadable.
        catalog = MarketCatalog.from_file(settings.market_data_path)
    if holdings_repo is None:
        # No connection is made here — Postgres is reached lazily per request so
        # a DB outage yields 503, never a startup crash.
        holdings_repo = build_holdings_repository(settings.database_url)

    app = FastAPI(
        title="Mindfolio Time Machine API",
        version="0.1.0",
        openapi_url="/api/v2/openapi.json",
        docs_url="/api/v2/docs",
    )
    app.state.catalog = catalog
    app.state.holdings = holdings_repo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(health.router, prefix="/api/v2")
    app.include_router(stocks.router, prefix="/api/v2")
    app.include_router(reconstructions.router, prefix="/api/v2")
    app.include_router(holdings.router, prefix="/api/v2")
    return app


app = create_app()
