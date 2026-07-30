import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.oauth_flow import OAuthFlow
from app.services.token_cache import _decrypt, _encrypt


FLOW_LIFETIME_MINUTES = 10


def save_oauth_flow(
    db: Session,
    state: str,
    flow: dict,
    settings: Settings,
) -> None:
    """Save the large MSAL flow encrypted; only state goes in the cookie."""
    db.add(
        OAuthFlow(
            state=state,
            encrypted_flow=_encrypt(json.dumps(flow), settings),
            expires_at=datetime.now(UTC) + timedelta(minutes=FLOW_LIFETIME_MINUTES),
        )
    )
    db.commit()


def pop_oauth_flow(
    db: Session,
    state: str,
    settings: Settings,
) -> dict | None:
    saved_flow = db.scalar(select(OAuthFlow).where(OAuthFlow.state == state))
    if saved_flow is None:
        return None

    db.delete(saved_flow)
    db.commit()

    expires_at = saved_flow.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        return None

    return json.loads(_decrypt(saved_flow.encrypted_flow, settings))


def delete_user_oauth_flows(db: Session) -> None:
    """Remove unfinished login flows during logout or cleanup."""
    db.execute(delete(OAuthFlow))
    db.commit()
