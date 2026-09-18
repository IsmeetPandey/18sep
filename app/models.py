"""API contracts kept separate from persistence representation."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Status = Literal["open", "in_progress", "resolved", "ignored"]


class InteractionIn(BaseModel):
    provider: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    provider_event_id: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=5000)
    reach: int = Field(default=0, ge=0, le=100_000_000)


class AssignmentIn(BaseModel):
    assignee: str | None = Field(default=None, max_length=120)

    @field_validator("assignee")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None


class StatusIn(BaseModel):
    status: Status


class DraftIn(BaseModel):
    draft: str = Field(min_length=1, max_length=5000)


class InteractionOut(BaseModel):
    id: int
    provider: str
    provider_event_id: str
    author: str
    body: str
    reach: int
    intent: str
    priority: str
    score: int
    status: Status
    sla_deadline: datetime
    assignee: str | None
    response_draft: str | None
    created_at: datetime
    updated_at: datetime


class ExceptionOut(BaseModel):
    id: int
    interaction_id: int
    kind: str
    severity: str
    reason: str
    created_at: datetime


class AuditOut(BaseModel):
    event_type: str
    actor: str
    detail: str
    created_at: datetime
