"""Phúc owns the chat transport and RAG integration."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.api.auth import CurrentUser, Db
from app.services.history import history_service
from app.services.rag.contracts import ChatRequest
from app.services.rag.generation import answer_events, claim_turn, prepare_turn
from app.services.rag.mock import mock_events


class EventStreamResponse(StreamingResponse):
    media_type = "text/event-stream"


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/mock/stream", response_class=EventStreamResponse)
def stream_mock(body: ChatRequest, request: Request):
    if not request.app.state.settings.enable_mock_chat:
        raise HTTPException(status_code=404, detail="Mock chat is disabled.")
    return EventStreamResponse(
        mock_events(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/{session_id}/stream", response_class=EventStreamResponse)
def stream_answer(
    session_id: UUID, body: ChatRequest, request: Request, db: Db, current_user: CurrentUser
):
    history_service.get_session_or_404(db, session_id, current_user=current_user)
    release = claim_turn(request.app, session_id)
    try:
        prepared = prepare_turn(db, request.app, session_id, body, current_user)
    except Exception:
        release()
        raise
    return EventStreamResponse(
        answer_events(request.app, session_id, current_user, prepared, release),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        background=BackgroundTask(release),
    )
