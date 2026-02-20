"""Dashboard statistics endpoint."""

from fastapi import APIRouter

from storage.database import get_db
from api.schemas import StatsResponse, RunOut

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    db = get_db()

    # Finding counts by priority
    total = db.audit_findings.count_documents({})
    high = db.audit_findings.count_documents({"priority": "high"})
    medium = db.audit_findings.count_documents({"priority": "medium"})
    low = db.audit_findings.count_documents({"priority": "low"})

    # By status
    new = db.audit_findings.count_documents({"status": "new"})
    prev = db.audit_findings.count_documents({"status": "previously_identified"})
    resolved = db.audit_findings.count_documents({"status": "resolved"})

    # Runs
    total_runs = db.audit_runs.count_documents({})

    last_run = None
    row = db.audit_runs.find_one(sort=[("id", -1)])
    if row:
        last_run = RunOut(
            id=row["id"],
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            total_posts=row.get("total_posts", 0),
            total_findings=row.get("total_findings", 0),
            total_api_calls=row.get("total_api_calls", 0),
            total_tokens=row.get("total_tokens", 0),
            started_by=row.get("started_by"),
            category=row.get("category"),
        )

    return StatsResponse(
        total_findings=total, high=high, medium=medium, low=low,
        new=new, previously_identified=prev, resolved=resolved,
        total_runs=total_runs, last_run=last_run,
    )
