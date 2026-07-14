from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_core.domain.models import MonthEnvelope, StockSummary

router = APIRouter(tags=["stocks"])

_MONTH_PATTERN = r"^\d{4}-\d{2}$"


def get_catalog(request: Request) -> MarketCatalog:
    return request.app.state.catalog


@router.get("/stocks/popular", response_model=list[StockSummary])
def popular(
    limit: int = Query(default=12, description="Max stocks to return (clamped to 1..100)."),
    catalog: MarketCatalog = Depends(get_catalog),
) -> list[StockSummary]:
    return catalog.popular(limit=limit)


@router.get("/stocks/search", response_model=list[StockSummary])
def search(
    q: str = Query(..., description="Match against stock code, name, or industry."),
    limit: int = Query(default=20, description="Max results (clamped to 1..100)."),
    catalog: MarketCatalog = Depends(get_catalog),
) -> list[StockSummary]:
    return catalog.search(q, limit=limit)


@router.get(
    "/stocks/{stock_id}/months/{yyyy_mm}/envelope",
    response_model=MonthEnvelope,
)
def envelope(
    stock_id: str,
    yyyy_mm: str = Path(pattern=_MONTH_PATTERN, description="Month as YYYY-MM."),
    catalog: MarketCatalog = Depends(get_catalog),
) -> MonthEnvelope:
    result = catalog.envelope(stock_id, yyyy_mm)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No price envelope for stock {stock_id} in {yyyy_mm}.",
        )
    return result
