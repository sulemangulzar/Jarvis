import asyncio
from typing import Any, cast

from langchain_core.messages import AIMessage

from app.api.v1 import chat as chat_api
from app.core.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models.conversation import ConversationMessage
from app.models.user import User
from app.services import emails, todos
from app.services import graph_client
from app.services.conversations import get_messages
from app.services.graph_client import GraphAPIError
from app.schemas.chat import ChatRequest
from app.agent import to_graph_utc


class FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body or {"value": []}

    def json(self):
        return self._body


class FakeAsyncClient:
    response = FakeResponse()
    current = None
    calls = []

    def __init__(self, **kwargs):
        self.calls = []

    async def __aenter__(self):
        FakeAsyncClient.current = self
        return self

    async def __aexit__(self, *args):
        return None

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return FakeAsyncClient.response


async def run(coroutine):
    return await coroutine


def test_chat_request_validates_browser_timezone():
    request = ChatRequest(message="What is on my calendar?", timezone="America/New_York")
    assert request.timezone == "America/New_York"

    try:
        ChatRequest(message="What is on my calendar?", timezone="not/a-timezone")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected an invalid timezone to be rejected")


def test_calendar_local_time_converts_to_utc_across_dst():
    # March 8, 2026 is after the US DST transition: New York is UTC-4.
    assert to_graph_utc("2026-03-08T10:00:00", "America/New_York") == (
        "2026-03-08T14:00:00"
    )


def test_graph_client_sends_bearer_token_and_selects_data(monkeypatch):
    FakeAsyncClient.response = FakeResponse(200, {"id": "email-1"})
    monkeypatch.setattr(graph_client.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        graph_client.graph_request(
            "GET",
            "/me/messages",
            "server-only-token",
            params={"$top": 1},
        )
    )

    client = FakeAsyncClient.current
    assert client is not None
    method, url, kwargs = client.calls[0]
    assert result == {"id": "email-1"}
    assert method == "GET"
    assert url.endswith("/me/messages")
    assert kwargs["headers"] == {"Authorization": "Bearer server-only-token"}
    assert kwargs["params"] == {"$top": 1}


def test_email_draft_creates_message_and_never_sends(monkeypatch):
    FakeAsyncClient.response = FakeResponse(201, {"id": "draft-1", "isDraft": True})
    monkeypatch.setattr(graph_client.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        emails.create_email_draft(
            "server-only-token",
            "Meeting notes",
            "Please review these notes.",
            ["person@example.com"],
        )
    )

    client = FakeAsyncClient.current
    assert client is not None
    method, url, kwargs = client.calls[0]
    assert result["isDraft"] is True
    assert method == "POST"
    assert url.endswith("/me/messages")
    assert "/send" not in url.lower()
    assert kwargs["json"]["toRecipients"][0]["emailAddress"]["address"] == (
        "person@example.com"
    )


def test_graph_client_hides_upstream_error_details(monkeypatch):
    FakeAsyncClient.response = FakeResponse(500, {"error": {"message": "secret detail"}})
    monkeypatch.setattr(graph_client.httpx, "AsyncClient", FakeAsyncClient)

    try:
        asyncio.run(graph_client.graph_request("GET", "/me/messages", "token"))
    except GraphAPIError as error:
        assert error.status_code == 502
        assert str(error) == "Microsoft Graph could not complete the request"
    else:
        raise AssertionError("Expected GraphAPIError")


def test_todo_operations_use_the_default_list(monkeypatch):
    calls = []

    async def fake_request(method, path, access_token, **kwargs):
        calls.append((method, path, kwargs))
        if path == "/me/todo/lists":
            return {"value": [{"id": "default-list"}]}
        return {"id": "task-1", "title": "Learn Jarvis"}

    monkeypatch.setattr(todos, "graph_request", fake_request)
    result = asyncio.run(todos.create_todo("token", {"title": "Learn Jarvis"}))

    assert result["id"] == "task-1"
    assert calls[1][1] == "/me/todo/lists/default-list/tasks"


def test_chat_saves_user_and_assistant_messages(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(ConversationMessage).delete()
    db.query(User).delete()
    db.commit()
    user = User(microsoft_oid="chat-user", email="chat@example.com", name="Chat User")
    db.add(user)
    db.commit()
    db.refresh(user)

    class FakeRequest:
        session = {"user_id": user.id}

    class FakeAgent:
        async def ainvoke(self, state):
            assert state["messages"][-1].content == "Show my tasks"
            return {"messages": [AIMessage(content="Here are your tasks.")]}

    monkeypatch.setattr(chat_api, "get_saved_access_token", lambda *args: "token")
    monkeypatch.setattr(chat_api, "build_agent", lambda *args: FakeAgent())

    response = asyncio.run(
        chat_api.chat(
            ChatRequest(message="Show my tasks"),
            cast(Any, FakeRequest()),
            db,
            get_settings(),
        )
    )

    saved = get_messages(db, response.conversation_id)
    assert response.message == "Here are your tasks."
    assert [message.role for message in saved] == ["user", "assistant"]
    assert saved[0].content == "Show my tasks"
    assert saved[1].content == "Here are your tasks."
    db.close()
