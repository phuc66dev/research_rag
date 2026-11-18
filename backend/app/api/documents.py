"""Bảo: replace the explicit stubs with document processing and storage."""

from uuid import UUID

from fastapi import APIRouter

from app.api.workspaces import Db, require_workspace
from app.core.errors import not_implemented

router = APIRouter(tags=["documents"])


@router.get("/workspaces/{workspace_id}/documents", status_code=501)
def list_documents(workspace_id: UUID, db: Db):
    require_workspace(db, workspace_id)
    not_implemented("Danh sách chưa có storage")


@router.post("/workspaces/{workspace_id}/documents", status_code=501)
def upload_document(workspace_id: UUID, db: Db):
    require_workspace(db, workspace_id)
    not_implemented("Upload và xử lý tài liệu")


@router.get("/documents/{document_id}/status", status_code=501)
def document_status(document_id: UUID):
    not_implemented("Trạng thái tài liệu")


@router.get("/documents/{document_id}/file", status_code=501)
def original_document(document_id: UUID):
    not_implemented("Đọc file gốc")


@router.delete("/documents/{document_id}", status_code=501)
def delete_document(document_id: UUID):
    not_implemented("Xóa tài liệu")
