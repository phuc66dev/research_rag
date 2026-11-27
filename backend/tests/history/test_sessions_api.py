import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.history import history_service


@pytest.fixture
def database_url(tmp_path):
    return f"sqlite:///{(tmp_path / 'test_history.db').as_posix()}"


@pytest.fixture
def client(database_url):
    with TestClient(create_app(database_url=database_url, enable_mock_chat=True)) as c:
        yield c


def register_and_login(client: TestClient, username: str, email: str) -> dict:
    """Helper to create and authenticate a user in the test client."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "Password123!",
            "full_name": f"User {username}",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": username,
            "password": "Password123!",
        },
    )
    assert res.status_code == 200
    return res.json()["user"]


def create_workspace(client: TestClient, name: str = "Hệ cơ sở dữ liệu") -> str:
    """Helper to create a workspace."""
    res = client.post("/api/v1/workspaces", json={"name": name, "description": "Môn học"})
    assert res.status_code == 201
    return res.json()["id"]


def test_create_session_success(client):
    user = register_and_login(client, "phu_test", "phu@edurag.vn")
    workspace_id = create_workspace(client, "Khai phá dữ liệu")

    res = client.post(
        "/api/v1/chat/sessions",
        json={"workspace_id": workspace_id, "title": "Tìm hiểu thuật toán Apriori"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Tìm hiểu thuật toán Apriori"
    assert data["workspace_id"] == workspace_id
    assert data["owner_id"] == user["id"]
    assert data["message_count"] == 0
    assert "id" in data


def test_create_session_in_nonexistent_workspace_fails(client):
    register_and_login(client, "phu_test2", "phu2@edurag.vn")
    res = client.post(
        "/api/v1/chat/sessions",
        json={
            "workspace_id": "00000000-0000-0000-0000-000000000000",
            "title": "Hội thoại lỗi",
        },
    )
    assert res.status_code == 404
    assert res.json()["detail"]["code"] == "workspace_not_found"


def test_session_unauthorized_fails(client):
    res = client.post(
        "/api/v1/chat/sessions",
        json={
            "workspace_id": "00000000-0000-0000-0000-000000000000",
            "title": "Không có auth",
        },
    )
    assert res.status_code == 401


def test_list_workspace_sessions_and_all_sessions(client):
    register_and_login(client, "phu_list", "list@edurag.vn")
    w1 = create_workspace(client, "Môn 1")
    w2 = create_workspace(client, "Môn 2")

    client.post("/api/v1/chat/sessions", json={"workspace_id": w1, "title": "Phiên 1 Môn 1"})
    client.post("/api/v1/chat/sessions", json={"workspace_id": w1, "title": "Phiên 2 Môn 1"})
    client.post("/api/v1/chat/sessions", json={"workspace_id": w2, "title": "Phiên 1 Môn 2"})

    # 1. List for w1 only
    res_w1 = client.get(f"/api/v1/workspaces/{w1}/sessions")
    assert res_w1.status_code == 200
    assert len(res_w1.json()) == 2

    # 2. List all sessions
    res_all = client.get("/api/v1/chat/sessions")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 3

    # 3. Search sessions (exact & accent/case insensitive)
    res_search = client.get("/api/v1/chat/sessions?query=Môn 2")
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["title"] == "Phiên 1 Môn 2"

    # 4. Search without accents (tiếng Việt không dấu) & uppercase
    res_no_accents = client.get("/api/v1/chat/sessions?query=mon 2")
    assert res_no_accents.status_code == 200
    assert len(res_no_accents.json()) == 1
    assert res_no_accents.json()[0]["title"] == "Phiên 1 Môn 2"

    res_upper = client.get("/api/v1/chat/sessions?query=MON 2")
    assert res_upper.status_code == 200
    assert len(res_upper.json()) == 1

    res_phien1 = client.get("/api/v1/chat/sessions?query=phien 1")
    assert res_phien1.status_code == 200
    assert len(res_phien1.json()) == 2


def test_append_message_and_retrieve_with_citations(client):
    register_and_login(client, "phu_msg", "msg@edurag.vn")
    w_id = create_workspace(client, "Trí tuệ nhân tạo")

    # Create session with default title
    session_res = client.post(
        "/api/v1/chat/sessions",
        json={"workspace_id": w_id, "title": "Hội thoại mới"},
    )
    session_id = session_res.json()["id"]

    # 1. Append user message -> should auto-update session title
    user_msg_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "role": "user",
            "content": "Giải thích mạng nơ-ron tích chập CNN hoạt động như thế nào?",
            "sources": [],
            "status": "completed",
        },
    )
    assert user_msg_res.status_code == 201
    assert user_msg_res.json()["role"] == "user"

    # Verify session title auto-updated
    detail_res = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert detail_res.status_code == 200
    assert "CNN" in detail_res.json()["title"]

    # 2. Append assistant message with citations
    citations = [
        {
            "id": "c1",
            "document_id": "11111111-1111-4111-8111-111111111111",
            "document_version": "v1.0",
            "document_title": "Giao_trinh_Deep_Learning.pdf",
            "page_number": 45,
            "snippet": "Lớp tích chập (Convolutional Layer) áp dụng các bộ lọc...",
            "bbox": None,
        }
    ]
    asst_msg_res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "role": "assistant",
            "content": "Mạng CNN gồm các tầng tích chập và pooling [1].",
            "sources": citations,
            "status": "completed",
        },
    )
    assert asst_msg_res.status_code == 201
    assert len(asst_msg_res.json()["sources"]) == 1
    assert asst_msg_res.json()["sources"][0]["page_number"] == 45

    # 3. Retrieve messages via list_messages endpoint
    msgs_res = client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["sources"][0]["document_title"] == "Giao_trinh_Deep_Learning.pdf"


def test_rename_and_delete_session(client):
    register_and_login(client, "phu_crud", "crud@edurag.vn")
    w_id = create_workspace(client, "An ninh mạng")
    s_id = client.post(
        "/api/v1/chat/sessions",
        json={"workspace_id": w_id, "title": "Tiêu đề cũ"},
    ).json()["id"]

    # Rename
    patch_res = client.patch(
        f"/api/v1/chat/sessions/{s_id}",
        json={"title": "Tiêu đề mới đã đổi"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Tiêu đề mới đã đổi"

    # Delete
    del_res = client.delete(f"/api/v1/chat/sessions/{s_id}")
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    assert client.get(f"/api/v1/chat/sessions/{s_id}").status_code == 404


def test_two_users_isolation(client):
    """CRITICAL: User A cannot read, modify, or delete User B's sessions."""
    # User A (Phúc)
    register_and_login(client, "phuc_owner", "phuc@edurag.vn")
    w_a = create_workspace(client, "Sổ tay của Phúc")
    session_a = client.post(
        "/api/v1/chat/sessions",
        json={"workspace_id": w_a, "title": "Bí mật của Phúc"},
    ).json()

    # User B (Phú)
    client.cookies.clear()
    register_and_login(client, "phu_attacker", "phu_attacker@edurag.vn")

    # Workspace ownership now rejects access before listing another owner's sessions.
    res_list = client.get(f"/api/v1/workspaces/{w_a}/sessions")
    assert res_list.status_code == 403

    # User B tries to read session_a -> 403 Forbidden
    res_get = client.get(f"/api/v1/chat/sessions/{session_a['id']}")
    assert res_get.status_code == 403
    assert res_get.json()["detail"]["code"] == "forbidden"

    # User B tries to read session_a messages -> 403 Forbidden
    res_msgs = client.get(f"/api/v1/chat/sessions/{session_a['id']}/messages")
    assert res_msgs.status_code == 403

    # User B tries to patch session_a -> 403 Forbidden
    res_patch = client.patch(
        f"/api/v1/chat/sessions/{session_a['id']}",
        json={"title": "Hacked"},
    )
    assert res_patch.status_code == 403

    # User B tries to delete session_a -> 403 Forbidden
    res_del = client.delete(f"/api/v1/chat/sessions/{session_a['id']}")
    assert res_del.status_code == 403

    # Switch back to User A -> session still exists intact
    client.cookies.clear()
    register_and_login(client, "phuc_owner", "phuc@edurag.vn")
    assert client.get(f"/api/v1/chat/sessions/{session_a['id']}").status_code == 200


