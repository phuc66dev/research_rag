import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.models.document import Document, DocumentJob
from app.models.workspace import Workspace
from app.repositories import documents as repo
from app.services.documents.access import fail, require_document, require_workspace_access
from app.services.history import history_service


async def upload_document(request: Request, db, current_user, workspace_id: str, filename: str):
    require_workspace_access(db, workspace_id, current_user)
    settings = request.app.state.settings
    storage = request.app.state.document_storage
    title = filename.replace("\\", "/").split("/")[-1].strip()
    if not title or len(title) > 255 or any(ord(c) < 32 for c in title):
        fail(422, "invalid_filename", "Tên tệp không hợp lệ.")
    if (
        not title.lower().endswith(".pdf")
        or request.headers.get("content-type", "").split(";")[0].lower() != "application/pdf"
    ):
        fail(415, "unsupported_type", "Bản demo chỉ nhận PDF có văn bản.")
    length = request.headers.get("content-length")
    if length and length.isdecimal() and int(length) > settings.document_max_bytes:
        fail(413, "file_too_large", "Tệp vượt quá giới hạn dung lượng.")
    storage.root.mkdir(parents=True, exist_ok=True)
    document_id = str(uuid4())
    temp = storage.temporary_path(document_id)
    target = storage.path(document_id)
    digest = hashlib.sha256()
    size = 0
    saved = False
    try:
        with temp.open("xb") as stream:
            async for block in request.stream():
                size += len(block)
                if size > settings.document_max_bytes:
                    fail(413, "file_too_large", "Tệp vượt quá giới hạn dung lượng.")
                digest.update(block)
                stream.write(block)
        with temp.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                fail(415, "invalid_pdf", "Nội dung tệp không phải PDF.")
        version = digest.hexdigest()
        if repo.duplicate(db, workspace_id, version):
            fail(409, "duplicate_document", "Tệp này đã có trong sổ tay.")
        db.expire_all()
        require_workspace_access(db, workspace_id, current_user)
        # Serialize publication against workspace deletion and concurrent uploads.
        locked = db.execute(
            update(Workspace)
            .where(
                Workspace.id == workspace_id,
                Workspace.owner_id == current_user.id,
                Workspace.is_deleting.is_(False),
            )
            .values(updated_at=datetime.now(UTC))
        )
        if not locked.rowcount:
            fail(409, "workspace_deleting", "Sổ tay đã thay đổi hoặc đang được xóa.")
        count = db.scalar(
            select(func.count()).select_from(Document).where(Document.workspace_id == workspace_id)
        )
        if count >= settings.document_max_per_workspace:
            fail(409, "document_limit", "Sổ tay đã đạt giới hạn số tài liệu.")
        item = Document(
            id=document_id,
            owner_id=current_user.id,
            workspace_id=workspace_id,
            title=title,
            document_version=version,
            size_bytes=size,
        )
        db.add(item)
        db.flush()
        db.add(DocumentJob(document_id=document_id))
        temp.replace(target)
        db.commit()
        saved = True
        db.refresh(item)
        return item
    except IntegrityError:
        db.rollback()
        fail(409, "duplicate_document", "Tệp này đã có trong sổ tay.")
    finally:
        temp.unlink(missing_ok=True)
        if not saved:
            db.rollback()
            target.unlink(missing_ok=True)


def retry_document(db, document_id, current_user):
    item = require_document(db, document_id, current_user)
    if item.status != "failed":
        fail(409, "document_not_failed", "Chỉ có thể thử lại tài liệu xử lý lỗi.")
    changed = db.execute(
        update(Document)
        .where(Document.id == item.id, Document.status == "failed")
        .values(status="queued")
    )
    if not changed.rowcount:
        db.rollback()
        fail(409, "document_not_failed", "Tài liệu đã được đưa vào hàng đợi.")
    job = db.get(DocumentJob, item.id)
    repo.delete_document_index(db, item.id)
    job.generation += 1
    job.state = "queued"
    job.lease_token = None
    job.started_at = None
    item.status = "queued"
    item.error_code = None
    item.page_count = None
    item.chunk_count = 0
    item.embedding_model = None
    item.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(item)
    return item


def delete_document(db, item, storage):
    item.status = "deleting"
    item.updated_at = datetime.now(UTC)
    job = db.get(DocumentJob, item.id)
    if job:
        job.state = "cancelled"
        job.lease_token = None
        job.generation += 1
    repo.delete_document_index(db, item.id)
    db.commit()
    finish_deletion(db, item, storage)


def finish_deletion(db, item, storage):
    history_service.cleanup_citations_for_document(db, item.id)
    storage.path(item.id).unlink(missing_ok=True)
    repo.remove_document(db, item)
    db.commit()


def delete_workspace_documents(db, workspace_id: str, current_user, storage):
    """Cleanup boundary used by Phúc's workspace deletion."""
    require_workspace_access(db, workspace_id, current_user, allow_deleting=True)
    for item in repo.list_documents(db, current_user.id, workspace_id):
        delete_document(db, item, storage)
