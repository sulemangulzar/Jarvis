import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import get_db
from app.models.user import User
from app.schemas.graph import (
    EmailDraftRequest,
    EventCreateRequest,
    EventUpdateRequest,
    TodoCreateRequest,
    TodoUpdateRequest,
)
from app.services import calendar, emails, todos
from app.services.graph_client import GraphAPIError
from app.services.microsoft_auth import get_saved_access_token

router = APIRouter(tags=["Microsoft Graph"])


def get_graph_access_token(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> str:
    """Require a signed-in user and return a refreshed token to backend code."""
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
    return access_token


def graph_error(error: GraphAPIError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=str(error))


@router.get("/emails")
async def get_emails(
    access_token: str = Depends(get_graph_access_token),
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        return await emails.list_emails(access_token, limit)
    except GraphAPIError as error:
        raise graph_error(error) from error


@router.get("/emails/{email_id}")
async def get_email(
    email_id: str,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        return await emails.get_email(access_token, email_id)
    except GraphAPIError as error:
        raise graph_error(error) from error


@router.post("/emails/drafts", status_code=status.HTTP_201_CREATED)
async def create_email_draft(
    data: EmailDraftRequest,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        return await emails.create_email_draft(
            access_token,
            subject=data.subject,
            body=data.body,
            recipients=data.recipients,
        )
    except GraphAPIError as error:
        raise graph_error(error) from error


@router.get("/events")
async def get_events(
    access_token: str = Depends(get_graph_access_token),
    limit: int = Query(default=50, ge=1, le=100),
):
    try:
        return await calendar.list_events(access_token, limit)
    except GraphAPIError as error:
        raise graph_error(error) from error


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreateRequest,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        return await calendar.create_event(access_token, data.to_graph())
    except GraphAPIError as error:
        raise graph_error(error) from error


@router.patch("/events/{event_id}")
async def update_event(
    event_id: str,
    data: EventUpdateRequest,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        return await calendar.update_event(access_token, event_id, data.to_graph())
    except GraphAPIError as error:
        raise graph_error(error) from error


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        await calendar.delete_event(access_token, event_id)
    except GraphAPIError as error:
        raise graph_error(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/todos")
async def get_todos(
    access_token: str = Depends(get_graph_access_token),
    limit: int = Query(default=50, ge=1, le=100),
):
    try:
        return await todos.list_todos(access_token, limit)
    except (GraphAPIError, ValueError) as error:
        if isinstance(error, GraphAPIError):
            raise graph_error(error) from error
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/todos", status_code=status.HTTP_201_CREATED)
async def create_todo(
    data: TodoCreateRequest,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        return await todos.create_todo(access_token, data.to_graph())
    except (GraphAPIError, ValueError) as error:
        if isinstance(error, GraphAPIError):
            raise graph_error(error) from error
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.patch("/todos/{task_id}")
async def update_todo(
    task_id: str,
    data: TodoUpdateRequest,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        return await todos.update_todo(access_token, task_id, data.to_graph())
    except (GraphAPIError, ValueError) as error:
        if isinstance(error, GraphAPIError):
            raise graph_error(error) from error
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.delete("/todos/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    task_id: str,
    access_token: str = Depends(get_graph_access_token),
):
    try:
        await todos.delete_todo(access_token, task_id)
    except (GraphAPIError, ValueError) as error:
        if isinstance(error, GraphAPIError):
            raise graph_error(error) from error
        raise HTTPException(status_code=502, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
