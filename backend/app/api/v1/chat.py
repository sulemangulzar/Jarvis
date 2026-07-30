import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.agent import build_agent
from app.core.config import Settings, get_settings
from app.db import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversations import (
    get_messages,
    get_or_create_conversation,
    save_message,
)
from app.services.microsoft_auth import get_saved_access_token

router = APIRouter(tags=["Chat"])


def message_content(message) -> str:
    """Convert an LLM message into text that is safe to save and return."""
    content = message.content
    if isinstance(content, str):
        return content
    return str(content)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user_id = request.session.get("user_id")
    if user_id is None or db.get(User, user_id) is None:
        raise HTTPException(status_code=401, detail="You must sign in first")

    try:
        access_token = get_saved_access_token(db, user_id, settings)
    except (ValueError, requests.exceptions.RequestException) as error:
        raise HTTPException(
            status_code=401,
            detail="Microsoft authentication needs to be completed again",
        ) from error

    if access_token is None:
        raise HTTPException(
            status_code=401,
            detail="Microsoft authentication needs to be completed again",
        )

    try:
        conversation = get_or_create_conversation(
            db, user_id, data.conversation_id
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Conversation not found") from error

    history = []
    for saved_message in get_messages(db, conversation.id):
        if saved_message.role == "user":
            history.append(HumanMessage(content=saved_message.content))
        elif saved_message.role == "assistant":
            history.append(AIMessage(content=saved_message.content))

    save_message(db, conversation.id, "user", data.message)
    history.append(HumanMessage(content=data.message))

    try:
        agent = build_agent(access_token, settings)
        result = await agent.ainvoke({"messages": history})
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Jarvis could not complete that request.",
        ) from error

    messages = result.get("messages", [])
    assistant_messages = [
        message
        for message in messages
        if isinstance(message, AIMessage) and message.content
    ]
    if not assistant_messages:
        raise HTTPException(
            status_code=502,
            detail="Jarvis did not return a response.",
        )

    response_text = message_content(assistant_messages[-1])
    save_message(db, conversation.id, "assistant", response_text)

    return ChatResponse(
        conversation_id=conversation.id,
        message=response_text,
    )
