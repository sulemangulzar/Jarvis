import httpx
import msal

from app.core.config import Settings

GRAPH_SCOPES = ["User.Read"]
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"


def build_msal_app(settings: Settings) -> msal.ConfidentialClientApplication:
    """Create the one MSAL client used by the OAuth routes."""
    return msal.ConfidentialClientApplication(
        client_id=settings.microsoft_client_id,
        client_credential=settings.microsoft_client_secret,
        authority=settings.microsoft_authority,
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
