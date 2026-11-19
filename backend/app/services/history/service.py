from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.auth import require_owner
from app.models.session import ChatSession
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories import sessions as repo
from app.schemas.session import (
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionRead,
)


class HistoryService:
    """Service handling all chat history and session persistence operations."""

    def get_session_or_404(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User | None = None,
        check_owner: bool = True,
    ) -> ChatSession:
        """Fetch session by ID.

        If check_owner is True and current_user is provided, verifies that current_user is the
        owner; raises 403 Forbidden otherwise.
        """
        session = repo.get_session(db, str(session_id))
        if session is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "session_not_found", "message": "Không tìm thấy phiên hội thoại."},
            )
        if check_owner and current_user is not None:
            require_owner(session.owner_id, current_user)
        return session

    def list_sessions_with_count(
        self,
        db: Session,
        current_user: User,
        workspace_id: str | UUID | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[ChatSessionRead], int]:
        """List chat sessions owned by current_user with pagination and total count."""
        w_id = str(workspace_id) if workspace_id else None
        pairs, total = repo.list_sessions(
            db=db,
            owner_id=current_user.id,
            workspace_id=w_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        items = [
            ChatSessionRead(
                id=str(session.id),
                workspace_id=str(session.workspace_id),
                owner_id=str(session.owner_id),
                title=session.title,
                message_count=count,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
            for session, count in pairs
        ]
        return items, total

    def list_sessions(
        self,
        db: Session,
        current_user: User,
        workspace_id: str | UUID | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ChatSessionRead]:
        """List chat sessions owned by current_user with optional filters."""
        items, _ = self.list_sessions_with_count(
            db=db,
            current_user=current_user,
            workspace_id=workspace_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        return items

    def create_session(
        self,
        db: Session,
        current_user: User,
        data: ChatSessionCreate,
    ) -> ChatSessionRead:
        """Create a new chat session for current_user inside a workspace."""
        # Verify workspace exists
        workspace = db.get(Workspace, str(data.workspace_id))
        if workspace is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "workspace_not_found",
                    "message": "Không tìm thấy sổ tay môn học.",
                },
            )

        session = repo.create_session(
            db=db,
            owner_id=current_user.id,
            workspace_id=str(data.workspace_id),
            title=data.title,
        )
        return ChatSessionRead(
            id=str(session.id),
            workspace_id=str(session.workspace_id),
            owner_id=str(session.owner_id),
            title=session.title,
            message_count=0,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def get_session_detail(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User,
        messages_limit: int | None = None,
        messages_offset: int = 0,
    ) -> ChatSessionDetail:
        """Get session detail with full messages and parsed citations."""
        session = self.get_session_or_404(db, session_id, current_user=current_user)
        messages, total = repo.list_messages(
            db, session.id, limit=messages_limit, offset=messages_offset
        )
        parsed_messages = [ChatMessageRead.from_orm(m) for m in messages]

        return ChatSessionDetail(
            id=str(session.id),
            workspace_id=str(session.workspace_id),
            owner_id=str(session.owner_id),
            title=session.title,
            message_count=total,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=parsed_messages,
        )

    def rename_session(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User,
        new_title: str,
    ) -> ChatSessionRead:
        """Rename session title, validating ownership."""
        session = self.get_session_or_404(db, session_id, current_user=current_user)
        updated = repo.rename_session(db, session, new_title.strip())
        count = repo.get_session_message_count(db, updated.id)
        return ChatSessionRead(
            id=str(updated.id),
            workspace_id=str(updated.workspace_id),
            owner_id=str(updated.owner_id),
            title=updated.title,
            message_count=count,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    def delete_session(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User,
    ) -> None:
        """Delete session and cascade delete all its messages."""
        session = self.get_session_or_404(db, session_id, current_user=current_user)
        repo.delete_session(db, session)

    def list_messages_with_count(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[ChatMessageRead], int]:
        """List messages for a session with total count, verifying user is the session owner."""
        session = self.get_session_or_404(db, session_id, current_user=current_user)
        messages, total = repo.list_messages(db, session.id, limit=limit, offset=offset)
        return [ChatMessageRead.from_orm(m) for m in messages], total

    def list_messages(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ChatMessageRead]:
        """List messages for a session, verifying user is the session owner."""
        items, _ = self.list_messages_with_count(
            db=db,
            session_id=session_id,
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
        return items

    def append_message(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User,
        role: str,
        content: str,
        sources: list[Any] | None = None,
        status: str = "completed",
    ) -> ChatMessageRead:
        """Append a single message (user or assistant) to a session."""
        session = self.get_session_or_404(db, session_id, current_user=current_user)
        msg = repo.add_message(
            db=db,
            session=session,
            role=role,
            content=content,
            sources=sources,
            status=status,
        )
        return ChatMessageRead.from_orm(msg)

    def record_chat_turn(
        self,
        db: Session,
        session_id: str | UUID,
        current_user: User,
        query: str,
        answer: str,
        citations: list[Any] | None = None,
        status: str = "completed",
    ) -> tuple[ChatMessageRead, ChatMessageRead]:
        """Convenience method for teammate Phúc:

        Atomically records a complete user query + assistant answer turn with citations.
        Updates session timestamps and auto-names session title if currently default.
        """
        session = self.get_session_or_404(db, session_id, current_user=current_user)

        user_msg = repo.add_message(
            db=db,
            session=session,
            role="user",
            content=query,
            sources=None,
            status="completed",
        )
        assistant_msg = repo.add_message(
            db=db,
            session=session,
            role="assistant",
            content=answer,
            sources=citations,
            status=status,
        )
        return ChatMessageRead.from_orm(user_msg), ChatMessageRead.from_orm(assistant_msg)

    def cleanup_citations_for_document(self, db: Session, document_id: str | UUID) -> int:
        """Helper for teammate Bảo:

        When a document is deleted, tags any saved citations pointing to it as deleted.
        """
        return repo.invalidate_document_citations(db, str(document_id))


# Singleton instance for easy import across modules
history_service = HistoryService()
