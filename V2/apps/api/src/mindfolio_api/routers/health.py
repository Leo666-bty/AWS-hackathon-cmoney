from fastapi import APIRouter
from pydantic import BaseModel

from mindfolio_api import __version__
from mindfolio_api.config import get_settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_status: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="mindfolio-api",
        version=__version__,
        model_status=settings.model_status,
    )
