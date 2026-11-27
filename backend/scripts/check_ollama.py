"""Check the configured local Ollama model using synthetic text, never user documents."""

import http.client
import json
from pathlib import Path
from urllib.parse import urlsplit

from app.core.config import Settings
from app.services.rag.provider import ProviderError, stream_completion


def main() -> int:
    settings = Settings(_env_file=Path(__file__).resolve().parents[1] / ".env")
    url = urlsplit(settings.llm_base_url)
    if (
        url.scheme != "http"
        or url.hostname not in {"localhost", "127.0.0.1", "::1"}
        or url.port != 11434
        or url.path.rstrip("/") != "/v1"
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        print("Chỉ kiểm tra Ollama local: LLM_BASE_URL=http://127.0.0.1:11434/v1")
        return 1
    connection = http.client.HTTPConnection(url.hostname, url.port, timeout=5)
    try:
        connection.request("GET", "/api/tags")
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError("Ollama không trả về danh sách model.")
        payload = json.loads(response.read(1_000_000))
    except (OSError, ValueError, http.client.HTTPException):
        print("Chưa kết nối được Ollama ở cổng 11434. Cài/mở Ollama rồi chạy lại.")
        return 1
    finally:
        connection.close()
    if settings.llm_model not in {model.get("name") for model in payload.get("models", [])}:
        print("Chưa tải model cấu hình. Với cấu hình mẫu, chạy: ollama pull qwen2.5:3b")
        return 1
    print("Đã tìm thấy model local. Đang kiểm tra luồng trả lời bằng dữ liệu minh họa…")
    try:
        answer = "".join(
            stream_completion(
                settings,
                [
                    {
                        "role": "system",
                        "content": "Trả lời ngắn bằng tiếng Việt, chỉ dựa trên nguồn.",
                    },
                    {
                        "role": "user",
                        "content": (
                            "Nguồn [1]: Lá cây dùng ánh sáng để quang hợp. "
                            "Câu hỏi: Lá cây dùng gì để quang hợp? Trả lời một câu kèm [1]."
                        ),
                    },
                ],
            )
        )
    except ProviderError as exc:
        print(f"Kiểm tra stream thất bại: {exc}")
        return 1
    if not answer.strip():
        print("Model trả về nội dung rỗng.")
        return 1
    print("Đã nhận stream hoàn tất từ model local:")
    print(answer)
    print("Đây là kiểm tra kết nối, chưa phải đánh giá chất lượng RAG trên tài liệu thực.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
