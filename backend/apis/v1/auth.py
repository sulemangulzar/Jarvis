from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import decode_token
from models.auth import User
from schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=f"{settings.api_prefix}/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=f"{settings.api_prefix}/auth",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def build_auth_response(access_token: str, user: User) -> AuthResponse:
    return AuthResponse(
        access_token=access_token,
        expires_in=settings.access_token_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if auth_service.find_user_by_email(db, data.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = auth_service.create_user(db, data.email, data.password)
    access_token, refresh_token = auth_service.create_token_pair(db, user)
    set_refresh_cookie(response, refresh_token)
    return build_auth_response(access_token, user)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token, refresh_token = auth_service.create_token_pair(db, user)
    set_refresh_cookie(response, refresh_token)
    return build_auth_response(access_token, user)


@router.post("/refresh", response_model=AuthResponse)
def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
    db: Session = Depends(get_db),
):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Refresh token cookie is missing")

    try:
        payload = decode_token(refresh_token, "refresh")
        user_id = int(payload["sub"])
        token_id = payload["jti"]
    except (ValueError, TypeError, KeyError):
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired") from None

    saved_token = auth_service.find_refresh_token(db, token_id)
    user = db.get(User, user_id)
    if saved_token is None or saved_token.user_id != user_id or user is None:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    access_token, new_refresh_token = auth_service.rotate_refresh_token(
        db, saved_token, user
    )
    set_refresh_cookie(response, new_refresh_token)
    return build_auth_response(access_token, user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
    db: Session = Depends(get_db),
):
    # The refresh token identifies the user even if their access token expired.
    if refresh_token:
        try:
            payload = decode_token(refresh_token, "refresh")
            auth_service.revoke_all_user_tokens(db, int(payload["sub"]))
        except (ValueError, TypeError, KeyError):
            pass

    clear_refresh_cookie(response)
    return MessageResponse(message="Logged out from all sessions")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
