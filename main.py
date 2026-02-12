"""KoinX Blog Tax Content Auditor — CLI entry point."""

import argparse
import logging
import sys
import time

from config.settings import OUTPUT_DIR


def setup_logging():
    """Configure logging to console and file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("auditor.log"),
        ],
    )


def run_audit(post_id=None):
    """Execute a single audit run."""
    from storage.database import Database
    from analyzer.gap_detector import GapDetector
    from storage.change_tracker import ChangeTracker
    from output.excel_generator import ExcelGenerator
    from tax_sources.tax_reference_store import TaxReferenceStore

    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("KoinX Blog Tax Content Auditor")
    logger.info("=" * 60)

    start_time = time.time()

    # Initialize
    db = Database()
    detector = GapDetector(db)
    tracker = ChangeTracker(db)
    excel_gen = ExcelGenerator()
    tax_store = TaxReferenceStore(db)

    # Run audit
    logger.info("Starting audit pipeline...")
    findings = detector.run_full_audit(single_post_id=post_id)

    if not findings:
        logger.info("No findings detected. Audit complete.")
        db.close()
        return

    # Track changes
    run_id = tracker.start_run(total_posts=len(findings))
    classified_findings = tracker.classify_findings(run_id, findings)

    api_stats = detector.mistral.get_usage_stats()
    tracker.complete_run(run_id, len(classified_findings), api_stats)

    # Generate report
    tax_refs = tax_store.get_references()
    run_stats = {
        "run_id": run_id,
        "total_posts": len(set(f["blog_url"] for f in findings)),
        "api_stats": api_stats,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = excel_gen.generate(classified_findings, run_stats, tax_refs)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Audit complete in {elapsed:.1f}s")
    logger.info(f"Total findings: {len(classified_findings)}")
    logger.info(f"  New: {sum(1 for f in classified_findings if f.get('status') == 'new')}")
    logger.info(f"  Previously identified: {sum(1 for f in classified_findings if f.get('status') == 'previously_identified')}")
    logger.info(f"  Resolved: {sum(1 for f in classified_findings if f.get('status') == 'resolved')}")
    logger.info(f"Report saved: {report_path}")
    logger.info(f"API usage: {api_stats}")
    logger.info("=" * 60)

    db.close()


def run_scheduler():
    """Start the daily audit scheduler."""
    from scheduler.job_manager import JobManager

    logger = logging.getLogger(__name__)
    logger.info("Starting audit scheduler...")

    manager = JobManager()
    manager.start()


def main():
    parser = argparse.ArgumentParser(
        description="KoinX Blog Tax Content Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py run                  Run a full audit
  python main.py run --post-id 12345  Audit a single post
  python main.py schedule             Start daily scheduler (2 AM)
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run audit once")
    run_parser.add_argument(
        "--post-id", type=int, default=None,
        help="Audit a single post by WordPress ID",
    )

    # 'schedule' subcommand
    subparsers.add_parser("schedule", help="Start daily audit scheduler")

    args = parser.parse_args()

    setup_logging()

    if args.command == "run":
        run_audit(post_id=args.post_id)
    elif args.command == "schedule":
        run_scheduler()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
