import logging
from typing import Any

import httpx

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
logger = logging.getLogger(__name__)


class GraphAPIError(Exception):
    """An expected error from Microsoft Graph."""

    def __init__(self, status_code: int, message: str, error_code: str | None = None):
        self.status_code = status_code
        self.error_code = error_code
        detail = f"{message} ({error_code})" if error_code else message
        super().__init__(detail)


async def graph_request(
    method: str,
    path: str,
    access_token: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
) -> Any:
    """Make one authenticated Graph request without exposing its token."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_BASE_URL}{path}"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
            )
    except httpx.RequestError as error:
        raise GraphAPIError(503, "Microsoft Graph is currently unavailable") from error

    if response.status_code >= 400:
        error_code = None
        try:
            error_body = response.json().get("error", {})
            error_code = error_body.get("code")
        except (AttributeError, ValueError):
            pass

        logger.warning(
            "Microsoft Graph request failed: method=%s path=%s status=%s code=%s",
            method,
            path,
            response.status_code,
            error_code,
        )

        if response.status_code == 401:
            raise GraphAPIError(401, "Microsoft authentication has expired", error_code)
        if response.status_code == 403:
            raise GraphAPIError(
                403,
                "Microsoft denied this operation. Re-consent to the required Graph permission.",
                error_code,
            )
        if response.status_code == 404:
            raise GraphAPIError(404, "The requested Microsoft item was not found", error_code)
        if response.status_code == 400:
            raise GraphAPIError(400, "Microsoft rejected the request data", error_code)
        raise GraphAPIError(502, "Microsoft Graph could not complete the request", error_code)

    if response.status_code == 204:
        return None

    try:
        return response.json()
    except ValueError as error:
        raise GraphAPIError(502, "Microsoft Graph returned an invalid response") from error
