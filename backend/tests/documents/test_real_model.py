"""Opt-in integration test: real PDF extraction, CPU model and persistent vectors.

Default CI uses labelled embedding fixtures; this test explicitly downloads the public model.
"""

import asyncio
import os
from pathlib import Path

import pytest

from app.services.documents.worker import process_next
from app.services.retrieval.embedding import LocalEmbedding


@pytest.mark.skipif(os.environ.get("EDURAG_RUN_MODEL_TEST") != "1", reason="Opt-in model download")
def test_real_multilingual_retrieval(document_app, document_client, workspace_id, upload):
    document_app.state.settings.embedding_cache_dir = str(
        Path(__file__).resolve().parents[2] / "data" / "models"
    )
    document_app.state.embedder = LocalEmbedding(document_app.state.settings)
    item = upload().json()
    assert asyncio.run(process_next(document_app))
    status = document_client.get(f"/api/v1/documents/{item['id']}/status").json()
    assert status["status"] == "ready", status
    assert status["embedding_model"] == document_app.state.settings.embedding_model
    for query, page in [
        ("Cây xanh sử dụng ánh sáng mặt trời như thế nào?", 1),
        ("Tổng sản phẩm quốc nội đo lường điều gì?", 2),
    ]:
        response = document_client.post(
            f"/api/v1/workspaces/{workspace_id}/sources/search",
            json={
                "document_ids": [item["id"]],
                "query": query,
                "limit": 1,
            },
        )
        assert response.status_code == 200
        assert response.json()[0]["page_number"] == page
        assert response.json()[0]["score"] > 0.3
