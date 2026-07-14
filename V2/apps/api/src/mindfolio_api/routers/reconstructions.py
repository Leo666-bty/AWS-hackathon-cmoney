from fastapi import APIRouter, Depends, HTTPException, Request

from mindfolio_api.ai.narrative import generate_narrative
from mindfolio_api.config import get_settings
from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_api.routers.stocks import get_catalog
from mindfolio_api.schemas.reconstruction import (
    CompleteRequest,
    CompleteResponse,
    TradeConfig,
)
from mindfolio_api.services.reconstruction import (
    MonthNotFound,
    StockNotFound,
    TradeValidationError,
    complete_reconstruction,
    validate_buy,
)
from mindfolio_core.domain.models import PriceValidation

router = APIRouter(tags=["reconstructions"])


@router.post("/reconstructions/validate", response_model=PriceValidation)
def validate(
    config: TradeConfig,
    catalog: MarketCatalog = Depends(get_catalog),
) -> PriceValidation:
    try:
        return validate_buy(catalog, config)
    except StockNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Unknown stock {exc.stock_id}.")
    except MonthNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail=f"No data for stock {exc.stock_id} in month {exc.month}.",
        )


@router.post("/reconstructions/complete", response_model=CompleteResponse)
def complete(
    payload: CompleteRequest,
    request: Request,
    catalog: MarketCatalog = Depends(get_catalog),
) -> CompleteResponse:
    try:
        result = complete_reconstruction(catalog, payload.trades)
    except StockNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Unknown stock {exc.stock_id}.")
    except TradeValidationError as exc:
        raise HTTPException(
            status_code=422, detail=f"Trade {exc.index}: {exc.message}"
        )

    # Bedrock disabled by default → deterministic fallback narrative (demo-safe).
    narrative = generate_narrative(
        result,
        client=request.app.state.bedrock_client,
        settings=get_settings(),
    )
    return CompleteResponse(result=result, narrative=narrative)
