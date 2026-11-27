from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    title: str
    document_version: str
    size_bytes: int
    status: Literal["queued", "processing", "ready", "failed", "deleting"]
    error_code: str | None
    page_count: int | None
    chunk_count: int
    embedding_model: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def utc(cls, value):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class SourceSearch(BaseModel):
    document_ids: list[UUID] = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=6, ge=1, le=20)

    @field_validator("query", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class SourceChunk(BaseModel):
    id: str
    document_id: str
    document_version: str
    document_title: str
    text: str
    page_number: int
    section_title: str | None = None
    bbox: None = None
    score: float
