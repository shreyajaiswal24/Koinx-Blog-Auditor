"""Dashboard statistics endpoint."""

from fastapi import APIRouter

from storage.database import Database
from api.schemas import StatsResponse, RunOut

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    db = Database()
    try:
        # Finding counts by priority (latest run only for active findings)
        total = db.execute("SELECT COUNT(*) FROM audit_findings").fetchone()[0]
        high = db.execute(
            "SELECT COUNT(*) FROM audit_findings WHERE priority='high'"
        ).fetchone()[0]
        medium = db.execute(
            "SELECT COUNT(*) FROM audit_findings WHERE priority='medium'"
        ).fetchone()[0]
        low = db.execute(
            "SELECT COUNT(*) FROM audit_findings WHERE priority='low'"
        ).fetchone()[0]

        # By status
        new = db.execute(
            "SELECT COUNT(*) FROM audit_findings WHERE status='new'"
        ).fetchone()[0]
        prev = db.execute(
            "SELECT COUNT(*) FROM audit_findings WHERE status='previously_identified'"
        ).fetchone()[0]
        resolved = db.execute(
            "SELECT COUNT(*) FROM audit_findings WHERE status='resolved'"
        ).fetchone()[0]

        # Runs
        total_runs = db.execute("SELECT COUNT(*) FROM audit_runs").fetchone()[0]

        last_run = None
        row = db.execute(
            "SELECT id, started_at, completed_at, total_posts, total_findings, "
            "total_api_calls, total_tokens FROM audit_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            last_run = RunOut(
                id=row[0], started_at=row[1], completed_at=row[2],
                total_posts=row[3], total_findings=row[4],
                total_api_calls=row[5], total_tokens=row[6],
            )

        return StatsResponse(
            total_findings=total, high=high, medium=medium, low=low,
            new=new, previously_identified=prev, resolved=resolved,
            total_runs=total_runs, last_run=last_run,
        )
    finally:
        db.close()
