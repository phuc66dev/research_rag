"""Local HTTP server exercises the real provider transport without paid APIs."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.core.config import Settings
from app.services.rag.provider import ProviderError, stream_completion


@pytest.fixture
def server():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.server.received = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.auth = self.headers.get("Authorization")
            self.server.path = self.path
            self.send_response(self.server.status)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for block in self.server.blocks:
                self.wfile.write(block.encode("utf-8"))
                self.wfile.flush()

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.status = 200
    httpd.blocks = [
        'data: {"choices":[{"index":0,"delta":{"content":"Tiếng Việt [1]."},'
        '"finish_reason":null}]}\n\n',
        'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',
        "data: [DONE]\n\n",
    ]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    settings = Settings(
        _env_file=None,
        llm_base_url=f"http://127.0.0.1:{httpd.server_port}/v1",
        llm_model="test-only",
        llm_api_key="test-only-secret",
    )
    yield httpd, settings
    httpd.shutdown()
    thread.join()
    httpd.server_close()


def test_real_transport_sends_auth_and_decodes_utf8(server):
    httpd, settings = server
    assert list(stream_completion(settings, [{"role": "user", "content": "Question"}])) == [
        "Tiếng Việt [1]."
    ]
    assert httpd.path == "/v1/chat/completions"
    assert httpd.auth == "Bearer test-only-secret"
    assert httpd.received["stream"] is True
    assert httpd.received["model"] == "test-only"


@pytest.mark.parametrize("case", ["http-error", "missing-done", "truncated", "bad-json"])
def test_transport_rejects_incomplete_or_failed_streams(server, case):
    httpd, settings = server
    if case == "http-error":
        httpd.status = 401
        httpd.blocks = ["test-only-secret upstream response must not escape"]
    elif case == "missing-done":
        httpd.blocks = httpd.blocks[:1]
    elif case == "truncated":
        httpd.blocks[1] = httpd.blocks[1].replace('"stop"', '"length"')
    else:
        httpd.blocks = ["data: {broken\n\n"]
    with pytest.raises(ProviderError) as caught:
        list(stream_completion(settings, []))
    assert "test-only-secret" not in str(caught.value)


@pytest.mark.parametrize("status,expected", [(401, "API key"), (403, "API key"), (429, "hạn mức")])
def test_upstream_status_has_actionable_error_without_body(server, status, expected):
    httpd, settings = server
    httpd.status = status
    httpd.blocks = ["test-only-secret upstream body"]
    with pytest.raises(ProviderError, match=expected) as caught:
        list(stream_completion(settings, []))
    assert "test-only-secret" not in str(caught.value)


@pytest.mark.parametrize("status,expected", [(404, "tải hoặc tạo model"), (500, "GPU/driver")])
def test_ollama_status_reports_model_or_runner_failure(server, monkeypatch, status, expected):
    import http.client

    httpd, settings = server
    original_connection = http.client.HTTPConnection
    # Exercise local-Ollama detection against the test HTTP server; never call real Ollama.
    monkeypatch.setattr(
        http.client,
        "HTTPConnection",
        lambda host, port, timeout: original_connection(
            "127.0.0.1", httpd.server_port, timeout=timeout
        ),
    )
    settings.llm_base_url = "http://127.0.0.1:11434/v1"
    httpd.status = status
    httpd.blocks = ["test-only-secret CUDA runner diagnostic"]
    with pytest.raises(ProviderError, match=expected) as caught:
        list(stream_completion(settings, []))
    assert "test-only-secret" not in str(caught.value)
