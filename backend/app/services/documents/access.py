from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.auth import require_owner
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace


def fail(status: int, code: str, message: str):
    raise HTTPException(status, detail={"code": code, "message": message})


def require_workspace_access(
    db: Session, workspace_id: str, current_user: User, *, allow_deleting: bool = False
):
    workspace = db.get(Workspace, str(workspace_id))
    if workspace is None:
        fail(404, "workspace_not_found", "Không tìm thấy sổ tay môn học.")
    owner_id = getattr(workspace, "owner_id", None)
    if owner_id is None:
        fail(
            503,
            "workspace_authorization_unavailable",
            "Sổ tay chưa được tích hợp quyền sở hữu. Vui lòng liên hệ người quản lý.",
        )
    require_owner(owner_id, current_user)
    if workspace.is_deleting and not allow_deleting:
        fail(409, "workspace_deleting", "Sổ tay đang được xóa. Hãy thử lại thao tác xóa sổ tay.")
    return workspace


def require_document(db: Session, document_id: str, current_user: User):
    item = db.get(Document, str(document_id))
    if item is None:
        fail(404, "document_not_found", "Không tìm thấy tài liệu.")
    require_owner(item.owner_id, current_user)
    require_workspace_access(db, item.workspace_id, current_user)
    return item
