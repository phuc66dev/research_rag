"""Real PDF/retrieval/auth/history integration with a labelled provider fixture only."""

import asyncio
import json

import pytest

from app.services.rag import generation, provider
from app.services.rag.contracts import ChatRequest


@pytest.fixture
def chat(document_client, document_app, workspace_id, upload, process_document, monkeypatch):
    document_app.state.settings.llm_base_url = "http://127.0.0.1:9/v1"
    document_app.state.settings.llm_model = "test-fixture-only"
    source = upload().json()
    process_document()
    session = document_client.post(
        "/api/v1/chat/sessions", json={"workspace_id": workspace_id}
    ).json()
    calls = []

    def fixture_provider(settings, messages):
        calls.append(messages)
        yield "Photosynthesis uses sunlight "
        yield "to make chemical energy [1]."

    monkeypatch.setattr(provider, "stream_completion", fixture_provider)
    body = {
        "workspace_id": workspace_id,
        "document_ids": [source["id"]],
        "query": "Photosynthesis sunlight chemical energy",
    }
    return session["id"], body, calls


def events(response):
    assert response.status_code == 200, response.text
    result = []
    for block in response.text.strip().split("\n\n"):
        lines = block.splitlines()
        result.append((lines[0][7:], json.loads(lines[1][6:])))
    return result


def test_send_save_resume_and_follow_up(document_client, chat):
    session_id, body, calls = chat
    received = events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    names = [name for name, _ in received]
    assert names.index("citations") < names.index("token") < names.index("done")
    assert received[-1][1]["mock"] is False
    detail = document_client.get(f"/api/v1/chat/sessions/{session_id}").json()
    assert len(detail["messages"]) == 2
    user, assistant = detail["messages"]
    assert user["sources"][0]["document_id"] == body["document_ids"][0]
    assert assistant["id"] == received[-1][1]["message_id"]
    assert assistant["status"] == "completed"
    assert assistant["sources"][0]["page_number"] == 1
    assert "sunlight" in assistant["sources"][0]["snippet"]
    assert detail["title"] == body["query"]
    body["query"] = "Explain sunlight again"
    events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    assert len(document_client.get(f"/api/v1/chat/sessions/{session_id}").json()["messages"]) == 4
    assert json.loads(calls[-1][1]["content"])["cau_hoi_truoc"] == [user["content"]]
    assert json.loads(calls[-1][1]["content"])["cau_tra_loi_truoc_cung_nguon"] == [
        assistant["content"]
    ]


def test_history_survives_new_app_instance(document_client, document_app, chat):
    from fastapi.testclient import TestClient

    from app.main import create_app

    session_id, body, _ = chat
    events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    with TestClient(create_app(settings=document_app.state.settings)) as fresh:
        fresh.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "bao",
                "password": "FixturePassword123!",
            },
        )
        response = fresh.get(f"/api/v1/chat/sessions/{session_id}")
        assert response.status_code == 200
        assert [message["role"] for message in response.json()["messages"]] == ["user", "assistant"]
        assert response.json()["messages"][-1]["status"] == "completed"


def test_changing_sources_excludes_old_answer_context(
    document_client, chat, upload, make_pdf, process_document
):
    session_id, body, calls = chat
    events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    other = upload(content=make_pdf("Gross domestic product measures goods and services.")).json()
    process_document()
    body = {**body, "document_ids": [other["id"]], "query": "Gross domestic product goods services"}
    events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    context = json.loads(calls[-1][1]["content"])
    assert context["cau_hoi_truoc"] == []
    assert context["cau_tra_loi_truoc_cung_nguon"] == []
    assert "Photosynthesis" not in context["nguon_hien_tai"][0]["van_ban"]


def test_missing_configuration_writes_no_messages(document_client, document_app, chat):
    session_id, body, calls = chat
    document_app.state.settings.llm_model = ""
    assert (
        document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body).status_code
        == 503
    )
    assert document_client.get(f"/api/v1/chat/sessions/{session_id}").json()["messages"] == []
    assert not calls


def test_provider_failure_keeps_partial_without_done(document_client, chat, monkeypatch):
    session_id, body, _ = chat

    def broken(*args):
        yield "Partial answer"
        raise provider.ProviderError("Provider fixture failed")

    monkeypatch.setattr(provider, "stream_completion", broken)
    received = events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    assert received[-1][0] == "error"
    assert "done" not in [name for name, _ in received]
    message = document_client.get(f"/api/v1/chat/sessions/{session_id}").json()["messages"][-1]
    assert message["content"] == "Partial answer"
    assert message["status"] == "error"


