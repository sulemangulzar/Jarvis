import httpx
import msal
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services.token_cache import load_token_cache, save_token_cache

GRAPH_SCOPES = [
    "User.Read",
    "Mail.ReadWrite",
    "Calendars.ReadWrite",
    "Tasks.ReadWrite",
]
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"


def build_msal_app(
    settings: Settings,
    token_cache: msal.SerializableTokenCache | None = None,
) -> msal.ConfidentialClientApplication:
    """Create the MSAL client, optionally with a user's saved cache."""
    # A serializable cache is required so it can be encrypted and saved in Neon.
    cache = token_cache if token_cache is not None else msal.SerializableTokenCache()
    return msal.ConfidentialClientApplication(
        client_id=settings.microsoft_client_id,
        client_credential=settings.microsoft_client_secret,
        authority=settings.microsoft_authority,
        token_cache=cache,
    )


async def get_microsoft_profile(access_token: str) -> dict:
    """Get the small set of user fields needed by Jarvis from Microsoft Graph."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "$select": "id,displayName,mail,userPrincipalName",
    }

    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(GRAPH_ME_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


def get_saved_access_token(
    db: Session,
    user_id: int,
    settings: Settings,
) -> str | None:
    """Load and refresh a user's Microsoft access token from the encrypted cache."""
    cache = load_token_cache(db, user_id, settings)
    if cache is None:
        return None

    msal_app = build_msal_app(settings, token_cache=cache)
    accounts = msal_app.get_accounts()
    if not accounts:
        return None

    result = msal_app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])
    access_token = result.get("access_token") if result else None

    if cache.has_state_changed:
        save_token_cache(db, user_id, cache, settings)

    return access_token
