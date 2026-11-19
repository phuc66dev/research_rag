import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CitationSource(BaseModel):
    """Source citation item referenced in AI answers (aligned with contracts/rag.md)."""

    id: str = Field(description="Unique ID of the citation or chunk")
    document_id: str = Field(description="UUID of the referenced document")
    document_version: str | None = Field(default=None, description="Hash or version of document")
    document_title: str = Field(description="Title / filename of the document")
    page_number: int | None = Field(default=None, description="1-based page number in document")
    snippet: str = Field(default="", description="Relevant textual quote or excerpt")
    bbox: list[float] | None = Field(default=None, description="Bounding box if available")


class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant"] = Field(description="Role of message sender")
    content: str = Field(min_length=1, description="Message text content")
    sources: list[CitationSource] = Field(default_factory=list, description="Citations referenced")
    status: Literal["completed", "interrupted", "error"] = Field(
        default="completed", description="Status of the generation"
    )


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    sources: list[CitationSource] = Field(default_factory=list)
    status: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def restore_utc(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @classmethod
    def from_orm(cls, message: Any) -> "ChatMessageRead":
        """Convert SQLAlchemy ChatMessage model to Pydantic schema with parsed sources JSON."""
        parsed_sources: list[CitationSource] = []
        if hasattr(message, "sources_json") and message.sources_json:
            try:
                raw_sources = json.loads(message.sources_json)
                if isinstance(raw_sources, list):
                    for item in raw_sources:
                        if isinstance(item, dict):
                            parsed_sources.append(CitationSource.model_validate(item))
            except Exception:
                parsed_sources = []

        created_at = message.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        return cls(
            id=str(message.id),
            session_id=str(message.session_id),
            role=message.role,
            content=message.content,
            sources=parsed_sources,
            status=message.status,
            created_at=created_at,
        )


class ChatSessionCreate(BaseModel):
    workspace_id: str = Field(description="UUID of the workspace")
    title: str = Field(default="Hội thoại mới", min_length=1, max_length=200)

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value):
        return value.strip() if isinstance(value, str) else value


class ChatSessionPatch(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value):
        return value.strip() if isinstance(value, str) else value


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    owner_id: str
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def restore_utc(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class ChatSessionDetail(ChatSessionRead):
    messages: list[ChatMessageRead] = Field(default_factory=list)
