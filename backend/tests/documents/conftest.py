import hashlib
import io
import math
import re

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.core.config import Settings
from app.main import create_app


class FixtureEmbedding:
    """Labelled deterministic test fixture. Never selected by production configuration."""

    model_name = "test-fixture-word-vectors"

    def embed(self, texts, *, query=False):
        vectors = []
        for text in texts:
            vector = [0.0] * 256
            for word in re.findall(r"\w+", text.lower()):
                index = int(hashlib.sha256(word.encode()).hexdigest(), 16) % len(vector)
                vector[index] += 1
            length = math.sqrt(sum(value * value for value in vector)) or 1
            vectors.append([value / length for value in vector])
        return vectors


@pytest.fixture
def make_pdf():
    def make(*pages, encrypted=False):
        writer = PdfWriter()
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        for text in pages:
            page = writer.add_blank_page(width=600, height=800)
            page[NameObject("/Resources")] = DictionaryObject(
                {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
            )
            stream = DecodedStreamObject()
            safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream.set_data(f"BT /F1 12 Tf 20 700 Td ({safe}) Tj ET".encode("ascii"))
            page[NameObject("/Contents")] = writer._add_object(stream)
        if encrypted:
            writer.encrypt("test-only-password")
        target = io.BytesIO()
        writer.write(target)
        return target.getvalue()

    return make


@pytest.fixture
def document_app(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'docs.db').as_posix()}",
        document_storage_dir=str(tmp_path / "files"),
        document_worker_enabled=False,
        embedding_cache_dir=str(tmp_path / "models"),
    )
    app = create_app(settings=settings)
    app.state.embedder = FixtureEmbedding()
    return app


@pytest.fixture
def document_client(document_app):
    with TestClient(document_app) as client:
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "bao",
                "email": "bao@example.test",
                "password": "FixturePassword123!",
            },
        )
        response = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "bao", "password": "FixturePassword123!"},
        )
        assert response.status_code == 200
        yield client


@pytest.fixture
def workspace_id(document_client):
    response = document_client.post("/api/v1/workspaces", json={"name": "Sinh hoc"})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def upload(document_client, workspace_id, make_pdf):
    def send(content=None, title="lecture.pdf", workspace=None):
        return document_client.post(
            f"/api/v1/workspaces/{workspace or workspace_id}/documents",
            params={"filename": title},
            content=content
            if content is not None
            else make_pdf(
                "Photosynthesis lets plants convert sunlight into chemical energy.",
                "Gross domestic product measures the value of goods and services.",
            ),
            headers={"Content-Type": "application/pdf"},
        )

    return send


@pytest.fixture
def process_document(document_app):
    import asyncio

    from app.services.documents.extract import extract_chunks
    from app.services.documents.worker import process_next

    async def fixture_processor(app, item):
        result = extract_chunks(
            app.state.document_storage.path(item.id),
            item.document_version,
            app.state.settings.document_max_pages,
            app.state.settings.document_max_chunks,
        )
        for chunk, vector in zip(
            result["chunks"],
            app.state.embedder.embed([chunk["text"] for chunk in result["chunks"]]),
            strict=True,
        ):
            chunk["embedding"] = vector
        result["model"] = app.state.embedder.model_name
        return result

    def process():
        return asyncio.run(process_next(document_app, processor=fixture_processor))

    return process
