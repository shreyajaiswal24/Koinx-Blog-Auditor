"""Audit run history endpoint."""

from typing import List

from fastapi import APIRouter

from storage.database import get_db
from api.schemas import RunOut

router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs", response_model=List[RunOut])
def get_runs():
    db = get_db()
    docs = db.audit_runs.find().sort("id", -1)
    return [
        RunOut(
            id=d["id"],
            started_at=d.get("started_at"),
            completed_at=d.get("completed_at"),
            total_posts=d.get("total_posts", 0),
            total_findings=d.get("total_findings", 0),
            total_api_calls=d.get("total_api_calls", 0),
            total_tokens=d.get("total_tokens", 0),
            started_by=d.get("started_by"),
            category=d.get("category"),
        )
        for d in docs
    ]
