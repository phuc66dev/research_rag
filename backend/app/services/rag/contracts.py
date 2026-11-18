"""Shared boundary: Phúc proposes changes; Bảo and Phú review consumers."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    workspace_id: UUID
    document_ids: list[UUID] = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=4000)
    mode: Literal["strict"] = "strict"

    @field_validator("query", mode="before")
    @classmethod
    def trim_query(cls, value):
        return value.strip() if isinstance(value, str) else value


class Citation(BaseModel):
    id: str
    document_id: UUID
    document_version: str
    document_title: str
    page_number: int = Field(ge=1)
    snippet: str
    bbox: tuple[float, float, float, float] | None = None
