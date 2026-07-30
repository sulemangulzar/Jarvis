import secrets
from typing import cast

import httpx
import msal
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import get_db
from app.models.user import User
from app.services.microsoft_auth import (
    GRAPH_SCOPES,
    build_msal_app,
    get_microsoft_profile,
)
from app.services.token_cache import delete_token_cache, save_token_cache
from app.services.users import save_microsoft_user

router = APIRouter(
    prefix="/auth/microsoft",
    tags=["Microsoft authentication"],
)
session_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def start_login(request: Request, settings: Settings):
    """Create the Microsoft authorization request and redirect the browser."""
    try:
        msal_app = build_msal_app(settings)
        flow = msal_app.initiate_auth_code_flow(
            scopes=GRAPH_SCOPES,
            redirect_uri=settings.microsoft_redirect_uri,
            state=secrets.token_urlsafe(32),
            # Query callback keeps the SameSite=Lax session cookie available
            # during local development. State is still validated by MSAL.
            response_mode="query",
        )
    except requests.exceptions.RequestException as error:
        raise HTTPException(
            status_code=503,
            detail="Microsoft is currently unavailable.",
        ) from error

    if "error" in flow:
        raise HTTPException(
            status_code=502,
            detail="Microsoft could not start authentication.",
        )

    request.session["microsoft_auth_flow"] = flow
    return RedirectResponse(url=flow["auth_uri"], status_code=302)


@router.get("/login", include_in_schema=False)
def login(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    return start_login(request, settings)


async def complete_login(
    request: Request,
    settings: Settings,
    db: Session,
):
    """Exchange Microsoft's response, call Graph, and create the local user."""
    flow = request.session.pop("microsoft_auth_flow", None)
    if flow is None:
        raise HTTPException(
            status_code=400,
            detail="Microsoft login session expired. Start login again.",
        )

    if request.method == "POST":
        response_data = dict(await request.form())
    else:
        response_data = dict(request.query_params)

    try:
        msal_app = build_msal_app(settings)
        result = msal_app.acquire_token_by_auth_code_flow(flow, response_data)
    except requests.exceptions.RequestException as error:
        raise HTTPException(
            status_code=503,
            detail="Microsoft is currently unavailable.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Microsoft returned an invalid authentication response.",
        ) from error

    if "error" in result or not result.get("access_token"):
        raise HTTPException(
            status_code=401,
            detail="Microsoft authentication was not successful.",
        )

    try:
        profile = await get_microsoft_profile(result["access_token"])
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve your Microsoft profile.",
        ) from error

    microsoft_oid = profile.get("id")
    if not microsoft_oid:
        raise HTTPException(
            status_code=502,
            detail="Microsoft returned an incomplete user profile.",
        )

    email = profile.get("mail") or profile.get("userPrincipalName")
    user = save_microsoft_user(
        db=db,
        microsoft_oid=microsoft_oid,
        email=email,
        name=profile.get("displayName"),
    )
    save_token_cache(
        db,
        user.id,
        cast(msal.SerializableTokenCache, msal_app.token_cache),
        settings,
    )
    request.session["user_id"] = user.id

    # The session cookie is the only application credential sent back to the
    # browser. Tokens are never placed in this redirect URL.
    return RedirectResponse(url=settings.frontend_url, status_code=303)


@router.get("/callback", include_in_schema=False)
async def callback_get(
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    return await complete_login(request, settings, db)


@router.post("/callback", include_in_schema=False)
async def callback_post(
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    return await complete_login(request, settings, db)


def user_response(user: User) -> dict:
    return {
        "microsoft_user_id": user.microsoft_oid,
        "display_name": user.name,
        "email": user.email,
    }


@session_router.get("/status")
def authentication_status(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if user_id is None:
        return {"authenticated": False, "user": None}

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": user_response(user),
    }


@router.get("/me")
def current_user(request: Request, db: Session = Depends(get_db)):
    """Keep the earlier /me endpoint as a convenient authenticated check."""
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="You are not logged in")

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="User no longer exists")

    return {"user": user_response(user)}


@session_router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is not None:
        delete_token_cache(db, user_id)
    request.session.clear()
    return {"success": True}
