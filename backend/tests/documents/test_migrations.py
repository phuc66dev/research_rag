from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app.core.config import Settings
from app.main import create_app


def test_additive_migration_preserves_legacy_workspace_and_quarantines_owner(tmp_path):
    url = f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE workspaces (id VARCHAR(36) PRIMARY KEY, "
                "name VARCHAR(100), description VARCHAR(500), "
                "created_at DATETIME, updated_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO workspaces VALUES ('legacy', 'Old course', '', "
                "'2026-01-01', '2026-01-01')"
            )
        )
    settings = Settings(_env_file=None, database_url=url, document_worker_enabled=False)
    for _ in range(2):
        with TestClient(create_app(settings=settings)):
            pass
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT name, owner_id FROM workspaces WHERE id='legacy'")
        ).one()
        assert row == ("Old course", None)
        assert connection.scalar(text("SELECT COUNT(*) FROM schema_revisions")) == 3
        assert {"documents", "document_chunks", "document_jobs"}.issubset(
            inspect(connection).get_table_names()
        )
    engine.dispose()
