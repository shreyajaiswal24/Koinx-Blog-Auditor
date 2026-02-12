"""SQLite database setup and connection management."""

import logging
import sqlite3
from pathlib import Path

from config.settings import DB_PATH

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS blog_posts (
    id INTEGER PRIMARY KEY,
    wp_id INTEGER UNIQUE,
    title TEXT,
    url TEXT,
    slug TEXT,
    published_at TEXT,
    modified_at TEXT,
    content_hash TEXT,
    last_audited_at REAL
);

CREATE TABLE IF NOT EXISTS audit_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    blog_url TEXT,
    blog_title TEXT,
    section_heading TEXT,
    exact_quote TEXT,
    issue_type TEXT,
    description TEXT,
    suggested_update TEXT,
    source TEXT,
    llm_confidence REAL,
    confidence REAL,
    priority TEXT,
    finding_hash TEXT,
    status TEXT DEFAULT 'new',
    first_detected_at REAL,
    last_detected_at REAL,
    FOREIGN KEY (run_id) REFERENCES audit_runs(id)
);

CREATE TABLE IF NOT EXISTS audit_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at REAL,
    completed_at REAL,
    total_posts INTEGER,
    total_findings INTEGER,
    total_api_calls INTEGER,
    total_tokens INTEGER
);

CREATE TABLE IF NOT EXISTS tax_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    content TEXT,
    source TEXT,
    url TEXT,
    fetched_at REAL
);

CREATE INDEX IF NOT EXISTS idx_finding_hash ON audit_findings(finding_hash);
CREATE INDEX IF NOT EXISTS idx_finding_run ON audit_findings(run_id);
CREATE INDEX IF NOT EXISTS idx_blog_url ON audit_findings(blog_url);
"""


class Database:
    """SQLite database wrapper with schema management."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def execute(self, sql: str, params=None):
        """Execute a SQL statement."""
        if params:
            return self.conn.execute(sql, params)
        return self.conn.execute(sql)

    def executemany(self, sql: str, params_list):
        """Execute a SQL statement for multiple parameter sets."""
        return self.conn.executemany(sql, params_list)

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
