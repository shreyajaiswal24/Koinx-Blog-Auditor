"""Audit run history endpoint."""

from typing import List

from fastapi import APIRouter

from storage.database import Database
from api.schemas import RunOut

router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs", response_model=List[RunOut])
def get_runs():
    db = Database()
    try:
        rows = db.execute(
            "SELECT id, started_at, completed_at, total_posts, total_findings, "
            "total_api_calls, total_tokens FROM audit_runs ORDER BY id DESC"
        ).fetchall()
        return [
            RunOut(
                id=r[0], started_at=r[1], completed_at=r[2],
                total_posts=r[3], total_findings=r[4],
                total_api_calls=r[5], total_tokens=r[6],
            )
            for r in rows
        ]
    finally:
        db.close()
