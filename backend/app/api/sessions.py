"""Sessions and chat history endpoints (Owned by Phú).

Implements:
- Workspace-scoped session listing: GET /api/v1/workspaces/{workspace_id}/sessions
- Global session listing & search: GET /api/v1/chat/sessions
- Session creation: POST /api/v1/chat/sessions
- Session detail: GET /api/v1/chat/sessions/{session_id}
- Session rename: PATCH /api/v1/chat/sessions/{session_id}
- Session deletion: DELETE /api/v1/chat/sessions/{session_id}
- Message listing: GET /api/v1/chat/sessions/{session_id}/messages
- Message addition: POST /api/v1/chat/sessions/{session_id}/messages
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.auth import get_current_user
from app.api.workspaces import Db, require_workspace
from app.models.user import User
from app.schemas.session import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionPatch,
    ChatSessionRead,
)
from app.services.history import history_service

router = APIRouter(tags=["sessions"])
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/workspaces/{workspace_id}/sessions", response_model=list[ChatSessionRead])
def list_workspace_sessions(
    workspace_id: UUID,
    db: Db,
    current_user: CurrentUser,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100, description="Max number of sessions to return"),
    offset: int = Query(default=0, ge=0, description="Number of sessions to skip"),
):
    """List chat sessions owned by the current user within a specific workspace with pagination."""
    require_workspace(db, workspace_id)
    items, total = history_service.list_sessions_with_count(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Has-More"] = "true" if (offset + len(items) < total) else "false"
    return items


@router.get("/chat/sessions", response_model=list[ChatSessionRead])
def list_all_user_sessions(
    db: Db,
    current_user: CurrentUser,
    response: Response,
    workspace_id: UUID | None = None,
    query: str | None = Query(default=None, description="Search keyword in session title"),
    limit: int = Query(default=50, ge=1, le=100, description="Max number of sessions to return"),
    offset: int = Query(default=0, ge=0, description="Number of sessions to skip"),
):
    """List all chat sessions belonging to the current user, with optional workspace filter, search, and pagination."""
    items, total = history_service.list_sessions_with_count(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        search=query,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Has-More"] = "true" if (offset + len(items) < total) else "false"
    return items


@router.post("/chat/sessions", response_model=ChatSessionRead, status_code=201)
def create_session(
    data: ChatSessionCreate,
    db: Db,
    current_user: CurrentUser,
):
    """Create a new chat session for the authenticated user."""
    return history_service.create_session(
        db=db,
        current_user=current_user,
        data=data,
    )


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session_detail(
    session_id: UUID,
    db: Db,
    current_user: CurrentUser,
):
    """Retrieve details and messages of a chat session.

    Enforces owner isolation (returns 403 Forbidden if not the owner).
    """
    return history_service.get_session_detail(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )


@router.patch("/chat/sessions/{session_id}", response_model=ChatSessionRead)
def rename_session(
    session_id: UUID,
    data: ChatSessionPatch,
    db: Db,
    current_user: CurrentUser,
):
    """Rename a chat session.

    Enforces owner isolation (returns 403 Forbidden if not the owner).
    """
    return history_service.rename_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
        new_title=data.title,
    )


@router.delete("/chat/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: UUID,
    db: Db,
    current_user: CurrentUser,
):
    """Delete a chat session and all its messages.

    Enforces owner isolation (returns 403 Forbidden if not the owner).
    """
    history_service.delete_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )
    return Response(status_code=204)


@router.get("/chat/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
def list_session_messages(
    session_id: UUID,
    db: Db,
    current_user: CurrentUser,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100, description="Max number of messages to return"),
    offset: int = Query(default=0, ge=0, description="Number of messages to skip"),
):
    """Retrieve messages with citations in a chat session with pagination.

    Enforces owner isolation (returns 403 Forbidden if not the owner).
    """
    items, total = history_service.list_messages_with_count(
        db=db,
        session_id=session_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Has-More"] = "true" if (offset + len(items) < total) else "false"
    return items


@router.post(
    "/chat/sessions/{session_id}/messages", response_model=ChatMessageRead, status_code=201
)
def append_message(
    session_id: UUID,
    data: ChatMessageCreate,
    db: Db,
    current_user: CurrentUser,
):
    """Append a message to an existing chat session.

    Enforces owner isolation (returns 403 Forbidden if not the owner).
    """
    return history_service.append_message(
        db=db,
        session_id=session_id,
        current_user=current_user,
        role=data.role,
        content=data.content,
        sources=data.sources,
        status=data.status,
    )
