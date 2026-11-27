"""Ordered additive bootstrap migrations. Never infer ownership of legacy data."""

from sqlalchemy import Column, MetaData, String, Table, inspect, select, text

from app.core.database import Base


def migrate(engine):
    revisions = Table("schema_revisions", MetaData(), Column("id", String(80), primary_key=True))
    with engine.begin() as connection:
        revisions.create(connection, checkfirst=True)
        applied = set(connection.scalars(select(revisions.c.id)))
        if "0001_bootstrap" not in applied:
            baseline = [
                table
                for name, table in Base.metadata.tables.items()
                if name not in {"documents", "document_chunks", "document_jobs"}
            ]
            Base.metadata.create_all(connection, tables=baseline)
            connection.execute(revisions.insert().values(id="0001_bootstrap"))
        if "0002_workspace_owner" not in applied:
            columns = {column["name"] for column in inspect(connection).get_columns("workspaces")}
            if "owner_id" not in columns:
                connection.execute(text("ALTER TABLE workspaces ADD COLUMN owner_id VARCHAR(36)"))
            if "is_deleting" not in columns:
                connection.execute(
                    text("ALTER TABLE workspaces ADD COLUMN is_deleting BOOLEAN NOT NULL DEFAULT 0")
                )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS ix_workspaces_owner_id ON workspaces (owner_id)")
            )
            connection.execute(revisions.insert().values(id="0002_workspace_owner"))
        if "0003_documents" not in applied:
            tables = [
                Base.metadata.tables[name]
                for name in ("documents", "document_jobs", "document_chunks")
            ]
            Base.metadata.create_all(connection, tables=tables)
            connection.execute(revisions.insert().values(id="0003_documents"))
