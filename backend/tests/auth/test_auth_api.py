import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth import require_owner
from app.main import create_app


@pytest.fixture
def database_url(tmp_path):
    return f"sqlite:///{(tmp_path / 'test_auth.db').as_posix()}"


@pytest.fixture
def client(database_url):
    with TestClient(create_app(database_url=database_url, enable_mock_chat=True)) as c:
        yield c


def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "phu_dev",
            "email": "phu.dev@edurag.vn",
            "password": "Password123!",
            "full_name": "Nguyễn Văn Phú",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "phu_dev"
    assert data["email"] == "phu.dev@edurag.vn"
    assert data["full_name"] == "Nguyễn Văn Phú"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data

    # Verify session cookie was NOT set on registration (user must login separately)
    assert "edurag_session" not in response.cookies


def test_register_duplicate_username_fails(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "phu_user1",
            "email": "user1@edurag.vn",
            "password": "Password123!",
        },
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "PHU_USER1",  # Test case-insensitivity
            "email": "different@edurag.vn",
            "password": "Password123!",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "username_already_exists"


def test_register_duplicate_email_fails(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "user_a",
            "email": "duplicate@edurag.vn",
            "password": "Password123!",
        },
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "user_b",
            "email": "DUPLICATE@edurag.vn",
            "password": "Password123!",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "email_already_exists"


def test_register_short_password_fails(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "shortpass",
            "email": "short@edurag.vn",
            "password": "123",
        },
    )
    assert response.status_code == 422


def test_login_success_with_username_and_email(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "sinhvien",
            "email": "sinhvien@hcmus.edu.vn",
            "password": "SecretPassword123",
            "full_name": "Sinh Viên A",
        },
    )

    # 1. Login with username
    res1 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "sinhvien",
            "password": "SecretPassword123",
        },
    )
    assert res1.status_code == 200
    assert res1.json()["user"]["username"] == "sinhvien"
    assert "edurag_session" in res1.cookies

    # 2. Login with email
    res2 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "sinhvien@hcmus.edu.vn",
            "password": "SecretPassword123",
        },
    )
    assert res2.status_code == 200
    assert res2.json()["user"]["email"] == "sinhvien@hcmus.edu.vn"


def test_login_invalid_credentials(client):
    # Unknown user
    res1 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "nonexistent",
            "password": "WrongPassword",
        },
    )
    assert res1.status_code == 401
    assert res1.json()["detail"]["code"] == "invalid_credentials"

    # Known user, wrong password
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "realuser",
            "email": "real@edurag.vn",
            "password": "CorrectPassword123",
        },
    )
    res2 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "realuser",
            "password": "WrongPassword",
        },
    )
    assert res2.status_code == 401
    assert res2.json()["detail"]["code"] == "invalid_credentials"


def test_get_me_with_cookie_and_bearer_token(client):
    # Register user
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "username": "tokentest",
            "email": "token@edurag.vn",
            "password": "TokenPassword123",
        },
    )
    user_id = reg.json()["id"]

    # Login to obtain session
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "tokentest",
            "password": "TokenPassword123",
        },
    )
    token = login_res.json()["token"]

    # 1. Access with cookie (automatically stored in test client session)
    res_cookie = client.get("/api/v1/auth/me")
    assert res_cookie.status_code == 200
    assert res_cookie.json()["id"] == user_id

    # 2. Access with Bearer token in fresh headers
    client.cookies.clear()
    res_bearer = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_bearer.status_code == 200
    assert res_bearer.json()["id"] == user_id


def test_get_me_unauthorized_fails(client):
    client.cookies.clear()
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["detail"]["code"] == "unauthorized"


def test_logout_invalidates_session(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "logout_user",
            "email": "logout@edurag.vn",
            "password": "LogoutPassword123",
        },
    )
    # Login to establish session
    client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "logout_user",
            "password": "LogoutPassword123",
        },
    )
    # Check currently logged in
    assert client.get("/api/v1/auth/me").status_code == 200

    # Logout
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 204

    # Subsequent /me should return 401
    assert client.get("/api/v1/auth/me").status_code == 401


def test_two_accounts_isolation_and_require_owner(client):
    """Verify two accounts cannot access each other's protected resources."""
    # Account 1: User A (Phúc)
    res_a = client.post(
        "/api/v1/auth/register",
        json={
            "username": "phuc_account",
            "email": "phuc@edurag.vn",
            "password": "PhucPassword123",
        },
    )
    user_a = res_a.json()

    # Account 2: User B (Phú)
    client.cookies.clear()
    res_b = client.post(
        "/api/v1/auth/register",
        json={
            "username": "phu_account",
            "email": "phu@edurag.vn",
            "password": "PhuPassword123",
        },
    )
    user_b = res_b.json()

    assert user_a["id"] != user_b["id"]

    # Login as User B
    client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "phu_account",
            "password": "PhuPassword123",
        },
    )

    # When logged in as User B:
    me = client.get("/api/v1/auth/me").json()
    assert me["id"] == user_b["id"]
    assert me["username"] == "phu_account"

    # Test require_owner helper directly
    class MockUser:
        def __init__(self, uid):
            self.id = uid

    current_user_b = MockUser(user_b["id"])

    # Owner check for own resource should pass
    require_owner(user_b["id"], current_user_b)

    # Owner check for resource owned by User A should raise 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        require_owner(user_a["id"], current_user_b)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "forbidden"
