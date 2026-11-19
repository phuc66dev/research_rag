from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.repositories import users as repository
from app.schemas.auth import AuthResponse, UserLogin, UserRead, UserRegister
from app.services import auth as service

router = APIRouter(prefix="/auth", tags=["auth"])
Db = Annotated[Session, Depends(get_db)]

SESSION_COOKIE_NAME = "edurag_session"


def extract_session_token(request: Request) -> str | None:
    # 1. Check HttpOnly cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token

    # 2. Check Authorization header: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def set_auth_cookie(response: Response, token: str, expires_at: datetime) -> None:
    # Compute max_age in seconds
    now = datetime.now(UTC)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    max_age = max(0, int((expires_at - now).total_seconds()))

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def get_current_user(request: Request, db: Db) -> User:
    token = extract_session_token(request)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Chưa đăng nhập hoặc phiên làm việc đã hết hạn.",
            },
        )

    session = repository.get_valid_session(db, token)
    if session is None or session.user is None or not session.user.is_active:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Chưa đăng nhập hoặc phiên làm việc đã hết hạn.",
            },
        )

    return session.user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_owner(resource_owner_id: str, current_user: User) -> None:
    """Helper authorization: checks whether the current user is the owner of the resource."""
    if str(resource_owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "forbidden",
                "message": "Bạn không có quyền thao tác trên tài nguyên này.",
            },
        )


@router.post("/register", response_model=UserRead, status_code=201)
def register_user(data: UserRegister, db: Db):
    user = service.register(db, data)
    return user


@router.post("/login", response_model=AuthResponse)
def login_user(data: UserLogin, response: Response, db: Db):
    user, session = service.login(db, data)
    set_auth_cookie(response, session.id, session.expires_at)
    return AuthResponse(
        user=UserRead.model_validate(user),
        token=session.id,
        expires_at=session.expires_at,
    )


@router.post("/logout", status_code=204)
def logout_user(request: Request, response: Response, db: Db):
    token = extract_session_token(request)
    service.logout(db, token)
    clear_auth_cookie(response)
    return Response(status_code=204)


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser):
    return current_user
