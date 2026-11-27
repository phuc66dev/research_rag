import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import create_app
from app.models.document import Document, DocumentChunk, DocumentJob
from app.services.documents.worker import claim_job, complete_job, process_next


def test_upload_process_file_and_persistence(
    document_client, document_app, workspace_id, upload, process_document
):
    response = upload(title="../lecture.pdf")
    assert response.status_code == 202
    item = response.json()
    assert item["status"] == "queued" and item["title"] == "lecture.pdf"
    assert item["created_at"].endswith("Z") or item["created_at"].endswith("+00:00")
    assert process_document()
    result = document_client.get(f"/api/v1/documents/{item['id']}/status").json()
    assert result["status"] == "ready"
    assert result["page_count"] == 2 and result["chunk_count"] == 2
    assert document_client.get(f"/api/v1/workspaces/{workspace_id}").json()["document_count"] == 1
    original = document_client.get(f"/api/v1/documents/{item['id']}/file")
    assert original.content.startswith(b"%PDF-")
    assert original.headers["cache-control"] == "private, no-store"
    cookies = dict(document_client.cookies)
    with TestClient(create_app(settings=document_app.state.settings)) as second:
        second.cookies.update(cookies)
        assert second.get(f"/api/v1/documents/{item['id']}/status").json()["status"] == "ready"
        assert len(second.get(f"/api/v1/workspaces/{workspace_id}/documents").json()) == 1


def test_duplicate_hash_is_scoped_to_workspace(document_client, upload, process_document):
    assert upload().status_code == 202
    assert upload(title="renamed.pdf").status_code == 409
    other = document_client.post("/api/v1/workspaces", json={"name": "Other"}).json()["id"]
    assert upload(workspace=other).status_code == 202
    assert process_document() and process_document()


def test_format_limit_and_cleanup(document_client, document_app, upload, make_pdf):
    assert upload(content=b"not-pdf").status_code == 415
    assert upload(title="notes.txt").status_code == 415
    document_app.state.settings.document_max_bytes = 100
    assert upload(make_pdf("oversize")).status_code == 413
    assert not list(document_app.state.document_storage.root.glob("*"))
    with document_app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Document)) == 0


def test_streamed_limit_without_content_length(document_client, document_app, workspace_id):
    document_app.state.settings.document_max_bytes = 10
    result = document_client.post(
        f"/api/v1/workspaces/{workspace_id}/documents?filename=a.pdf",
        content=iter([b"%PDF-", b"1234567890"]),
        headers={"Content-Type": "application/pdf"},
    )
    assert result.status_code == 413
    assert not list(document_app.state.document_storage.root.glob("*"))


def test_bad_pdf_scan_and_encryption_fail_honestly(document_client, upload, make_pdf):
    for content in [b"%PDF-broken", make_pdf(""), make_pdf("secret", encrypted=True)]:
        item = upload(content).json()
        assert item["status"] == "queued"
        from app.services.documents.worker import run_pipeline

        app = document_client.app
        assert asyncio.run(process_next(app, processor=run_pipeline))
        state = document_client.get(f"/api/v1/documents/{item['id']}/status").json()
        assert state["status"] == "failed"
        assert state["error_code"] in {"invalid_pdf", "ocr_required", "encrypted_pdf"}
        assert state["chunk_count"] == 0


def test_retry_replaces_index_and_rejects_active_jobs(
    document_client, document_app, upload, process_document
):
    item = upload().json()
    url = f"/api/v1/documents/{item['id']}/retry"
    assert document_client.post(url).status_code == 409

    async def failed(app, item):
        return {"error": "embedding_unavailable"}

    assert asyncio.run(process_next(document_app, processor=failed))
    assert document_client.post(url).status_code == 202
    assert document_client.post(url).status_code == 409
    assert process_document()
    with document_app.state.session_factory() as db:
        assert db.get(DocumentJob, item["id"]).attempts == 2
        assert db.scalar(select(func.count()).select_from(DocumentChunk)) == 2


