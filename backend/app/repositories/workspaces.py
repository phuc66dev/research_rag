from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate


def list_workspaces(db: Session) -> list[Workspace]:
    return list(db.scalars(select(Workspace).order_by(Workspace.updated_at.desc(), Workspace.id)))


def create_workspace(db: Session, data: WorkspaceCreate) -> Workspace:
    item = Workspace(**data.model_dump())
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
