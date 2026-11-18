"""Shared entry point owned by Bảo; register routers here by coordinated PR."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import chat, documents, health, sessions, workspaces
from app.core.config import Settings
from app.models.workspace import Base


def create_app(*, database_url: str | None = None, enable_mock_chat: bool | None = None) -> FastAPI:
    settings = Settings()
    if database_url is not None:
        settings.database_url = database_url
    if enable_mock_chat is not None:
        settings.enable_mock_chat = enable_mock_chat
    url = make_url(settings.database_url)
    pool_options = (
        {"poolclass": StaticPool}
        if url.drivername.startswith("sqlite") and url.database in (None, "", ":memory:")
        else {}
    )
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if url.drivername.startswith("sqlite") else {},
        **pool_options,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if url.drivername.startswith("sqlite") and url.database not in (None, "", ":memory:"):
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(engine)
        try:
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        title="EduRAG-VN",
        version="0.1.0",
        description="Local bootstrap API. No authentication or production RAG yet.",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.session_factory = sessionmaker(bind=engine)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    for router in (
        health.router,
        workspaces.router,
        documents.router,
        sessions.router,
        chat.router,
    ):
        application.include_router(router, prefix="/api/v1")
    return application


app = create_app()
