"""OpenAI-compatible Chat Completions SSE transport; no SDK, retries or fallback."""

import http.client
import json
import time
from urllib.parse import urlsplit


class ProviderError(Exception):
    pass


def stream_completion(settings, messages):
    url = urlsplit(settings.llm_base_url.rstrip("/") + "/chat/completions")
    connection_type = (
        http.client.HTTPSConnection if url.scheme == "https" else http.client.HTTPConnection
    )
    connection = connection_type(url.hostname, url.port, timeout=30)
    started = time.monotonic()
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    key = settings.llm_api_key.get_secret_value()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        connection.request(
            "POST",
            url.path,
            body=json.dumps(
                {
                    "model": settings.llm_model,
                    "messages": messages,
                    "stream": True,
                    "max_tokens": settings.llm_max_tokens,
                }
            ).encode("utf-8"),
            headers=headers,
        )
        response = connection.getresponse()
        if response.status != 200:
            if url.hostname in {"localhost", "127.0.0.1", "::1"} and url.port == 11434:
                if response.status == 404:
                    raise ProviderError(
                        "Ollama chưa có model được cấu hình. Hãy tải hoặc tạo model rồi thử lại."
                    )
                if response.status >= 500:
                    raise ProviderError(
                        "Ollama không khởi chạy được model. "
                        "Kiểm tra GPU/driver hoặc dùng model CPU."
                    )
            if response.status in {401, 403}:
                raise ProviderError(
                    "Nhà cung cấp AI từ chối truy cập. Kiểm tra API key và quyền model."
                )
            if response.status == 429:
                raise ProviderError("Đã chạm hạn mức của nhà cung cấp AI. Vui lòng thử lại sau.")
            raise ProviderError(f"Nhà cung cấp AI từ chối yêu cầu (HTTP {response.status}).")
        if not response.getheader("Content-Type", "").startswith("text/event-stream"):
            raise ProviderError("Nhà cung cấp AI không trả về luồng SSE.")
        stopped = False
        data = []
        total = 0
        while time.monotonic() - started < settings.llm_timeout_seconds:
            line = response.readline(65537)
            total += len(line)
            if len(line) > 65536 or total > 2_000_000:
                raise ProviderError("Phản hồi AI vượt giới hạn.")
            if not line:
                break
            line = line.decode("utf-8").rstrip("\r\n")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
            elif not line and data:
                payload = "\n".join(data)
                data = []
                if payload == "[DONE]":
                    if not stopped:
                        raise ProviderError("AI kết thúc mà chưa hoàn tất câu trả lời.")
                    return
                chunk = json.loads(payload)
                if "error" in chunk:
                    raise ProviderError("Nhà cung cấp AI báo lỗi trong khi trả lời.")
                for choice in chunk.get("choices", []):
                    if choice.get("index", 0) != 0:
                        continue
                    text = choice.get("delta", {}).get("content")
                    if text:
                        if not isinstance(text, str):
                            raise ProviderError("Nội dung AI không hợp lệ.")
                        yield text
                    reason = choice.get("finish_reason")
                    if reason is not None:
                        if reason != "stop":
                            raise ProviderError("Câu trả lời AI bị cắt hoặc không thể hoàn tất.")
                        stopped = True
        raise ProviderError("Kết nối AI bị gián đoạn hoặc quá thời gian chờ.")
    except ProviderError:
        raise
    except Exception:
        # Never include upstream bodies, URLs or credentials in public errors/logs.
        raise ProviderError("Không kết nối được AI hoặc dữ liệu phản hồi không hợp lệ.") from None
    finally:
        connection.close()
