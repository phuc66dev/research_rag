"""Bảo: persistent conversation and message storage."""

from uuid import UUID

from fastapi import APIRouter

from app.api.workspaces import Db, require_workspace
from app.core.errors import not_implemented

router = APIRouter(tags=["sessions"])


@router.get("/workspaces/{workspace_id}/sessions", status_code=501)
def list_sessions(workspace_id: UUID, db: Db):
    require_workspace(db, workspace_id)
    not_implemented("Danh sách chưa có storage")


@router.post("/chat/sessions", status_code=501)
def create_session():
    not_implemented("Tạo hội thoại")


@router.get("/chat/sessions/{session_id}/messages", status_code=501)
def list_messages(session_id: UUID):
    not_implemented("Lịch sử tin nhắn")
