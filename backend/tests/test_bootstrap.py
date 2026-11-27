"""Behavior at the team's API boundaries, using a real temporary SQLite database."""

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def authenticate(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bootstrap",
            "email": "bootstrap@example.test",
            "password": "Fixture123!",
        },
    )
    response = client.post(
        "/api/v1/auth/login", json={"username_or_email": "bootstrap", "password": "Fixture123!"}
    )
    assert response.status_code == 200


@pytest.fixture
def database_url(tmp_path):
    return f"sqlite:///{(tmp_path / 'test.db').as_posix()}"


@pytest.fixture
def client(database_url):
    with TestClient(create_app(database_url=database_url, enable_mock_chat=True)) as client:
        authenticate(client)
        yield client


def test_health_marks_development_mode_and_missing_rag(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["rag_ready"] is False
    assert response.json()["mock_chat_enabled"] is True


def test_workspace_round_trip_and_delete(client):
    created = client.post("/api/v1/workspaces", json={"name": "  Kinh tế vĩ mô  "})
    assert created.status_code == 201
    item = created.json()
    assert item["name"] == "Kinh tế vĩ mô"
    assert item["document_count"] == 0
    workspace_id = item["id"]
    assert client.get("/api/v1/workspaces").json()[0]["id"] == workspace_id
    renamed = client.patch(f"/api/v1/workspaces/{workspace_id}", json={"name": "Mạng máy tính"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Mạng máy tính"
    assert client.delete(f"/api/v1/workspaces/{workspace_id}").status_code == 204
    assert client.get("/api/v1/workspaces").json() == []
    assert client.get(f"/api/v1/workspaces/{workspace_id}").status_code == 404


@pytest.mark.parametrize("name", ["", "  ", "x" * 101])
def test_invalid_workspace_name_is_rejected(client, name):
    assert client.post("/api/v1/workspaces", json={"name": name}).status_code == 422


def test_workspace_survives_new_application_instance(database_url):
    with TestClient(create_app(database_url=database_url)) as first:
        authenticate(first)
        created = first.post("/api/v1/workspaces", json={"name": "Xác suất"}).json()
    with TestClient(create_app(database_url=database_url)) as second:
        authenticate(second)
        assert second.get("/api/v1/workspaces").json()[0]["id"] == created["id"]


def test_patch_rejects_null_and_blank_names(client):
    item = client.post("/api/v1/workspaces", json={"name": "Môn học"}).json()
    for name in [None, "  "]:
        assert (
            client.patch(f"/api/v1/workspaces/{item['id']}", json={"name": name}).status_code == 422
        )
    assert client.get(f"/api/v1/workspaces/{item['id']}").json()["name"] == "Môn học"


def test_unknown_workspace_does_not_create_document_collection(client):
    assert client.get(f"/api/v1/workspaces/{uuid4()}/documents").status_code == 404


def mock_request():
    return {
        "workspace_id": str(uuid4()),
        "document_ids": [str(uuid4())],
        "query": "Tổng cầu gồm những thành phần nào?",
    }


def test_mock_stream_orders_citations_before_tokens_and_marks_demo(client):
    body = mock_request()
    response = client.post("/api/v1/chat/mock/stream", json=body)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = block.splitlines()
        event = next(line.removeprefix("event: ") for line in lines if line.startswith("event: "))
        payload = next(line.removeprefix("data: ") for line in lines if line.startswith("data: "))
        events.append((event, json.loads(payload)))
    names = [event for event, _ in events]
    assert names[0] == "status"
    assert names.index("citations") < names.index("token")
    assert names[-1] == "done"
    citations = next(payload["citations"] for event, payload in events if event == "citations")
    assert citations[0]["document_id"] == body["document_ids"][0]
    assert citations[0]["page_number"] == 42
    assert citations[0]["bbox"] is None
    assert events[-1][1]["provider"] == "mock"
    assert "minh họa" in "".join(p["text"] for event, p in events if event == "token")


def test_mock_can_be_disabled(database_url):
    with TestClient(create_app(database_url=database_url, enable_mock_chat=False)) as client:
        assert client.post("/api/v1/chat/mock/stream", json=mock_request()).status_code == 404


def test_chat_requires_nonempty_scope_and_question(client):
    body = mock_request()
    assert (
        client.post("/api/v1/chat/mock/stream", json={**body, "document_ids": []}).status_code
        == 422
    )
    assert client.post("/api/v1/chat/mock/stream", json={**body, "query": "  "}).status_code == 422


def test_real_chat_never_silently_uses_mock(client):
    response = client.post(f"/api/v1/chat/sessions/{uuid4()}/stream", json=mock_request())
    assert response.status_code == 501
    assert response.json()["detail"]["code"] == "not_implemented"


def test_workspace_timestamps_include_utc_offset(client):
    from datetime import datetime, timedelta

    item = client.post("/api/v1/workspaces", json={"name": "Múi giờ"}).json()
    for field in ("created_at", "updated_at"):
        value = datetime.fromisoformat(item[field])
        assert value.utcoffset() == timedelta(0)


@pytest.mark.parametrize("url", ["sqlite:///:memory:", "sqlite://"])
def test_in_memory_database_is_shared_with_request_threads(url):
    with TestClient(create_app(database_url=url), raise_server_exceptions=False) as client:
        authenticate(client)
        response = client.post("/api/v1/workspaces", json={"name": "Trong bộ nhớ"})
        assert response.status_code == 201
        assert len(client.get("/api/v1/workspaces").json()) == 1


@pytest.mark.parametrize("resource", ["documents"])
def test_document_collection_is_implemented_and_initially_empty(client, resource):
    item = client.post("/api/v1/workspaces", json={"name": "Môn học"}).json()
    response = client.get(f"/api/v1/workspaces/{item['id']}/{resource}")
    assert response.status_code == 200
    assert response.json() == []


def test_openapi_exposes_sse_media_type_and_unimplemented_statuses(client):
    paths = client.get("/openapi.json").json()["paths"]
    mock_response = paths["/api/v1/chat/mock/stream"]["post"]["responses"]["200"]
    assert "text/event-stream" in mock_response.get("content", {})
    for path, method in [
        ("/api/v1/chat/sessions/{session_id}/stream", "post"),
    ]:
        responses = paths[path][method]["responses"]
        assert "501" in responses
        assert "200" not in responses
    document_path = paths["/api/v1/workspaces/{workspace_id}/documents"]
    assert "200" in document_path["get"]["responses"]
    assert "202" in document_path["post"]["responses"]
    assert "application/pdf" in document_path["post"]["requestBody"]["content"]
