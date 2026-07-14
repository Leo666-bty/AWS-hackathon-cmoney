"""Holdings dependency.

The legacy unauthenticated `POST /confirmed-holdings` and
`GET /users/{user_id}/confirmed-holdings` routes were removed: they trusted a
client-supplied `user_id` and bypassed the report-claim consent gate (a
cross-member isolation hole). Confirmed holdings are now written only through
the authenticated report-scoped flow in `routers/retention.py`. This module
keeps just the shared repository dependency.
"""

from fastapi import Request

from mindfolio_api.repositories.holdings import HoldingsRepository


def get_holdings(request: Request) -> HoldingsRepository:
    return request.app.state.holdings
