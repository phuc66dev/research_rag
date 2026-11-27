"""Shared entry point owned by Bảo; register routers here by coordinated PR."""

import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth, chat, documents, health, sessions, workspaces
from app.core.config import Settings
from app.core.migrations import migrate
from app.models.document import Document, DocumentChunk, DocumentJob  # noqa: F401
from app.services.documents.storage import DocumentStorage
from app.services.documents.worker import worker_loop
from app.services.retrieval.embedding import LocalEmbedding


def create_app(
    *,
    database_url: str | None = None,
    enable_mock_chat: bool | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or Settings()
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
    if url.drivername.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def sqlite_constraints(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=10000")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if url.drivername.startswith("sqlite") and url.database not in (None, "", ":memory:"):
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        migrate(engine)
        worker = asyncio.create_task(worker_loop(app)) if settings.document_worker_enabled else None
        try:
            yield
        finally:
            if worker:
                worker.cancel()
                with suppress(asyncio.CancelledError):
                    await worker
            engine.dispose()

    application = FastAPI(
        title="EduRAG-VN",
        version="0.1.0",
        description=(
            "Local API with authentication, PDF ingestion and source retrieval. "
            "Source-grounded chat streams through a configured OpenAI-compatible provider."
        ),
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.session_factory = sessionmaker(bind=engine)
    application.state.document_storage = DocumentStorage(settings.document_storage_dir)
    application.state.embedder = LocalEmbedding(settings)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    for router in (
        health.router,
        auth.router,
        workspaces.router,
        documents.router,
        sessions.router,
        chat.router,
    ):
        application.include_router(router, prefix="/api/v1")
    return application


app = create_app()
