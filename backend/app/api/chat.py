"""Phúc owns the chat transport and RAG integration."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.errors import not_implemented
from app.services.rag.contracts import ChatRequest
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


@router.post("/sessions/{session_id}/stream", status_code=501)
def stream_answer(session_id: UUID, body: ChatRequest):
    not_implemented("RAG và chat thực")
