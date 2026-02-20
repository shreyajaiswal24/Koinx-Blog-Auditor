"""Aggregate and cache tax law references in MongoDB."""

import logging
import time
from typing import List, Dict, Optional

from config.settings import TAX_REFERENCE_TTL
from tax_sources.irs_fetcher import IRSFetcher

logger = logging.getLogger(__name__)


class TaxReferenceStore:
    """Manages tax law reference corpus with caching."""

    def __init__(self, db):
        """Initialize with a Database instance.

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
        """Load cached references from MongoDB if they exist and are fresh."""
        docs = list(self.db.tax_references.find())
        if not docs:
            return None

        # Check freshness of the newest entry
        newest = max(d.get("fetched_at", 0) for d in docs)
        if (time.time() - newest) > TAX_REFERENCE_TTL:
            logger.info("DB tax references cache expired")
            return None

        return [
            {"topic": d["topic"], "content": d["content"], "source": d["source"], "url": d.get("url", "")}
            for d in docs
        ]

    def _save_to_db(self, references: List[Dict[str, str]]):
        """Save references to MongoDB cache."""
        now = time.time()
        self.db.tax_references.delete_many({})
        if references:
            self.db.tax_references.insert_many([
                {
                    "topic": ref["topic"],
                    "content": ref["content"],
                    "source": ref["source"],
                    "url": ref.get("url", ""),
                    "fetched_at": now,
                }
                for ref in references
            ])
        logger.info(f"Cached {len(references)} tax references to DB")
