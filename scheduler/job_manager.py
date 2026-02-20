"""APScheduler-based daily audit scheduling."""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import SCHEDULE_HOUR, SCHEDULE_MINUTE

logger = logging.getLogger(__name__)


def _run_scheduled_audit():
    """Execute a full audit run (called by scheduler)."""
    # Import here to avoid circular imports
    from storage.database import Database
    from analyzer.gap_detector import GapDetector
    from storage.change_tracker import ChangeTracker
    from output.excel_generator import ExcelGenerator
    from tax_sources.tax_reference_store import TaxReferenceStore

    logger.info("=== Scheduled audit starting ===")
    try:
        db = Database()
        detector = GapDetector(db)
        tracker = ChangeTracker(db)
        excel_gen = ExcelGenerator()
        tax_store = TaxReferenceStore(db)

        findings = detector.run_full_audit()

        run_id = tracker.start_run(total_posts=0)
        classified = tracker.classify_findings(run_id, findings)

        api_stats = detector.mistral.get_usage_stats()
        tracker.complete_run(run_id, len(classified), api_stats)

        tax_refs = tax_store.get_references()
        run_stats = {
            "run_id": run_id,
            "total_posts": len(findings),
            "api_stats": api_stats,
        }
        report_path = excel_gen.generate(classified, run_stats, tax_refs)

        logger.info(f"=== Scheduled audit complete. Report: {report_path} ===")
    except Exception as e:
        logger.error(f"Scheduled audit failed: {e}", exc_info=True)


class JobManager:
    """Manages the daily audit cron job."""

    def __init__(self):
        self.scheduler = BlockingScheduler()

    def start(self):
        """Start the scheduler with a daily cron job."""
        trigger = CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE)

        self.scheduler.add_job(
            _run_scheduled_audit,
            trigger=trigger,
            id="daily_tax_audit",
            name="Daily KoinX Tax Content Audit",
            replace_existing=True,
        )

        next_run = self.scheduler.get_jobs()[0].next_run_time
        logger.info(f"Scheduler started. Next audit at: {next_run}")
        logger.info(f"Schedule: daily at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")
        logger.info("Press Ctrl+C to stop.")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
            self.scheduler.shutdown()
