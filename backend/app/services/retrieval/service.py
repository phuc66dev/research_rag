import math

from sqlalchemy import select

from app.models.document import Document, DocumentChunk
from app.schemas.document import SourceChunk, SourceSearch
from app.services.documents.access import fail, require_document, require_workspace_access


def search_sources(db, *, current_user, workspace_id: str, request: SourceSearch, embedder):
    """Validate every requested source before embedding or reading indexed content."""
    require_workspace_access(db, workspace_id, current_user)
    ids = list(dict.fromkeys(str(value) for value in request.document_ids))
    for document_id in ids:
        item = require_document(db, document_id, current_user)
        if item.workspace_id != workspace_id:
            fail(403, "source_outside_workspace", "Nguồn không thuộc sổ tay đang hỏi.")
        if item.status != "ready":
            fail(409, "source_not_ready", "Có tài liệu chưa sẵn sàng để tìm kiếm.")
        if item.embedding_model != embedder.model_name:
            fail(409, "index_model_mismatch", "Chỉ mục dùng model khác. Cần lập chỉ mục lại.")
    try:
        vector = embedder.embed([request.query], query=True)[0]
    except Exception:
        fail(503, "embedding_unavailable", "Không chạy được model tìm kiếm. Vui lòng thử lại.")
    db.expire_all()
    for document_id in ids:
        item = require_document(db, document_id, current_user)
        if item.status != "ready":
            fail(409, "source_not_ready", "Nguồn đã thay đổi trong khi tìm kiếm.")
    stmt = (
        select(DocumentChunk, Document)
        .join(Document)
        .where(
            Document.owner_id == current_user.id,
            Document.workspace_id == workspace_id,
            Document.status == "ready",
            Document.id.in_(ids),
            DocumentChunk.document_version == Document.document_version,
        )
    )
    results = []
    for chunk, item in db.execute(stmt.execution_options(yield_per=100)):
        if len(vector) != len(chunk.embedding):
            fail(409, "index_dimension_mismatch", "Kích thước vector không khớp chỉ mục.")
        score = sum(a * b for a, b in zip(vector, chunk.embedding, strict=True))
        if not math.isfinite(score) or score <= 0:
            continue
        results.append(
            SourceChunk(
                id=chunk.id,
                document_id=item.id,
                document_version=chunk.document_version,
                document_title=item.title,
                text=chunk.text,
                page_number=chunk.page_number,
                score=score,
            )
        )
        results.sort(key=lambda result: (-result.score, result.id))
        del results[request.limit :]
    return sorted(results, key=lambda result: (-result.score, result.id))[: request.limit]
