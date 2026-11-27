"""Only server-generated UUIDs become filesystem names."""

from pathlib import Path
from uuid import UUID


class DocumentStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def path(self, document_id: str) -> Path:
        return self.root / f"{UUID(document_id)}.pdf"

    def temporary_path(self, upload_id: str) -> Path:
        return self.root / f"{UUID(upload_id)}.upload"