def test_two_accounts_cannot_access_documents_or_workspace(document_client, workspace_id, upload):
    item = upload().json()
    document_client.cookies.clear()
    assert document_client.get(f"/api/v1/documents/{item['id']}/file").status_code == 401
    document_client.post(
        "/api/v1/auth/register",
        json={
            "username": "other",
            "email": "other@example.test",
            "password": "FixturePassword123!",
        },
    )
    document_client.post(
        "/api/v1/auth/login", json={"username_or_email": "other", "password": "FixturePassword123!"}
    )
    assert document_client.get("/api/v1/workspaces").json() == []
    for suffix in ("status", "file"):
        assert document_client.get(f"/api/v1/documents/{item['id']}/{suffix}").status_code == 403
    assert document_client.post(f"/api/v1/documents/{item['id']}/retry").status_code == 403
    assert document_client.delete(f"/api/v1/documents/{item['id']}").status_code == 403
    assert document_client.get(f"/api/v1/workspaces/{workspace_id}/documents").status_code == 403
    assert upload().status_code == 403
    assert (
        document_client.post(
            f"/api/v1/workspaces/{workspace_id}/sources/search",
            json={"document_ids": [item["id"]], "query": "sunlight"},
        ).status_code
        == 403
    )
    assert document_client.delete(f"/api/v1/workspaces/{workspace_id}").status_code == 403
    assert (
        document_client.patch(
            f"/api/v1/workspaces/{workspace_id}", json={"name": "hacked"}
        ).status_code
        == 403
    )
    assert (
        document_client.post(
            "/api/v1/chat/sessions", json={"workspace_id": workspace_id}
        ).status_code
        == 403
    )


def test_delete_cleans_vectors_file_and_history(
    document_client, document_app, workspace_id, upload, process_document
):
    item = upload().json()
    assert process_document()
    session = document_client.post(
        "/api/v1/chat/sessions", json={"workspace_id": workspace_id}
    ).json()
    message = document_client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        json={
            "role": "assistant",
            "content": "answer",
            "sources": [
                {
                    "id": "c1",
                    "document_id": item["id"],
                    "document_title": item["title"],
                    "snippet": "old snippet",
                }
            ],
        },
    )
    assert message.status_code == 201
    assert document_client.delete(f"/api/v1/documents/{item['id']}").status_code == 204
    assert not document_app.state.document_storage.path(item["id"]).exists()
    assert document_client.get(f"/api/v1/documents/{item['id']}/file").status_code == 404
    with document_app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(DocumentChunk)) == 0
        assert db.get(DocumentJob, item["id"]) is None
    sources = document_client.get(f"/api/v1/chat/sessions/{session['id']}/messages").json()[0][
        "sources"
    ]
    assert "xóa" in sources[0]["snippet"]
    assert upload().status_code == 202


def test_late_job_cannot_recreate_deleted_source(document_client, document_app, upload):
    item = upload().json()
    claimed, generation, token = claim_job(document_app)
    assert document_client.delete(f"/api/v1/documents/{item['id']}").status_code == 204
    assert not complete_job(document_app, claimed, generation, token, {"error": "old_job"})
    assert document_client.get(f"/api/v1/documents/{item['id']}/status").status_code == 404


def test_expired_job_can_be_retried(document_client, document_app, upload, process_document):
    item = upload().json()
    claim_job(document_app)
    with document_app.state.session_factory() as db:
        db.get(DocumentJob, item["id"]).started_at = datetime.now(UTC) - timedelta(days=1)
        db.commit()
    assert claim_job(document_app) is None
    state = document_client.get(f"/api/v1/documents/{item['id']}/status").json()
    assert state["status"] == "failed" and state["error_code"] == "processing_interrupted"
    assert document_client.post(f"/api/v1/documents/{item['id']}/retry").status_code == 202
    assert process_document()


def test_workspace_deletion_cleans_documents_and_history(
    document_client, document_app, workspace_id, upload, process_document
):
    item = upload().json()
    assert process_document()
    session = document_client.post(
        "/api/v1/chat/sessions", json={"workspace_id": workspace_id}
    ).json()
    message = document_client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        json={"role": "user", "content": "test question"},
    )
    assert message.status_code == 201
    assert document_client.delete(f"/api/v1/workspaces/{workspace_id}").status_code == 204
    assert not document_app.state.document_storage.path(item["id"]).exists()
    assert document_client.get(f"/api/v1/chat/sessions/{session['id']}").status_code == 404
    with document_app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Document)) == 0
        from app.models.message import ChatMessage

        assert db.scalar(select(func.count()).select_from(ChatMessage)) == 0


def test_origin_and_missing_resource(document_client, workspace_id, upload):
    assert (
        document_client.post(
            f"/api/v1/workspaces/{workspace_id}/documents?filename=a.pdf",
            content=b"%PDF-",
            headers={"Content-Type": "application/pdf", "Origin": "https://evil.test"},
        ).status_code
        == 403
    )
    assert document_client.get(f"/api/v1/documents/{uuid4()}/status").status_code == 404