@pytest.mark.parametrize("answer", ["", "Invalid reference [99]."])
def test_empty_or_invalid_citation_is_not_completed(document_client, chat, monkeypatch, answer):
    session_id, body, _ = chat

    def fixture_provider(*args):
        yield answer

    monkeypatch.setattr(provider, "stream_completion", fixture_provider)
    received = events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    assert received[-1][0] == "error"
    assert not any(name == "done" for name, _ in received)


def test_turn_placeholder_transaction_rolls_back_on_failure(
    document_client, document_app, chat, monkeypatch
):
    from app.models.user import User
    from app.repositories import sessions as repository
    from app.services.history import history_service

    session_id, body, _ = chat
    owner = document_client.get("/api/v1/auth/me").json()["id"]
    original = repository.add_message

    def fail_assistant(db, session, role, *args, **kwargs):
        if role == "assistant":
            raise RuntimeError("Test-only write failure")
        return original(db, session, role, *args, **kwargs)

    monkeypatch.setattr(repository, "add_message", fail_assistant)
    with document_app.state.session_factory() as db:
        with pytest.raises(RuntimeError, match="Test-only"):
            history_service.begin_stream(db, session_id, db.get(User, owner), body["query"], [], [])
    detail = document_client.get(f"/api/v1/chat/sessions/{session_id}").json()
    assert detail["messages"] == []
    assert detail["title"] == "Hội thoại mới"


def test_parallel_turn_is_rejected_and_release_allows_next(document_client, document_app, chat):
    session_id, body, calls = chat
    release = generation.claim_turn(document_app, session_id)
    try:
        assert (
            document_client.post(
                f"/api/v1/chat/sessions/{session_id}/stream", json=body
            ).status_code
            == 409
        )
        assert not calls
    finally:
        release()
    received = events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    assert received[-1][0] == "done"


def test_two_accounts_cannot_stream_another_session(document_client, document_app, chat):
    session_id, body, calls = chat
    document_client.post("/api/v1/auth/logout")
    path = f"/api/v1/chat/sessions/{session_id}/stream"
    assert document_client.post(path, json=body).status_code == 401
    document_client.post(
        "/api/v1/auth/register",
        json={
            "username": "other",
            "email": "other@example.test",
            "password": "FixturePassword123!",
        },
    )
    document_client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "other",
            "password": "FixturePassword123!",
        },
    )
    assert document_client.post(path, json=body).status_code == 403
    release = generation.claim_turn(document_app, session_id)
    try:
        assert document_client.post(path, json=body).status_code == 403
    finally:
        release()
    assert not calls


def test_sources_and_workspace_must_match(document_client, chat, upload, make_pdf):
    session_id, body, calls = chat
    other = document_client.post("/api/v1/workspaces", json={"name": "Other"}).json()["id"]
    foreign_source = upload(workspace=other).json()["id"]
    path = f"/api/v1/chat/sessions/{session_id}/stream"
    assert document_client.post(path, json={**body, "workspace_id": other}).status_code == 403
    assert (
        document_client.post(path, json={**body, "document_ids": [foreign_source]}).status_code
        == 403
    )
    pending = upload(content=make_pdf("Unprocessed source"), title="pending.pdf").json()
    assert (
        document_client.post(path, json={**body, "document_ids": [pending["id"]]}).status_code
        == 409
    )
    assert not calls


def test_no_evidence_does_not_call_provider(document_client, document_app, chat, monkeypatch):
    session_id, body, calls = chat
    monkeypatch.setattr(generation, "search_sources", lambda *args, **kwargs: [])
    received = events(document_client.post(f"/api/v1/chat/sessions/{session_id}/stream", json=body))
    assert received[1] == ("citations", {"citations": [], "mock": False})
    assert received[-1][0] == "done"
    assert not calls


def test_disconnect_keeps_interrupted_tokens_and_releases_lock(document_app, document_client, chat):
    from app.models.user import User
    from app.services.history import history_service

    session_id, body, _ = chat
    owner = document_client.get("/api/v1/auth/me").json()["id"]
    with document_app.state.session_factory() as db:
        user = db.get(User, owner)
        prepared = generation.prepare_turn(db, document_app, session_id, ChatRequest(**body), user)

    async def consume():
        release = generation.claim_turn(document_app, session_id)
        iterator = generation.answer_events(document_app, session_id, None, prepared, release)
        while "event: token" not in await anext(iterator):
            pass
        await iterator.aclose()
        generation.claim_turn(document_app, session_id)()

    asyncio.run(consume())
    with document_app.state.session_factory() as db:
        detail = history_service.get_session_detail(db, session_id, db.get(User, owner))
        assert detail.messages[-1].status == "interrupted"
        assert detail.messages[-1].content == "Photosynthesis uses sunlight "
