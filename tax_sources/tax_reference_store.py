"""Aggregate and cache tax law references in SQLite."""

import json
import logging
import time
from typing import List, Dict, Optional

from config.settings import TAX_REFERENCE_TTL
from tax_sources.irs_fetcher import IRSFetcher

logger = logging.getLogger(__name__)


class TaxReferenceStore:
    """Manages tax law reference corpus with caching."""

    def __init__(self, db):
        """Initialize with a database connection wrapper.

        Args:
            db: storage.database.Database instance
        """
        self.db = db
        self.fetcher = IRSFetcher()
        self._cache: Optional[List[Dict[str, str]]] = None
        self._cache_time: float = 0

    def get_references(self) -> List[Dict[str, str]]:
        """Get all tax references, using cache if fresh."""
        now = time.time()

        # Check in-memory cache
        if self._cache and (now - self._cache_time) < TAX_REFERENCE_TTL:
            logger.info("Using in-memory tax reference cache")
            return self._cache

        # Check DB cache
        db_refs = self._load_from_db()
        if db_refs:
            self._cache = db_refs
            self._cache_time = now
            logger.info(f"Loaded {len(db_refs)} references from DB cache")
            return db_refs

        # Fetch fresh from IRS
        logger.info("Fetching fresh tax references from IRS.gov...")
        references = self.fetcher.fetch_all_references()
        self._save_to_db(references)
        self._cache = references
        self._cache_time = now
        return references

    def get_reference_corpus(self) -> str:
        """Build a single text corpus from all references for LLM context."""
        refs = self.get_references()
        parts = []
        for ref in refs:
            parts.append(f"### {ref['topic']}")
            parts.append(ref["content"])
            parts.append(f"Source: {ref['source']}")
            parts.append("")
        return "\n".join(parts)

    def _load_from_db(self) -> Optional[List[Dict[str, str]]]:
        """Load cached references from SQLite if they exist and are fresh."""
        rows = self.db.execute(
            "SELECT topic, content, source, url, fetched_at FROM tax_references"
        ).fetchall()
        if not rows:
            return None

        # Check freshness of the newest entry
        newest = max(r[4] for r in rows)
        if (time.time() - newest) > TAX_REFERENCE_TTL:
            logger.info("DB tax references cache expired")
            return None

        return [
            {"topic": r[0], "content": r[1], "source": r[2], "url": r[3]}
            for r in rows
        ]

    def _save_to_db(self, references: List[Dict[str, str]]):
        """Save references to SQLite cache."""
        now = time.time()
        self.db.execute("DELETE FROM tax_references")
        for ref in references:
            self.db.execute(
                "INSERT INTO tax_references (topic, content, source, url, fetched_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (ref["topic"], ref["content"], ref["source"], ref.get("url", ""), now),
            )
        self.db.commit()
        logger.info(f"Cached {len(references)} tax references to DB")
