from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from mindfolio_api.auth import (
    MemberIdentity,
    authenticate_invite_code,
    issue_session_token,
    optional_member,
    require_member,
)
from mindfolio_api.repositories.holdings import HoldingsRepository, HoldingsUnavailable
from mindfolio_api.repositories.market_data import MarketCatalog
from mindfolio_api.repositories.retention import (
    InvalidClaimToken,
    ReportClaimConflict,
    ReportExpired,
    ReportNotFound,
    RetentionRepository,
    RetentionUnavailable,
)
from mindfolio_api.routers.holdings import get_holdings
from mindfolio_api.routers.stocks import get_catalog
from mindfolio_api.schemas.reconstruction import TradeConfig
from mindfolio_api.schemas.retention import (
    CardFeedbackRequest,
    CardFeedbackResponse,
    ClaimReportRequest,
    ClaimReportResponse,
    ConfirmReportHoldingsRequest,
    EventBatchRequest,
    EventBatchResponse,
    MemberDashboard,
    SessionRequest,
    SessionResponse,
)
from mindfolio_api.services.reconstruction import complete_reconstruction
from mindfolio_api.services.retention import build_action_card, build_dashboard
from mindfolio_core.domain.models import ConfirmedHolding

router = APIRouter(tags=["retention"])


def get_retention(request: Request) -> RetentionRepository:
    return request.app.state.retention


@router.post("/auth/session", response_model=SessionResponse)
def create_session(payload: SessionRequest) -> SessionResponse:
    identity = authenticate_invite_code(payload.invite_code)
    if identity is None:
        raise HTTPException(status_code=401, detail="Invalid invite code.")
    return SessionResponse(
        access_token=issue_session_token(identity),
        member_id=identity.member_id,
        display_name=identity.display_name,
    )


@router.post("/reports/{report_id}/claim", response_model=ClaimReportResponse)
def claim_report(
    report_id: str,
    payload: ClaimReportRequest,
    identity: MemberIdentity = Depends(require_member),
    retention: RetentionRepository = Depends(get_retention),
) -> ClaimReportResponse:
    try:
        report = retention.claim_report(report_id, payload.claim_token, identity.member_id)
    except ReportNotFound:
        raise HTTPException(status_code=404, detail="Report not found.")
    except InvalidClaimToken:
        raise HTTPException(status_code=403, detail="Invalid report claim token.")
    except ReportExpired:
        raise HTTPException(status_code=410, detail="Report claim has expired.")
    except ReportClaimConflict:
        raise HTTPException(status_code=409, detail="Report has already been claimed.")
    except RetentionUnavailable:
        raise HTTPException(status_code=503, detail="Report store is unavailable.")
    return ClaimReportResponse(
        report_id=report_id,
        member_id=identity.member_id,
        claimed_at=report["claimed_at"],
        holding_candidates=report["result"]["holding_candidates"],
    )


@router.post("/reports/{report_id}/confirmed-holdings")
def confirm_report_holdings(
    report_id: str,
    payload: ConfirmReportHoldingsRequest,
    identity: MemberIdentity = Depends(require_member),
    retention: RetentionRepository = Depends(get_retention),
    holdings: HoldingsRepository = Depends(get_holdings),
    catalog: MarketCatalog = Depends(get_catalog),
) -> list[ConfirmedHolding]:
    try:
        report = retention.get_member_report(identity.member_id, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Claimed report not found.")
        configs = [TradeConfig.model_validate(item) for item in report["trades"]]
        verified = complete_reconstruction(catalog, configs)
        allowed = set(verified.holding_candidates)
        selected = list(dict.fromkeys(payload.stock_ids))
        if not set(selected).issubset(allowed):
            raise HTTPException(status_code=422, detail="One or more stocks are not verified holding candidates.")
        return holdings.add_holdings(identity.member_id, selected, source_report_id=report_id)
    except RetentionUnavailable:
        raise HTTPException(status_code=503, detail="Report store is unavailable.")
    except HoldingsUnavailable:
        raise HTTPException(status_code=503, detail="Holdings store is unavailable.")


@router.get("/me/dashboard", response_model=MemberDashboard)
def member_dashboard(
    identity: MemberIdentity = Depends(require_member),
    retention: RetentionRepository = Depends(get_retention),
    holdings: HoldingsRepository = Depends(get_holdings),
    catalog: MarketCatalog = Depends(get_catalog),
) -> MemberDashboard:
    try:
        report = retention.get_member_report(identity.member_id)
        confirmed = holdings.list_holdings(identity.member_id)
        preference = None
        if confirmed:
            card = build_action_card(catalog, confirmed[0], None)
            preference = retention.get_feedback(identity.member_id, card.card_id)
        return build_dashboard(
            member_id=identity.member_id,
            display_name=identity.display_name,
            report=report,
            holdings=confirmed,
            catalog=catalog,
            feedback=preference,
        )
    except (RetentionUnavailable, HoldingsUnavailable):
        raise HTTPException(status_code=503, detail="Portfolio Radar is temporarily unavailable.")


@router.post("/me/action-cards/{card_id}/feedback", response_model=CardFeedbackResponse)
def card_feedback(
    card_id: str,
    payload: CardFeedbackRequest,
    identity: MemberIdentity = Depends(require_member),
    retention: RetentionRepository = Depends(get_retention),
) -> CardFeedbackResponse:
    try:
        saved_at = retention.save_feedback(identity.member_id, card_id, payload.preference)
    except RetentionUnavailable:
        raise HTTPException(status_code=503, detail="Feedback store is unavailable.")
    return CardFeedbackResponse(card_id=card_id, preference=payload.preference, saved_at=saved_at)


@router.post("/events/batch", response_model=EventBatchResponse)
def batch_events(
    payload: EventBatchRequest,
    identity: MemberIdentity | None = Depends(optional_member),
    retention: RetentionRepository = Depends(get_retention),
) -> EventBatchResponse:
    try:
        accepted = retention.add_events(identity.member_id if identity else None, payload.events)
    except RetentionUnavailable:
        raise HTTPException(status_code=503, detail="Event store is unavailable.")
    return EventBatchResponse(accepted_event_ids=accepted)
