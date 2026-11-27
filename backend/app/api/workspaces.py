from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, require_owner
from app.api.documents import check_origin
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories import workspaces as repository
from app.repositories.sessions import delete_workspace_sessions
from app.schemas.workspace import WorkspaceCreate, WorkspacePatch, WorkspaceRead
from app.services.documents.service import delete_workspace_documents

router = APIRouter(prefix="/workspaces", tags=["workspaces"], dependencies=[Depends(check_origin)])
Db = Annotated[Session, Depends(get_db)]


def require_workspace(db: Session, workspace_id: UUID, current_user: User) -> Workspace:
    item = db.get(Workspace, str(workspace_id))
    if item is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "workspace_not_found", "message": "Không tìm thấy sổ tay môn học."},
        )
    require_owner(item.owner_id, current_user)
    return repository.with_document_count(db, item)


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(db: Db, current_user: CurrentUser):
    return repository.list_workspaces(db, current_user.id)


@router.post("", response_model=WorkspaceRead, status_code=201)
def create_workspace(data: WorkspaceCreate, db: Db, current_user: CurrentUser):
    return repository.create_workspace(db, data, current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(workspace_id: UUID, db: Db, current_user: CurrentUser):
    return require_workspace(db, workspace_id, current_user)


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def rename_workspace(workspace_id: UUID, data: WorkspacePatch, db: Db, current_user: CurrentUser):
    return repository.rename_workspace(
        db, require_workspace(db, workspace_id, current_user), data.name
    )


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(workspace_id: UUID, db: Db, current_user: CurrentUser, request: Request):
    item = require_workspace(db, workspace_id, current_user)
    item.is_deleting = True
    db.commit()
    delete_workspace_documents(
        db, str(workspace_id), current_user, request.app.state.document_storage
    )
    delete_workspace_sessions(db, str(workspace_id))
    db.delete(item)
    db.commit()
    return Response(status_code=204)
