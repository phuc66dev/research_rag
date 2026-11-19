from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(default="", max_length=100)

    @field_validator("username", mode="before")
    @classmethod
    def clean_username(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class UserLogin(BaseModel):
    username_or_email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username_or_email", mode="before")
    @classmethod
    def clean_identifier(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def restore_utc(cls, value: datetime) -> datetime:
        # SQLite stores UTC values without timezone information.
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AuthResponse(BaseModel):
    user: UserRead
    token: str
    expires_at: datetime
