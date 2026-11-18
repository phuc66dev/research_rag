"""Deterministic UI transport fixture, never retrieval or factual AI output."""

import json
from collections.abc import Iterator
from uuid import uuid4

from app.services.rag.contracts import ChatRequest, Citation


def sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def mock_events(body: ChatRequest) -> Iterator[str]:
    yield sse("status", {"stage": "retrieving", "mock": True})
    citation = Citation(
        id="c1",
        document_id=body.document_ids[0],
        document_version="mock-v1",
        document_title="Tai_lieu_minh_hoa.pdf",
        page_number=42,
        snippet="Đây là đoạn nguồn minh họa giao diện, không phải tài liệu đã truy xuất.",
    )
    yield sse("citations", {"citations": [citation.model_dump(mode="json")], "mock": True})
    for text in ["Đây là câu trả lời minh họa ", "để kiểm tra streaming và popup nguồn [1]."]:
        yield sse("token", {"text": text})
    yield sse("done", {"message_id": str(uuid4()), "provider": "mock", "mock": True})
