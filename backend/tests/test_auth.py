import os

# Test configuration is set before importing the application because the app
# validates settings while it is created.
os.environ["APP_ENV"] = "development"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["MICROSOFT_CLIENT_ID"] = "test-client-id"
os.environ["MICROSOFT_CLIENT_SECRET"] = "test-client-secret"
os.environ["MICROSOFT_REDIRECT_URI"] = (
    "http://localhost:8000/auth/microsoft/callback"
)
os.environ["SESSION_SECRET"] = "test-session-secret-that-is-long-enough-123"
os.environ["TOKEN_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.api.v1 import auth
from app.db import Base, SessionLocal, engine
from app.main import app
from app.models.token_cache import MicrosoftTokenCache
from app.models.user import User



class FakeTokenCache:
    has_state_changed = False

    def serialize(self):
        return "{}"


class FakeMsalClient:
    def __init__(self, token_result=None):
        self.token_cache = FakeTokenCache()
        self.token_result = token_result or {
            "access_token": "fake-access-token",
            "id_token_claims": {},
        }

    def initiate_auth_code_flow(self, **kwargs):
        self.state = kwargs["state"]
        return {
            "auth_uri": "https://login.microsoftonline.com/test-login",
            "state": self.state,
        }

    def acquire_token_by_auth_code_flow(self, flow, response_data):
        return self.token_result


@pytest.fixture(autouse=True)
def clear_users():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.execute(delete(MicrosoftTokenCache))
    db.execute(delete(User))
    db.commit()
    db.close()
    yield


def make_client() -> TestClient:
    return TestClient(app)


def start_login(client: TestClient, monkeypatch, token_result=None):
    fake_msal = FakeMsalClient(token_result=token_result)
    monkeypatch.setattr(auth, "build_msal_app", lambda settings: fake_msal)
    response = client.get("/auth/microsoft/login", follow_redirects=False)
    assert response.status_code == 302
    return fake_msal


def test_live_and_ready_health_endpoints():
    with make_client() as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


def test_unauthenticated_status():
    with make_client() as client:
        response = client.get("/auth/status")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False, "user": None}


def test_callback_creates_session_user_and_status(monkeypatch):
    async def fake_graph_profile(access_token):
        assert access_token == "fake-access-token"
        return {
            "id": "microsoft-user-1",
            "displayName": "Ada Lovelace",
            "mail": "ada@example.com",
            "userPrincipalName": "ada@example.com",
        }

    monkeypatch.setattr(auth, "get_microsoft_profile", fake_graph_profile)

    with make_client() as client:
        fake_msal = start_login(client, monkeypatch)
        response = client.post(
            "/auth/microsoft/callback",
            data={"code": "fake-code", "state": fake_msal.state},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "http://localhost:5173"

        status = client.get("/auth/status")

    assert status.status_code == 200
    assert status.json() == {
        "authenticated": True,
        "user": {
            "microsoft_user_id": "microsoft-user-1",
            "display_name": "Ada Lovelace",
            "email": "ada@example.com",
        },
    }

    db = SessionLocal()
    saved_cache = db.query(MicrosoftTokenCache).one()
    assert saved_cache.encrypted_cache != "{}"
    db.close()


def test_logout_clears_session(monkeypatch):
    async def fake_graph_profile(access_token):
        return {
            "id": "microsoft-user-2",
            "displayName": "Grace Hopper",
            "mail": "grace@example.com",
        }

    monkeypatch.setattr(auth, "get_microsoft_profile", fake_graph_profile)

    with make_client() as client:
        fake_msal = start_login(client, monkeypatch)
        client.post(
            "/auth/microsoft/callback",
            data={"code": "fake-code", "state": fake_msal.state},
            follow_redirects=False,
        )
        logout = client.post("/auth/logout")
        status = client.get("/auth/status")

    assert logout.json() == {"success": True}
    assert status.json() == {"authenticated": False, "user": None}


def test_callback_rejects_missing_oauth_flow():
    with make_client() as client:
        response = client.get("/auth/microsoft/callback")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Microsoft login session expired. Start login again."
    )


def test_callback_rejects_failed_msal_result(monkeypatch):
    failed_result = {"error": "invalid_grant"}

    with make_client() as client:
        fake_msal = start_login(client, monkeypatch, token_result=failed_result)
        response = client.post(
            "/auth/microsoft/callback",
            data={"code": "bad-code", "state": fake_msal.state},
            follow_redirects=False,
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Microsoft authentication was not successful."


def test_callback_handles_graph_failure(monkeypatch):
    async def failed_graph_profile(access_token):
        request = httpx.Request("GET", "https://graph.microsoft.com/v1.0/me")
        response = httpx.Response(503, request=request)
        raise httpx.HTTPStatusError("Graph unavailable", request=request, response=response)

    monkeypatch.setattr(auth, "get_microsoft_profile", failed_graph_profile)

    with make_client() as client:
        fake_msal = start_login(client, monkeypatch)
        response = client.post(
            "/auth/microsoft/callback",
            data={"code": "fake-code", "state": fake_msal.state},
            follow_redirects=False,
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Could not retrieve your Microsoft profile."