def test_service_record_chat_turn_and_cleanup_helpers(client):
    """Test the Python helpers provided for Phúc and Bảo."""
    user = register_and_login(client, "phu_helpers", "helpers@edurag.vn")
    w_id = create_workspace(client, "Môn thử nghiệm helper")
    session = client.post(
        "/api/v1/chat/sessions",
        json={"workspace_id": w_id, "title": "Hội thoại mới"},
    ).json()

    # Test record_chat_turn in app state db session
    app = client.app
    with app.state.session_factory() as db:
        # Fetch actual User model instance
        from app.models.user import User

        db_user = db.get(User, user["id"])

        doc_id = "99999999-9999-4999-8999-999999999999"
        citations = [
            {
                "id": "c9",
                "document_id": doc_id,
                "document_title": "Tai_lieu_sap_xoa.pdf",
                "page_number": 12,
                "snippet": "Đoạn trích từ tài liệu",
            }
        ]

        # Phúc's turn helper
        u_msg, a_msg = history_service.record_chat_turn(
            db=db,
            session_id=session["id"],
            current_user=db_user,
            query="Câu hỏi thử nghiệm?",
            answer="Câu trả lời từ RAG [1].",
            citations=citations,
            status="completed",
        )
        assert u_msg.content == "Câu hỏi thử nghiệm?"
        assert a_msg.sources[0].document_title == "Tai_lieu_sap_xoa.pdf"

        # Bảo's cleanup helper
        updated = history_service.cleanup_citations_for_document(db, doc_id)
        assert updated == 1

        # Check citation was invalidated
        msgs = history_service.list_messages(db, session["id"], db_user)
        asst = [m for m in msgs if m.role == "assistant"][0]
        assert "Đã bị xóa" in asst.sources[0].document_title
        assert "Tài liệu gốc đã bị xóa" in asst.sources[0].snippet


