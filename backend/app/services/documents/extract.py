"""Bounded PDF text extraction. Also used as an isolated worker subprocess."""

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader


class ProcessingError(Exception):
    pass


def extract_chunks(path: Path, version: str, max_pages: int, max_chunks: int):
    try:
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted:
            raise ProcessingError("encrypted_pdf")
        if not reader.pages or len(reader.pages) > max_pages:
            raise ProcessingError("page_limit")
        chunks = []
        empty_pages = 0
        for page_number, page in enumerate(reader.pages, 1):
            # Refuse huge decoded streams before attempting text layout/extraction.
            content = page.get_contents()
            if content is not None and len(content.get_data()) > 8 * 1024 * 1024:
                raise ProcessingError("page_content_limit")
            text = " ".join(unicodedata.normalize("NFC", page.extract_text() or "").split())
            if not text:
                empty_pages += 1
                continue
            # 900 characters + 120 overlap, never merge across original PDF pages.
            for offset in range(0, len(text), 780):
                segment = text[offset : offset + 900]
                key = f"{version}:{page_number}:{offset}:{segment}"
                chunks.append(
                    {
                        "id": hashlib.sha256(key.encode()).hexdigest(),
                        "page_number": page_number,
                        "text": segment,
                    }
                )
                if len(chunks) > max_chunks:
                    raise ProcessingError("chunk_limit")
                if offset + 900 >= len(text):
                    break
        # A partial index must not silently omit scanned pages.
        if empty_pages:
            raise ProcessingError("ocr_required")
        if not chunks:
            raise ProcessingError("no_text")
        return {"page_count": len(reader.pages), "chunks": chunks}
    except ProcessingError:
        raise
    except Exception as exc:
        raise ProcessingError("invalid_pdf") from exc


if __name__ == "__main__":
    try:
        result = extract_chunks(Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
        print(json.dumps(result, ensure_ascii=True))
    except ProcessingError as exc:
        print(json.dumps({"error": str(exc)}))
