from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import generate_session_token, get_session_expiry, hash_password
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import UserRegister


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username.strip().lower())
    return db.scalar(stmt)


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email.strip().lower())
    return db.scalar(stmt)


def create_user(db: Session, data: UserRegister) -> User:
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_session(db: Session, user_id: str) -> UserSession:
    token = generate_session_token()
    expires_at = get_session_expiry(days=7)
    session = UserSession(
        id=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_valid_session(db: Session, token: str) -> UserSession | None:
    stmt = (
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(
            UserSession.id == token,
            UserSession.expires_at > datetime.now(UTC),
        )
    )
    return db.scalar(stmt)


def delete_session(db: Session, token: str) -> bool:
    session = db.get(UserSession, token)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False
