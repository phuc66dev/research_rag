from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import (
    generate_session_token,
    get_session_expiry,
    hash_password,
    verify_password,
)
from app.models.message import ChatMessage
from app.models.session import ChatSession
from app.models.user import User
from app.models.user_session import UserSession
from app.models.workspace import Base


def test_hash_password_and_verify():
    password = "MySecurePassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False
    assert verify_password(password, "invalid_hash_string") is False


def test_hash_password_empty_raises_value_error():
    with pytest.raises(ValueError, match="Mật khẩu không được để trống"):
        hash_password("")


def test_generate_session_token():
    t1 = generate_session_token()
    t2 = generate_session_token()
    assert len(t1) >= 32
    assert t1 != t2


def test_get_session_expiry():
    expiry = get_session_expiry(days=7)
    now = datetime.now(UTC)
    assert expiry > now
    assert (expiry - now).days == 6 or (expiry - now).days == 7


def test_models_database_persistence():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        # Create user
        user = User(
            username="phu_test",
            email="phu@example.edu.vn",
            hashed_password=hash_password("Pass1234"),
            full_name="Nguyễn Văn Phú",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.created_at is not None

        # Create user session
        token = generate_session_token()
        session = UserSession(
            id=token,
            user_id=user.id,
            expires_at=get_session_expiry(7),
        )
        db.add(session)
        db.commit()

        # Create chat session & message
        chat_sess = ChatSession(
            workspace_id="test-workspace-id",
            owner_id=user.id,
            title="Phiên thảo luận môn RAG",
        )
        db.add(chat_sess)
        db.commit()
        db.refresh(chat_sess)

        msg = ChatMessage(
            session_id=chat_sess.id,
            role="user",
            content="RAG hoạt động như thế nào?",
            sources_json="[]",
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        assert len(user.user_sessions) == 1
        assert len(user.chat_sessions) == 1
        assert len(chat_sess.messages) == 1
        assert chat_sess.messages[0].content == "RAG hoạt động như thế nào?"
