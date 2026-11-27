"""Runs outside the API process with a worker-enforced wall-clock deadline."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from app.services.documents.extract import ProcessingError, extract_chunks
from app.services.retrieval.embedding import LocalEmbedding


def main():
    options = json.loads(sys.argv[1])
    try:
        result = extract_chunks(
            Path(options["path"]), options["version"], options["max_pages"], options["max_chunks"]
        )
        try:
            embedder = LocalEmbedding(
                SimpleNamespace(
                    embedding_model=options["model"], embedding_cache_dir=options["cache_dir"]
                )
            )
            vectors = embedder.embed([chunk["text"] for chunk in result["chunks"]])
        except Exception:
            raise ProcessingError("embedding_unavailable") from None
        for chunk, vector in zip(result["chunks"], vectors, strict=True):
            chunk["embedding"] = vector
        result["model"] = options["model"]
    except ProcessingError as exc:
        result = {"error": str(exc)}
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
