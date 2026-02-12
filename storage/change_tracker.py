"""Change detection: track new, recurring, and resolved findings across runs."""

import hashlib
import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ChangeTracker:
    """Tracks findings across audit runs using content hashing."""

    def __init__(self, db):
        """Initialize with a Database instance."""
        self.db = db

    def start_run(self, total_posts: int) -> int:
        """Create a new audit run record and return its ID."""
        now = time.time()
        cursor = self.db.execute(
            "INSERT INTO audit_runs (started_at, total_posts, total_findings, total_api_calls, total_tokens) "
            "VALUES (?, ?, 0, 0, 0)",
            (now, total_posts),
        )
        self.db.commit()
        run_id = cursor.lastrowid
        logger.info(f"Started audit run #{run_id}")
        return run_id

    def complete_run(self, run_id: int, total_findings: int, api_stats: Dict[str, int]):
        """Mark a run as completed with stats."""
        now = time.time()
        self.db.execute(
            "UPDATE audit_runs SET completed_at=?, total_findings=?, "
            "total_api_calls=?, total_tokens=? WHERE id=?",
            (now, total_findings, api_stats.get("total_requests", 0),
             api_stats.get("total_tokens", 0), run_id),
        )
        self.db.commit()
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
        prev_hashes = set()
        rows = self.db.execute(
            "SELECT DISTINCT finding_hash FROM audit_findings WHERE run_id != ?",
            (run_id,),
        ).fetchall()
        for row in rows:
            prev_hashes.add(row[0])

        current_hashes = set()

        for finding in findings:
            finding_hash = self._compute_hash(finding["blog_url"], finding["exact_quote"])
            finding["finding_hash"] = finding_hash
            current_hashes.add(finding_hash)

            if finding_hash in prev_hashes:
                finding["status"] = "previously_identified"
                # Update last_detected_at for existing findings
                self.db.execute(
                    "UPDATE audit_findings SET last_detected_at=? WHERE finding_hash=? AND run_id != ?",
                    (now, finding_hash, run_id),
                )
            else:
                finding["status"] = "new"

            # Insert finding for this run
            self.db.execute(
                "INSERT INTO audit_findings "
                "(run_id, blog_url, blog_title, section_heading, exact_quote, "
                "issue_type, description, suggested_update, source, "
                "llm_confidence, confidence, priority, finding_hash, status, "
                "first_detected_at, last_detected_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    finding["blog_url"],
                    finding["blog_title"],
                    finding.get("section_heading", ""),
                    finding["exact_quote"],
                    finding["issue_type"],
                    finding["description"],
                    finding["suggested_update"],
                    finding["source"],
                    finding.get("llm_confidence", 0),
                    finding["confidence"],
                    finding["priority"],
                    finding_hash,
                    finding["status"],
                    now,
                    now,
                ),
            )

        # Mark resolved findings (were in previous runs but not this one)
        resolved_hashes = prev_hashes - current_hashes
        if resolved_hashes:
            placeholders = ",".join("?" for _ in resolved_hashes)
            self.db.execute(
                f"UPDATE audit_findings SET status='resolved' "
                f"WHERE finding_hash IN ({placeholders}) AND status != 'resolved'",
                list(resolved_hashes),
            )
            logger.info(f"Marked {len(resolved_hashes)} findings as resolved")

        self.db.commit()

        # Add resolved findings to the output for reporting
        resolved_findings = self._get_resolved_findings(resolved_hashes)

        return findings + resolved_findings

    def _get_resolved_findings(self, resolved_hashes: set) -> List[Dict[str, Any]]:
        """Fetch resolved findings from DB for reporting."""
        if not resolved_hashes:
            return []

        placeholders = ",".join("?" for _ in resolved_hashes)
        rows = self.db.execute(
            f"SELECT blog_url, blog_title, section_heading, exact_quote, "
            f"issue_type, description, suggested_update, source, "
            f"llm_confidence, confidence, priority, finding_hash "
            f"FROM audit_findings WHERE finding_hash IN ({placeholders}) "
            f"GROUP BY finding_hash",
            list(resolved_hashes),
        ).fetchall()

        resolved = []
        for r in rows:
            resolved.append({
                "blog_url": r[0],
                "blog_title": r[1],
                "section_heading": r[2],
                "exact_quote": r[3],
                "issue_type": r[4],
                "description": r[5],
                "suggested_update": r[6],
                "source": r[7],
                "llm_confidence": r[8],
                "confidence": r[9],
                "priority": r[10],
                "finding_hash": r[11],
                "status": "resolved",
            })

        return resolved

    @staticmethod
    def _compute_hash(blog_url: str, exact_quote: str) -> str:
        """Compute SHA-256 hash of blog_url + exact_quote for deduplication."""
        content = f"{blog_url}|{exact_quote}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()
