from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.workspace import Workspace
from app.repositories import workspaces as repository
from app.schemas.workspace import WorkspaceCreate, WorkspacePatch, WorkspaceRead

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
Db = Annotated[Session, Depends(get_db)]


def require_workspace(db: Session, workspace_id: UUID) -> Workspace:
    item = db.get(Workspace, str(workspace_id))
    if item is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "workspace_not_found", "message": "Không tìm thấy sổ tay môn học."},
        )
    return item


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(db: Db):
    return repository.list_workspaces(db)


@router.post("", response_model=WorkspaceRead, status_code=201)
def create_workspace(data: WorkspaceCreate, db: Db):
    return repository.create_workspace(db, data)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(workspace_id: UUID, db: Db):
    return require_workspace(db, workspace_id)


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def rename_workspace(workspace_id: UUID, data: WorkspacePatch, db: Db):
    return repository.rename_workspace(db, require_workspace(db, workspace_id), data.name)


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(workspace_id: UUID, db: Db):
    db.delete(require_workspace(db, workspace_id))
    db.commit()
    return Response(status_code=204)
