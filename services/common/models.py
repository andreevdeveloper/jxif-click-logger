from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column

try:
    from sqlalchemy.dialects.postgresql import JSONB as JSONType
except Exception:
    from sqlalchemy import JSON as JSONType


def utcnow():
    return datetime.now(timezone.utc)


class Link(SQLModel, table=True):
    __tablename__ = "links"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    target_url: str
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Click(SQLModel, table=True):
    __tablename__ = "clicks"

    id: Optional[int] = Field(default=None, primary_key=True)

    link_id: int = Field(foreign_key="links.id", index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    ip: Optional[str] = None
    forwarded_for: Optional[str] = None

    method: str
    path: str

    user_agent: Optional[str] = None
    accept_language: Optional[str] = None
    referer: Optional[str] = None

    headers: dict = Field(default_factory=dict, sa_column=Column(JSONType))
    query: dict = Field(default_factory=dict, sa_column=Column(JSONType))
    client: dict = Field(default_factory=dict, sa_column=Column(JSONType))