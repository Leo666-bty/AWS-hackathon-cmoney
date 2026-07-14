from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mindfolio_api.config import get_settings
from mindfolio_api.routers import health


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Mindfolio Time Machine API",
        version="0.1.0",
        openapi_url="/api/v2/openapi.json",
        docs_url="/api/v2/docs",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(health.router, prefix="/api/v2")
    return app


app = create_app()
