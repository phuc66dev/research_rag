from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk, DocumentJob


def list_documents(db: Session, owner_id: str, workspace_id: str):
    return list(
        db.scalars(
            select(Document)
            .where(Document.owner_id == owner_id, Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc(), Document.id)
        )
    )


def duplicate(db: Session, workspace_id: str, version: str):
    return db.scalar(
        select(Document).where(
            Document.workspace_id == workspace_id, Document.document_version == version
        )
    )


def delete_document_index(db: Session, document_id: str):
    """Delete vectors and text together; caller controls the transaction."""
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))


def remove_document(db: Session, item: Document):
    delete_document_index(db, item.id)
    db.execute(delete(DocumentJob).where(DocumentJob.document_id == item.id))
    db.delete(item)