def test_sessions_and_messages_pagination(client):
    """Test limit, offset, and pagination headers for sessions and messages."""
    register_and_login(client, "phu_paged", "paged@edurag.vn")
    w_id = create_workspace(client, "Môn Phân Trang")

    # 1. Create 5 sessions
    session_ids = []
    for i in range(1, 6):
        res = client.post(
            "/api/v1/chat/sessions",
            json={"workspace_id": w_id, "title": f"Phiên thứ {i}"},
        )
        assert res.status_code == 201
        session_ids.append(res.json()["id"])

    # Test sessions pagination page 1 (limit 2, offset 0)
    res_p1 = client.get(f"/api/v1/chat/sessions?workspace_id={w_id}&limit=2&offset=0")
    assert res_p1.status_code == 200
    assert len(res_p1.json()) == 2
    assert res_p1.headers["X-Total-Count"] == "5"
    assert res_p1.headers["X-Offset"] == "0"
    assert res_p1.headers["X-Limit"] == "2"
    assert res_p1.headers["X-Has-More"] == "true"

    # Test sessions pagination page 2 (limit 2, offset 2)
    res_p2 = client.get(f"/api/v1/chat/sessions?workspace_id={w_id}&limit=2&offset=2")
    assert res_p2.status_code == 200
    assert len(res_p2.json()) == 2
    assert res_p2.headers["X-Has-More"] == "true"

    # Test sessions pagination page 3 (limit 2, offset 4)
    res_p3 = client.get(f"/api/v1/chat/sessions?workspace_id={w_id}&limit=2&offset=4")
    assert res_p3.status_code == 200
    assert len(res_p3.json()) == 1
    assert res_p3.headers["X-Has-More"] == "false"

    # 2. Test messages pagination in session 1
    target_sid = session_ids[0]
    for m in range(1, 5):
        client.post(
            f"/api/v1/chat/sessions/{target_sid}/messages",
            json={"role": "user", "content": f"Tin nhắn số {m}"},
        )

    # Fetch messages page 1 (limit 2, offset 0)
    res_m1 = client.get(f"/api/v1/chat/sessions/{target_sid}/messages?limit=2&offset=0")
    assert res_m1.status_code == 200
    assert len(res_m1.json()) == 2
    assert res_m1.headers["X-Total-Count"] == "4"
    assert res_m1.headers["X-Has-More"] == "true"

    # Fetch messages page 2 (limit 2, offset 2)
    res_m2 = client.get(f"/api/v1/chat/sessions/{target_sid}/messages?limit=2&offset=2")
    assert res_m2.status_code == 200
    assert len(res_m2.json()) == 2
    assert res_m2.headers["X-Has-More"] == "false"
