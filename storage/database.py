"""MongoDB database connection and collection management."""

import logging

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection

from config.settings import MONGODB_URL, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

# Module-level client (reused across the app)
_client: MongoClient = None
_db = None


def get_db():
    """Get the MongoDB database instance (creates client on first call)."""
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGODB_URL)
        _db = _client[MONGODB_DB_NAME]
        _ensure_indexes(_db)
        logger.info(f"MongoDB connected: {MONGODB_URL} / {MONGODB_DB_NAME}")
    return _db


def _ensure_indexes(db):
    """Create indexes for performance."""
    db.audit_findings.create_index("finding_hash")
    db.audit_findings.create_index("run_id")
    db.audit_findings.create_index("blog_url")
    db.audit_findings.create_index("priority")
    db.audit_findings.create_index("status")
    db.blog_posts.create_index("wp_id", unique=True, sparse=True)
    db.users.create_index("email", unique=True)


def get_next_id(collection_name: str) -> int:
    """Get the next auto-increment integer ID for a collection."""
    db = get_db()
    result = db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return result["seq"]


class Database:
    """Compatibility wrapper — gives access to MongoDB collections.

    Consumers that previously called Database() and used db.execute()
    should be updated to use get_db() directly. This class exists to
    keep the constructor-based pattern working during migration.
    """

    def __init__(self):
        self.db = get_db()

    # Collection accessors
    @property
    def blog_posts(self) -> Collection:
        return self.db.blog_posts

    @property
    def audit_findings(self) -> Collection:
        return self.db.audit_findings

    @property
    def audit_runs(self) -> Collection:
        return self.db.audit_runs

    @property
    def tax_references(self) -> Collection:
        return self.db.tax_references

    @property
    def users(self) -> Collection:
        return self.db.users

    def close(self):
        """No-op — MongoDB client is reused at module level."""
        pass
