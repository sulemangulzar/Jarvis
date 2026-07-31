import json
from datetime import UTC, datetime
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.messages import SystemMessage
from pydantic import SecretStr
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import Settings
from app.services import calendar, emails, todos
from app.services.graph_client import GraphAPIError

def to_graph_utc(value: str, timezone_name: str) -> str:
    """Convert an ISO local/offset datetime to Graph's UTC date-time format."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return parsed.astimezone(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


SYSTEM_PROMPT = """
You are Jarvis, a helpful personal assistant connected to the user's Microsoft account.
Use the available tools when the user asks about email, calendar, or Microsoft To-Do.

Important email rule: you may read emails and create drafts, but you must never send email.
There is no send-email tool. Tell the user that drafts must be reviewed and sent by them.

Execution rule:
- When the user clearly asks you to create, update, or delete a calendar event or To-Do task, execute the tool immediately.
- Do not ask for confirmation before each action and do not repeatedly ask for confirmation.
- Ask a question only when a required detail is genuinely missing or ambiguous (for example, no meeting time).
- After a successful tool call, clearly summarize what changed. Never claim success unless the tool returned successfully.

If a tool returns an error, explain the safe error and suggest the relevant next step.
For permission errors, tell the user to sign out, sign in again, and grant the requested Microsoft permission.

