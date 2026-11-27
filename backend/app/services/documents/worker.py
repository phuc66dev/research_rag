import asyncio
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, update

from app.models.document import Document, DocumentChunk, DocumentJob
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.documents import delete_document_index
from app.services.documents.service import finish_deletion

logger = logging.getLogger(__name__)


def _run_pipeline_sync(executable: str, options_json: str, timeout: int, cwd: str):
    import subprocess

    try:
        proc = subprocess.run(
            [executable, "-m", "app.services.documents.pipeline", options_json],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=cwd,
        )
        if proc.returncode:
            logger.warning(
                "Pipeline subprocess exited %d; stderr: %s; stdout: %s",
                proc.returncode,
                proc.stderr[:500],
                proc.stdout[:500],
            )
            return {"error": "processing_failed"}
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "processing_timeout"}
    except Exception:
        logger.exception("Pipeline execution failed unexpectedly")
        return {"error": "processing_failed"}


async def run_pipeline(app, item):
    settings = app.state.settings
    from pathlib import Path as _Path

    options = {
        "path": str(app.state.document_storage.path(item.id)),
        "version": item.document_version,
        "max_pages": settings.document_max_pages,
        "max_chunks": settings.document_max_chunks,
        "model": settings.embedding_model,
        "cache_dir": str(_Path(settings.embedding_cache_dir).resolve()),
    }
    backend_dir = str(_Path(__file__).resolve().parents[3])
    return await asyncio.to_thread(
        _run_pipeline_sync,
        sys.executable,
        json.dumps(options),
        settings.document_job_timeout,
        backend_dir,
    )


def claim_job(app):
    with app.state.session_factory() as db:
        cutoff = datetime.now(UTC) - timedelta(seconds=app.state.settings.document_job_timeout + 30)
        for job in db.scalars(
            select(DocumentJob).where(
                DocumentJob.state == "processing", DocumentJob.started_at < cutoff
            )
        ):
            job.state = "failed"
            job.lease_token = None
            item = db.get(Document, job.document_id)
            if item and item.status == "processing":
                item.status = "failed"
                item.error_code = "processing_interrupted"
                item.updated_at = datetime.now(UTC)
        db.commit()
        job = db.scalar(
            select(DocumentJob)
            .where(DocumentJob.state == "queued")
            .order_by(DocumentJob.document_id)
            .limit(1)
        )
        if not job:
            return None
        document_id, generation = job.document_id, job.generation
        token = str(uuid4())
        claimed = db.execute(
            update(DocumentJob)
            .where(
                DocumentJob.document_id == document_id,
                DocumentJob.generation == generation,
                DocumentJob.state == "queued",
            )
            .values(
                state="processing",
                lease_token=token,
                started_at=datetime.now(UTC),
                attempts=DocumentJob.attempts + 1,
            )
        )
        if not claimed.rowcount:
            db.rollback()
            return None
        item = db.get(Document, document_id)
        if not item or item.status != "queued":
            db.rollback()
            return None
        workspace = db.get(Workspace, item.workspace_id)
        owner = db.get(User, item.owner_id)
        if (
            workspace is None
            or workspace.owner_id != item.owner_id
            or workspace.is_deleting
            or owner is None
            or not owner.is_active
        ):
            job = db.get(DocumentJob, document_id)
            job.state = "failed"
            job.lease_token = None
            item.status = "failed"
            item.error_code = "source_access_revoked"
            db.commit()
            return None
        item.status = "processing"
        item.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(item)
        db.expunge(item)
        return item, generation, token


def complete_job(app, item, generation, token, result):
    with app.state.session_factory() as db:
        # This write takes the DB lock before publishing chunks; delete/retry revokes the lease.
        claimed = db.execute(
            update(DocumentJob)
            .where(
                DocumentJob.document_id == item.id,
                DocumentJob.generation == generation,
                DocumentJob.lease_token == token,
                DocumentJob.state == "processing",
            )
            .values(state="failed" if "error" in result else "completed", lease_token=None)
        )
        if not claimed.rowcount:
            db.rollback()
            return False
        current = db.get(Document, item.id)
        if not current or current.status != "processing":
            db.rollback()
            return False
        delete_document_index(db, item.id)
        current.updated_at = datetime.now(UTC)
        if "error" in result:
            current.status = "failed"
            current.error_code = result["error"]
            current.chunk_count = 0
        else:
            for chunk in result["chunks"]:
                # Same bytes in different workspaces have independent index identities.
                chunk_id = hashlib.sha256(f"{item.id}:{chunk['id']}".encode()).hexdigest()
                db.add(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=item.id,
                        document_version=item.document_version,
                        page_number=chunk["page_number"],
                        text=chunk["text"],
                        embedding=chunk["embedding"],
                    )
                )
            current.status = "ready"
            current.error_code = None
            current.page_count = result["page_count"]
            current.chunk_count = len(result["chunks"])
            current.embedding_model = result["model"]
        db.commit()
        return True


async def process_next(app, processor=run_pipeline):
    claim = claim_job(app)
    if claim is None:
        return False
    item, generation, token = claim
    try:
        result = await processor(app, item)
    except Exception:
        logger.exception("Document processing failed")
        result = {"error": "processing_failed"}
    complete_job(app, item, generation, token, result)
    return True


async def worker_loop(app):
    while True:
        try:
            with app.state.session_factory() as db:
                for item in db.scalars(select(Document).where(Document.status == "deleting")):
                    finish_deletion(db, item, app.state.document_storage)
            await process_next(app)
        except asyncio.CancelledError:
            raise
        except Exception:
            # No source text, paths, or credentials in operational logs.
            logger.warning("Document worker cycle failed; retrying on next cycle")
        await asyncio.sleep(1)
