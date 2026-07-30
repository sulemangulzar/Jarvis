from datetime import datetime

from pydantic import BaseModel, Field


class EmailDraftRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=100_000)
    recipients: list[str] = Field(min_length=1, max_length=50)


class EventDateTime(BaseModel):
    date_time: datetime
    time_zone: str = "UTC"

    def to_graph(self) -> dict:
        return {
            "dateTime": self.date_time.isoformat(),
            "timeZone": self.time_zone,
        }


class EventCreateRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    start: EventDateTime
    end: EventDateTime
    body: str | None = None
    location: str | None = None

    def to_graph(self) -> dict:
        event: dict[str, object] = {
            "subject": self.subject,
            "start": self.start.to_graph(),
            "end": self.end.to_graph(),
        }
        if self.body is not None:
            event["body"] = {"contentType": "Text", "content": self.body}
        if self.location is not None:
            event["location"] = {"displayName": self.location}
        return event


class EventUpdateRequest(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=500)
    start: EventDateTime | None = None
    end: EventDateTime | None = None
    body: str | None = None
    location: str | None = None

    def to_graph(self) -> dict:
        changes: dict[str, object] = {}
        if self.subject is not None:
            changes["subject"] = self.subject
        if self.start is not None:
            changes["start"] = self.start.to_graph()
        if self.end is not None:
            changes["end"] = self.end.to_graph()
        if self.body is not None:
            changes["body"] = {"contentType": "Text", "content": self.body}
        if self.location is not None:
            changes["location"] = {"displayName": self.location}
        return changes


class TodoCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body: str | None = None
    due_date_time: EventDateTime | None = None

    def to_graph(self) -> dict:
        task: dict[str, object] = {"title": self.title}
        if self.body is not None:
            task["body"] = {"content": self.body, "contentType": "text"}
        if self.due_date_time is not None:
            task["dueDateTime"] = self.due_date_time.to_graph()
        return task


class TodoUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    status: str | None = None
    body: str | None = None
    due_date_time: EventDateTime | None = None

    def to_graph(self) -> dict:
        changes: dict[str, object] = {}
        if self.title is not None:
            changes["title"] = self.title
        if self.status is not None:
            changes["status"] = self.status
        if self.body is not None:
            changes["body"] = {"content": self.body, "contentType": "text"}
        if self.due_date_time is not None:
            changes["dueDateTime"] = self.due_date_time.to_graph()
        return changes
