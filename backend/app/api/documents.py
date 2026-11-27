from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import FileResponse

from app.api.auth import CurrentUser, Db
from app.repositories import documents as repo
from app.schemas.document import DocumentRead, SourceChunk, SourceSearch
from app.services.documents import service
from app.services.documents.access import fail, require_document, require_workspace_access
from app.services.retrieval.service import search_sources


def check_origin(request: Request):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        allowed = {*request.app.state.settings.cors_origins, str(request.base_url).rstrip("/")}
        if origin and origin not in allowed:
            fail(403, "invalid_origin", "Nguồn yêu cầu không được phép.")


router = APIRouter(tags=["documents"], dependencies=[Depends(check_origin)])


@router.get("/workspaces/{workspace_id}/documents", response_model=list[DocumentRead])
def list_documents(workspace_id: UUID, db: Db, current_user: CurrentUser):
    require_workspace_access(db, str(workspace_id), current_user)
    return repo.list_documents(db, current_user.id, str(workspace_id))


@router.post(
    "/workspaces/{workspace_id}/documents",
    response_model=DocumentRead,
    status_code=202,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def upload_document(
    workspace_id: UUID,
    request: Request,
    db: Db,
    current_user: CurrentUser,
    filename: Annotated[str, Query(min_length=1, max_length=255)],
):
    return await service.upload_document(request, db, current_user, str(workspace_id), filename)


@router.get("/documents/{document_id}/status", response_model=DocumentRead)
def document_status(document_id: UUID, db: Db, current_user: CurrentUser):
    return require_document(db, str(document_id), current_user)


@router.get(
    "/documents/{document_id}/file",
    response_class=FileResponse,
    responses={200: {"content": {"application/pdf": {}}}},
)
def original_document(document_id: UUID, db: Db, current_user: CurrentUser, request: Request):
    item = require_document(db, str(document_id), current_user)
    if item.status == "deleting":
        fail(410, "document_deleted", "Tài liệu đang được xóa.")
    if item.status != "ready":
        fail(409, "document_not_ready", "Tài liệu chưa sẵn sàng để mở nguồn.")
    path = request.app.state.document_storage.path(item.id)
    if not path.is_file():
        fail(404, "file_not_found", "Không tìm thấy tệp gốc.")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=item.title,
        content_disposition_type="inline",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/documents/{document_id}/retry", response_model=DocumentRead, status_code=202)
def retry_document(document_id: UUID, db: Db, current_user: CurrentUser):
    return service.retry_document(db, str(document_id), current_user)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: UUID, db: Db, current_user: CurrentUser, request: Request):
    service.delete_document(
        db, require_document(db, str(document_id), current_user), request.app.state.document_storage
    )
    return Response(status_code=204)


@router.post("/workspaces/{workspace_id}/sources/search", response_model=list[SourceChunk])
def search(
    workspace_id: UUID, data: SourceSearch, db: Db, current_user: CurrentUser, request: Request
):
    return search_sources(
        db,
        current_user=current_user,
        workspace_id=str(workspace_id),
        request=data,
        embedder=request.app.state.embedder,
    )
