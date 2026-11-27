from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate


def list_workspaces(db: Session, owner_id: str) -> list[Workspace]:
    items = list(
        db.scalars(
            select(Workspace)
            .where(Workspace.owner_id == owner_id)
            .order_by(Workspace.updated_at.desc(), Workspace.id)
        )
    )
    counts = dict(
        db.execute(
            select(Document.workspace_id, func.count())
            .where(Document.owner_id == owner_id)
            .group_by(Document.workspace_id)
        ).all()
    )
    for item in items:
        item.document_count = counts.get(item.id, 0)
    return items


def with_document_count(db: Session, item: Workspace) -> Workspace:
    item.document_count = db.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.workspace_id == item.id, Document.owner_id == item.owner_id)
    )
    return item


def create_workspace(db: Session, data: WorkspaceCreate, owner_id: str) -> Workspace:
    item = Workspace(**data.model_dump(), owner_id=owner_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def rename_workspace(db: Session, item: Workspace, name: str) -> Workspace:
    item.name = name
    item.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(item)
    return item
