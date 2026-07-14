from fastapi import APIRouter, Depends, HTTPException, Request

from mindfolio_api.repositories.holdings import HoldingsRepository, HoldingsUnavailable
from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_api.routers.stocks import get_catalog
from mindfolio_api.schemas.reconstruction import ConfirmHoldingsRequest
from mindfolio_api.services.reconstruction import (
    StockNotFound,
    TradeValidationError,
    confirm_holdings,
)
from mindfolio_core.domain.models import ConfirmedHolding

router = APIRouter(tags=["holdings"])


def get_holdings(request: Request) -> HoldingsRepository:
    return request.app.state.holdings


@router.post("/confirmed-holdings", response_model=list[ConfirmedHolding])
def confirm(
    payload: ConfirmHoldingsRequest,
    catalog: MarketCatalog = Depends(get_catalog),
    holdings: HoldingsRepository = Depends(get_holdings),
) -> list[ConfirmedHolding]:
    try:
        return confirm_holdings(catalog, holdings, payload.user_id, payload.trades)
    except StockNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Unknown stock {exc.stock_id}.")
    except TradeValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Trade {exc.index}: {exc.message}")
    except HoldingsUnavailable:
        raise HTTPException(status_code=503, detail="Holdings store is unavailable.")


@router.get("/users/{user_id}/confirmed-holdings", response_model=list[ConfirmedHolding])
def list_confirmed(
    user_id: str,
    holdings: HoldingsRepository = Depends(get_holdings),
) -> list[ConfirmedHolding]:
    try:
        return holdings.list_holdings(user_id)
    except HoldingsUnavailable:
        raise HTTPException(status_code=503, detail="Holdings store is unavailable.")
