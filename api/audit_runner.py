"""Background audit runner that bridges sync GapDetector to async FastAPI."""

import asyncio
import logging
import time
from typing import Optional

from api.state import audit_state

logger = logging.getLogger(__name__)


def _run_audit_sync(
    run_id: int,
    post_id: Optional[int] = None,
    started_by: Optional[str] = None,
    category: Optional[str] = None,
):
    """Run the full audit pipeline synchronously (called in executor thread).

    The run document is already created with status 'started'.
    This function updates it to 'completed' or 'failed'.
    """
    from storage.database import Database, get_db
    from analyzer.gap_detector import GapDetector
    from storage.change_tracker import ChangeTracker
    from output.excel_generator import ExcelGenerator
    from tax_sources.tax_reference_store import TaxReferenceStore
    from config.settings import OUTPUT_DIR

    start_time = time.time()

    db = Database()
    detector = GapDetector(db)
    tracker = ChangeTracker(db)
    excel_gen = ExcelGenerator()
    tax_store = TaxReferenceStore(db)

    def progress_callback(event):
        audit_state.broadcast(event)

    try:
        findings = detector.run_full_audit(
            single_post_id=post_id,
            progress_callback=progress_callback,
        )

        if not findings:
            logger.info("No findings detected.")
            # Mark as completed with 0 findings
            mongo_db = get_db()
            mongo_db.audit_runs.update_one(
                {"id": run_id},
                {"$set": {"status": "completed", "completed_at": time.time()}},
            )
            return

        # Use the pre-created run_id — update its post count
        total_posts = len(set(f["blog_url"] for f in findings))
        mongo_db = get_db()
        mongo_db.audit_runs.update_one(
            {"id": run_id},
            {"$set": {"total_posts": total_posts}},
        )

        classified = tracker.classify_findings(run_id, findings)

        api_stats = detector.mistral.get_usage_stats()

        # Mark run as completed
        now = time.time()
        mongo_db.audit_runs.update_one(
            {"id": run_id},
            {"$set": {
                "completed_at": now,
                "total_findings": len(classified),
                "total_api_calls": api_stats.get("total_requests", 0),
                "total_tokens": api_stats.get("total_tokens", 0),
                "status": "completed",
            }},
        )

        tax_refs = tax_store.get_references()
        run_stats = {
            "run_id": run_id,
            "total_posts": total_posts,
            "api_stats": api_stats,
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        excel_gen.generate(classified, run_stats, tax_refs)

        elapsed = time.time() - start_time
        logger.info(f"Audit complete in {elapsed:.1f}s — {len(classified)} findings")
    except Exception as e:
        logger.error(f"Audit run #{run_id} failed: {e}")
        # Mark as failed
        mongo_db = get_db()
        mongo_db.audit_runs.update_one(
            {"id": run_id},
            {"$set": {"status": "failed", "completed_at": time.time()}},
        )
        raise
    finally:
        db.close()


async def start_audit(
    run_id: int,
    post_id: Optional[int] = None,
    started_by: Optional[str] = None,
    category: Optional[str] = None,
):
    """Launch the audit in a background thread, updating audit_state."""
    audit_state.set_running(True)
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None, _run_audit_sync, run_id, post_id, started_by, category
        )
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        audit_state.broadcast({"event": "audit_error", "error": str(e)})
    finally:
        audit_state.set_running(False)
        audit_state.broadcast({"event": "audit_finished"})
