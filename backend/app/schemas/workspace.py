from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class WorkspacePatch(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    @field_validator("created_at", "updated_at")
    @classmethod
    def restore_utc(cls, value: datetime) -> datetime:
        # SQLite stores the UTC values without timezone information.
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
