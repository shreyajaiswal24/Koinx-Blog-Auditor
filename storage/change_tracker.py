"""Change detection: track new, recurring, and resolved findings across runs."""

import hashlib
import logging
import time
from typing import List, Dict, Any

from storage.database import get_next_id

logger = logging.getLogger(__name__)


class ChangeTracker:
    """Tracks findings across audit runs using content hashing."""

    def __init__(self, db):
        """Initialize with a Database instance."""
        self.db = db

    def start_run(self, total_posts: int, started_by: str = None, category: str = None) -> int:
        """Create a new audit run record and return its ID."""
        now = time.time()
        run_id = get_next_id("audit_runs")
        self.db.audit_runs.insert_one({
            "id": run_id,
            "started_at": now,
            "completed_at": None,
            "total_posts": total_posts,
            "total_findings": 0,
            "total_api_calls": 0,
            "total_tokens": 0,
            "started_by": started_by,
            "category": category,
            "status": "started",
        })
        logger.info(f"Started audit run #{run_id}")
        return run_id

    def complete_run(self, run_id: int, total_findings: int, api_stats: Dict[str, int]):
        """Mark a run as completed with stats."""
        now = time.time()
        self.db.audit_runs.update_one(
            {"id": run_id},
            {"$set": {
                "completed_at": now,
                "total_findings": total_findings,
                "total_api_calls": api_stats.get("total_requests", 0),
                "total_tokens": api_stats.get("total_tokens", 0),
                "status": "completed",
            }},
        )
        logger.info(f"Completed audit run #{run_id}: {total_findings} findings")

    def classify_findings(
        self, run_id: int, findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Classify each finding as new, previously_identified, or resolved.

        Also persists findings to the database.

        Returns:
            findings list with added 'status' and 'finding_hash' keys.
        """
        now = time.time()

        # Get all existing finding hashes from previous runs
        prev_docs = self.db.audit_findings.distinct(
            "finding_hash", {"run_id": {"$ne": run_id}}
        )
        prev_hashes = set(prev_docs)

        current_hashes = set()

        for finding in findings:
            finding_hash = self._compute_hash(finding["blog_url"], finding["exact_quote"])
            finding["finding_hash"] = finding_hash
            current_hashes.add(finding_hash)

            if finding_hash in prev_hashes:
                finding["status"] = "previously_identified"
                # Update last_detected_at for existing findings
                self.db.audit_findings.update_many(
                    {"finding_hash": finding_hash, "run_id": {"$ne": run_id}},
                    {"$set": {"last_detected_at": now}},
                )
            else:
                finding["status"] = "new"

            # Insert finding for this run
            finding_id = get_next_id("audit_findings")
            self.db.audit_findings.insert_one({
                "id": finding_id,
                "run_id": run_id,
                "blog_url": finding["blog_url"],
                "blog_title": finding["blog_title"],
                "section_heading": finding.get("section_heading", ""),
                "exact_quote": finding["exact_quote"],
                "issue_type": finding["issue_type"],
                "description": finding["description"],
                "suggested_update": finding["suggested_update"],
                "source": finding["source"],
                "llm_confidence": finding.get("llm_confidence", 0),
                "confidence": finding["confidence"],
                "priority": finding["priority"],
                "finding_hash": finding_hash,
                "status": finding["status"],
                "first_detected_at": now,
                "last_detected_at": now,
            })

        # Mark resolved findings (were in previous runs but not this one)
        resolved_hashes = prev_hashes - current_hashes
        if resolved_hashes:
            self.db.audit_findings.update_many(
                {
                    "finding_hash": {"$in": list(resolved_hashes)},
                    "status": {"$ne": "resolved"},
                },
                {"$set": {"status": "resolved"}},
            )
            logger.info(f"Marked {len(resolved_hashes)} findings as resolved")

        # Add resolved findings to the output for reporting
        resolved_findings = self._get_resolved_findings(resolved_hashes)

        return findings + resolved_findings

    def _get_resolved_findings(self, resolved_hashes: set) -> List[Dict[str, Any]]:
        """Fetch resolved findings from DB for reporting."""
        if not resolved_hashes:
            return []

        # Get one finding per hash using aggregation
        pipeline = [
            {"$match": {"finding_hash": {"$in": list(resolved_hashes)}}},
            {"$group": {
                "_id": "$finding_hash",
                "doc": {"$first": "$$ROOT"},
            }},
        ]
        results = self.db.audit_findings.aggregate(pipeline)

        resolved = []
        for r in results:
            doc = r["doc"]
            resolved.append({
                "blog_url": doc["blog_url"],
                "blog_title": doc["blog_title"],
                "section_heading": doc.get("section_heading", ""),
                "exact_quote": doc["exact_quote"],
                "issue_type": doc["issue_type"],
                "description": doc["description"],
                "suggested_update": doc["suggested_update"],
                "source": doc["source"],
                "llm_confidence": doc.get("llm_confidence", 0),
                "confidence": doc["confidence"],
                "priority": doc["priority"],
                "finding_hash": doc["finding_hash"],
                "status": "resolved",
            })

        return resolved

    @staticmethod
    def _compute_hash(blog_url: str, exact_quote: str) -> str:
        """Compute SHA-256 hash of blog_url + exact_quote for deduplication."""
        content = f"{blog_url}|{exact_quote}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()
