"""Run from backend: python scripts/export_openapi.py. Does not connect to the DB."""

import json
from pathlib import Path

from app.main import create_app

destination = Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(
    json.dumps(create_app().openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(destination)
