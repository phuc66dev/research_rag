import json
import unicodedata
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.message import ChatMessage
from app.models.session import ChatSession


def normalize_vietnamese(text: str) -> str:
    """Normalize Vietnamese text by stripping accents/diacritics and lowercasing."""
    if not text:
        return ""
    replaced = text.replace("đ", "d").replace("Đ", "d")
    decomposed = unicodedata.normalize("NFKD", replaced)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.lower().strip()


def list_sessions(
    db: Session,
    owner_id: str,
    workspace_id: str | None = None,
    search: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[tuple[ChatSession, int]], int]:
    """List sessions owned by a specific user with pagination, optional workspace filter and search.

    Supports case-insensitive and accent-insensitive (không dấu / có dấu) search.
    Returns:
        tuple of (paginated_pairs, total_count)
    """
    # Subquery for message count
    msg_count_subq = (
        select(ChatMessage.session_id, func.count(ChatMessage.id).label("cnt"))
        .group_by(ChatMessage.session_id)
        .subquery()
    )

    base_query = (
        select(
            ChatSession,
            func.coalesce(msg_count_subq.c.cnt, 0).label("message_count"),
        )
        .outerjoin(msg_count_subq, ChatSession.id == msg_count_subq.c.session_id)
        .where(ChatSession.owner_id == str(owner_id))
    )

    if workspace_id:
        base_query = base_query.where(ChatSession.workspace_id == str(workspace_id))

    # Case 1: Search query provided -> requires client/python-side accent-insensitive filtering
    if search and search.strip():
        norm_search = normalize_vietnamese(search)
        all_results = db.execute(
            base_query.order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        ).all()
        pairs = [(row[0], int(row[1])) for row in all_results]

        filtered = []
        for session, count in pairs:
            norm_title = normalize_vietnamese(session.title)
            if norm_search in norm_title:
                filtered.append((session, count))

        total_count = len(filtered)
        paged = filtered[offset : offset + limit] if limit is not None else filtered[offset:]
        return paged, total_count

    # Case 2: Standard browsing without search query -> pure SQL LIMIT & OFFSET for max performance
    count_query = select(func.count(ChatSession.id)).where(ChatSession.owner_id == str(owner_id))
    if workspace_id:
        count_query = count_query.where(ChatSession.workspace_id == str(workspace_id))
    total_count = db.scalar(count_query) or 0

    query = base_query.order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    results = db.execute(query).all()
    paged = [(row[0], int(row[1])) for row in results]
    return paged, total_count


def get_session(db: Session, session_id: str) -> ChatSession | None:
    """Retrieve a single session by ID."""
    return db.get(ChatSession, str(session_id))


def get_session_message_count(db: Session, session_id: str) -> int:
    """Get the message count for a single session."""
    count = db.scalar(
        select(func.count(ChatMessage.id)).where(ChatMessage.session_id == str(session_id))
    )
    return count or 0


def create_session(
    db: Session,
    owner_id: str,
    workspace_id: str,
    title: str = "Hội thoại mới",
) -> ChatSession:
    """Create a new chat session for a user in a workspace."""
    now = datetime.now(UTC)
    session = ChatSession(
        owner_id=str(owner_id),
        workspace_id=str(workspace_id),
        title=title,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def rename_session(db: Session, session: ChatSession, new_title: str) -> ChatSession:
    """Update session title and refresh updated_at."""
    session.title = new_title
    session.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session: ChatSession) -> None:
    """Delete a session (messages cascade deleted via relationship)."""
    db.delete(session)
    db.commit()


def list_messages(
    db: Session,
    session_id: str,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[ChatMessage], int]:
    """List messages in a session in chronological order with pagination.

    Returns:
        tuple of (messages, total_count)
    """
    total_count = (
        db.scalar(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == str(session_id))
        )
        or 0
    )

    query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == str(session_id))
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    )
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    messages = list(db.scalars(query))
    return messages, total_count


def add_message(
    db: Session,
    session: ChatSession,
    role: str,
    content: str,
    sources: list[dict[str, Any]] | list[Any] | None = None,
    status: str = "completed",
) -> ChatMessage:
    """Add a message to a session, serialize sources to JSON, and update session.updated_at."""
    sources_data = []
    if sources:
        for s in sources:
            if hasattr(s, "model_dump"):
                sources_data.append(s.model_dump())
            elif isinstance(s, dict):
                sources_data.append(s)

    now = datetime.now(UTC)
    msg = ChatMessage(
        session_id=session.id,
        role=role,
        content=content,
        sources_json=json.dumps(sources_data, ensure_ascii=False),
        status=status,
        created_at=now,
    )
    db.add(msg)

    # Auto-generate title from the first user question if still default
    if session.title == "Hội thoại mới" and role == "user":
        trimmed = content.strip().replace("\n", " ")
        session.title = (trimmed[:50] + "...") if len(trimmed) > 50 else trimmed

    session.updated_at = now
    db.commit()
    db.refresh(msg)
    return msg


def delete_workspace_sessions(
    db: Session,
    workspace_id: str,
    owner_id: str | None = None,
) -> int:
    """Delete all sessions in a workspace.

    Helper for Phúc when a workspace is deleted.
    """
    stmt = delete(ChatSession).where(ChatSession.workspace_id == str(workspace_id))
    if owner_id:
        stmt = stmt.where(ChatSession.owner_id == str(owner_id))
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0


def invalidate_document_citations(db: Session, document_id: str) -> int:
    """Invalidate or tag citations that reference a deleted document.

    Helper for Bảo when a document is removed: marks the citation as '[Tài liệu đã bị xóa]'.
    """
    messages = list(
        db.scalars(select(ChatMessage).where(ChatMessage.sources_json.contains(str(document_id))))
    )
    updated_count = 0
    for msg in messages:
        try:
            sources = json.loads(msg.sources_json)
            changed = False
            for src in sources:
                if str(src.get("document_id")) == str(document_id):
                    src["document_title"] = f"{src.get('document_title', '')} (Đã bị xóa)"
                    src["snippet"] = "[Tài liệu gốc đã bị xóa khỏi hệ thống]"
                    changed = True
            if changed:
                msg.sources_json = json.dumps(sources, ensure_ascii=False)
                updated_count += 1
        except Exception:
            continue

    if updated_count > 0:
        db.commit()
    return updated_count