def test_search_scope_pages_and_versions(document_client, workspace_id, upload, process_document):
    item = upload().json()
    url = f"/api/v1/workspaces/{workspace_id}/sources/search"
    body = {"document_ids": [item["id"]], "query": "sunlight plants photosynthesis"}
    assert document_client.post(url, json=body).status_code == 409
    assert process_document()
    response = document_client.post(url, json=body)
    assert response.status_code == 200
    first = response.json()[0]
    assert first["page_number"] == 1 and first["bbox"] is None
    assert first["document_version"] == item["document_version"]
    assert first["document_id"] == item["id"]
    other = document_client.post("/api/v1/workspaces", json={"name": "Other"}).json()["id"]
    assert (
        document_client.post(f"/api/v1/workspaces/{other}/sources/search", json=body).status_code
        == 403
    )
    assert document_client.post(url, json={**body, "document_ids": []}).status_code == 422
    assert document_client.post(url, json={**body, "query": " "}).status_code == 422


def test_workspace_quota_does_not_store_extra_file(document_app, upload, make_pdf):
    document_app.state.settings.document_max_per_workspace = 1
    assert upload().status_code == 202
    response = upload(make_pdf("A different file"))
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "document_limit"
    assert len(list(document_app.state.document_storage.root.glob("*.pdf"))) == 1


def test_search_never_returns_unselected_document(
    document_client, document_app, workspace_id, upload, make_pdf, process_document
):
    selected = upload().json()
    other = upload(make_pdf("Sunlight plants sunlight secret unselected"), title="other.pdf").json()
    assert process_document() and process_document()
    result = document_client.post(
        f"/api/v1/workspaces/{workspace_id}/sources/search",
        json={"document_ids": [selected["id"]], "query": "sunlight plants"},
    )
    assert result.status_code == 200 and result.json()
    assert {row["document_id"] for row in result.json()} == {selected["id"]}
    assert other["id"] not in {row["document_id"] for row in result.json()}


def test_expired_lease_cannot_overwrite_retry(document_app, document_client, upload):
    item = upload().json()
    claimed, generation, token = claim_job(document_app)
    with document_app.state.session_factory() as db:
        db.get(DocumentJob, item["id"]).started_at = datetime.now(UTC) - timedelta(days=1)
        db.commit()
    claim_job(document_app)
    assert document_client.post(f"/api/v1/documents/{item['id']}/retry").status_code == 202
    assert not complete_job(document_app, claimed, generation, token, {"error": "stale_result"})
    assert (
        document_client.get(f"/api/v1/documents/{item['id']}/status").json()["status"] == "queued"
    )


def test_file_is_not_exposed_before_ready(document_client, upload):
    item = upload().json()
    response = document_client.get(f"/api/v1/documents/{item['id']}/file")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "document_not_ready"


def test_worker_rechecks_ownership_before_extracting(document_app, workspace_id, upload):
    from app.models.workspace import Workspace

    item = upload().json()
    with document_app.state.session_factory() as db:
        db.get(Workspace, workspace_id).owner_id = None
        db.commit()
    assert claim_job(document_app) is None
    with document_app.state.session_factory() as db:
        assert db.get(Document, item["id"]).error_code == "source_access_revoked"


def test_delete_retry_after_file_error_preserves_history_marker_once(
    document_client, document_app, workspace_id, upload, process_document, monkeypatch
):
    from pathlib import Path

    import pytest

    item = upload().json()
    assert process_document()
    session = document_client.post(
        "/api/v1/chat/sessions", json={"workspace_id": workspace_id}
    ).json()
    assert (
        document_client.post(
            f"/api/v1/chat/sessions/{session['id']}/messages",
            json={
                "role": "assistant",
                "content": "answer",
                "sources": [
                    {
                        "id": "c1",
                        "document_id": item["id"],
                        "document_title": item["title"],
                        "snippet": "text",
                    }
                ],
            },
        ).status_code
        == 201
    )
    original_unlink = Path.unlink
    target = document_app.state.document_storage.path(item["id"])

    def deny_unlink(path, *args, **kwargs):
        if path == target:
            raise PermissionError("Test-only file lock")
        return original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", deny_unlink)
        with pytest.raises(PermissionError):
            document_client.delete(f"/api/v1/documents/{item['id']}")
    assert (
        document_client.get(f"/api/v1/documents/{item['id']}/status").json()["status"] == "deleting"
    )
    assert document_client.get(f"/api/v1/documents/{item['id']}/file").status_code == 410
    assert document_client.delete(f"/api/v1/documents/{item['id']}").status_code == 204
    sources = document_client.get(f"/api/v1/chat/sessions/{session['id']}/messages").json()[0][
        "sources"
    ]
    assert sources[0]["document_title"].count("(Đã bị xóa)") == 1
