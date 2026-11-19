from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories import users as repository
from app.schemas.auth import UserLogin, UserRegister


def register(db: Session, data: UserRegister) -> User:
    if repository.get_user_by_username(db, data.username):
        raise HTTPException(
            status_code=409,
            detail={"code": "username_already_exists", "message": "Tên đăng nhập đã được sử dụng."},
        )
    if repository.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=409,
            detail={"code": "email_already_exists", "message": "Email đã được sử dụng."},
        )

    user = repository.create_user(db, data)
    return user


def login(db: Session, data: UserLogin) -> tuple[User, UserSession]:
    identifier = data.username_or_email
    user = (
        repository.get_user_by_email(db, identifier)
        if "@" in identifier
        else repository.get_user_by_username(db, identifier)
    )

    if user is None:
        # Fallback check if user entered username as email or vice versa
        user = (
            repository.get_user_by_username(db, identifier)
            if "@" in identifier
            else repository.get_user_by_email(db, identifier)
        )

    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "invalid_credentials",
                "message": "Tên đăng nhập/email hoặc mật khẩu không chính xác.",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail={"code": "user_inactive", "message": "Tài khoản người dùng đã bị khóa."},
        )

    session = repository.create_session(db, user.id)
    return user, session


def logout(db: Session, token: str | None) -> None:
    if token:
        repository.delete_session(db, token)