Calendar date and time rules:
- The user's IANA timezone is {timezone}.
- The current local date and time is {current_datetime}.
- Today is {today} in the user's timezone, not the server's timezone.
- Calculate relative dates such as tomorrow from today's local date.
- Interpret a time without a timezone in the user's timezone.
- Never invent a month, date, duration, or timezone. If a required date, time, duration, or timezone is ambiguous, ask one concise clarifying question before creating or updating an event.
- Use ISO date-time strings for calendar tools. The calendar tool converts local times safely for Microsoft Graph.
"""


def tool_error(error: Exception) -> str:
    if isinstance(error, GraphAPIError):
        return json.dumps(
            {
                "error": str(error),
                "status_code": error.status_code,
                "instruction": "Explain this safe error to the user and suggest the next step.",
            }
        )
    return json.dumps({"error": "The requested Microsoft operation could not be completed."})


def build_agent(access_token: str, settings: Settings, user_timezone: str = "UTC"):
    """Build a LangGraph agent with the user's token and local timezone context."""
    # ZoneInfo raises immediately for an invalid value; API validation normally
    # catches this, while this guard also protects other callers of build_agent.
    local_zone = ZoneInfo(user_timezone)
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    @tool
    async def list_recent_emails(limit: int = 10) -> str:
        """List the user's most recent emails."""
        try:
            result = await emails.list_emails(access_token, max(1, min(limit, 50)))
            return json.dumps(result)
        except Exception as error:
            return tool_error(error)

    @tool
    async def read_email(email_id: str) -> str:
        """Read one email using its Microsoft Graph email ID."""
        try:
            return json.dumps(await emails.get_email(access_token, email_id))
        except Exception as error:
            return tool_error(error)

    @tool
    async def draft_email(subject: str, body: str, recipients: list[str]) -> str:
        """Create an email draft for the user to review. Never send email."""
        try:
            result = await emails.create_email_draft(
                access_token, subject, body, recipients
            )
            return json.dumps(
                {
                    "message": "Draft created. It was not sent.",
                    "draft": result,
                }
            )
        except Exception as error:
            return tool_error(error)

    @tool
    async def list_calendar_events(limit: int = 20) -> str:
        """List upcoming calendar events."""
        try:
            result = await calendar.list_events(access_token, max(1, min(limit, 50)))
            return json.dumps(result)
        except Exception as error:
            return tool_error(error)

    @tool
    async def create_calendar_event(
        subject: str,
        start: str,
        end: str,
        time_zone: str | None = None,
        body: str = "",
        location: str = "",
        attendees: list[str] | None = None,
    ) -> str:
        """Create a calendar event and invite attendees by email address.

        Start and end should be ISO date-time strings. If the user names an
        attendee without an email address, ask for the address before calling
        this tool because Graph cannot reliably resolve arbitrary names.
        """
        event_timezone = time_zone or user_timezone
        try:
            # Graph reliably accepts UTC/Windows-compatible timestamps. Convert
            # IANA browser times here so DST and server timezone never matter.
            graph_start = to_graph_utc(start, event_timezone)
            graph_end = to_graph_utc(end, event_timezone)
        except (ValueError, ZoneInfoNotFoundError) as error:
            return json.dumps({"error": f"Invalid calendar date-time: {error}"})
        event: dict[str, object] = {
            "subject": subject,
            "start": {"dateTime": graph_start, "timeZone": "UTC"},
            "end": {"dateTime": graph_end, "timeZone": "UTC"},
        }
        if body:
            event["body"] = {"contentType": "Text", "content": body}
        if location:
            event["location"] = {"displayName": location}
        if attendees:
            event["attendees"] = [
                {
                    "emailAddress": {"address": address.strip()},
                    "type": "required",
                }
                for address in attendees
                if address.strip()
            ]
        try:
            return json.dumps(await calendar.create_event(access_token, event))
        except Exception as error:
            return tool_error(error)

    @tool
    async def update_calendar_event(event_id: str, changes: dict) -> str:
        """Update a calendar event using a Microsoft Graph changes object."""
        try:
            return json.dumps(
                await calendar.update_event(access_token, event_id, changes)
            )
        except Exception as error:
            return tool_error(error)

    @tool
    async def delete_calendar_event(event_id: str) -> str:
        """Delete a calendar event after the user requested its deletion."""
        try:
            await calendar.delete_event(access_token, event_id)
            return json.dumps({"success": True, "event_id": event_id})
        except Exception as error:
            return tool_error(error)

    @tool
    async def list_todo_tasks(limit: int = 20) -> str:
        """List tasks from the user's default Microsoft To-Do list."""
        try:
            result = await todos.list_todos(access_token, max(1, min(limit, 50)))
            return json.dumps(result)
        except Exception as error:
            return tool_error(error)

    @tool
    async def create_todo_task(title: str, body: str = "") -> str:
        """Create a task in the user's default Microsoft To-Do list."""
        title = title.strip()
        if not title:
            return json.dumps({"error": "A To-Do title is required."})

        task: dict[str, object] = {"title": title}
        if body:
            task["body"] = {"content": body, "contentType": "text"}
        try:
            return json.dumps(await todos.create_todo(access_token, task))
        except Exception as error:
            return tool_error(error)

    @tool
    async def update_todo_task(task_id: str, changes: dict) -> str:
        """Update a Microsoft To-Do task using a changes object."""
        try:
            return json.dumps(await todos.update_todo(access_token, task_id, changes))
        except Exception as error:
            return tool_error(error)

    @tool
    async def delete_todo_task(task_id: str) -> str:
        """Delete a task from the user's default Microsoft To-Do list."""
        try:
            await todos.delete_todo(access_token, task_id)
            return json.dumps({"success": True, "task_id": task_id})
        except Exception as error:
            return tool_error(error)

    tools = [
        list_recent_emails,
        read_email,
        draft_email,
        list_calendar_events,
        create_calendar_event,
        update_calendar_event,
        delete_calendar_event,
        list_todo_tasks,
        create_todo_task,
        update_todo_task,
        delete_todo_task,
    ]
    model = ChatOpenAI(
        api_key=SecretStr(settings.openai_api_key),
        model=settings.openai_model,
        temperature=0,
    ).bind_tools(tools)

    async def call_model(state: MessagesState):
        now_local = datetime.now(local_zone)
        response = await model.ainvoke(
            [
                SystemMessage(
                    content=SYSTEM_PROMPT.format(
                        timezone=user_timezone,
                        current_datetime=now_local.isoformat(),
                        today=now_local.date().isoformat(),
                    )
                ),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    graph = StateGraph(cast(Any, MessagesState))
    graph.add_node("assistant", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "assistant")
    graph.add_conditional_edges("assistant", tools_condition)
    graph.add_edge("tools", "assistant")
    return graph.compile()
