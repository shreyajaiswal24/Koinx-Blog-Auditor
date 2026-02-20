"""Findings endpoint: paginated, filterable list."""

import math
from typing import Optional

from fastapi import APIRouter, Query

from storage.database import get_db
from api.schemas import FindingOut, PaginatedFindings

router = APIRouter(prefix="/api", tags=["findings"])


@router.get("/findings", response_model=PaginatedFindings)
def get_findings(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    db = get_db()

    # Build filter
    query = {}
    if priority:
        query["priority"] = priority
    if status:
        query["status"] = status
    if issue_type:
        query["issue_type"] = issue_type

    # Count total
    total = db.audit_findings.count_documents(query)

    # Fetch page
    skip = (page - 1) * per_page
    docs = (
        db.audit_findings
        .find(query)
        .sort("id", -1)
        .skip(skip)
        .limit(per_page)
    )

    items = [
        FindingOut(
            id=d["id"],
            run_id=d["run_id"],
            blog_url=d["blog_url"],
            blog_title=d["blog_title"],
            section_heading=d.get("section_heading", ""),
            exact_quote=d["exact_quote"],
            issue_type=d["issue_type"],
            description=d["description"],
            suggested_update=d["suggested_update"],
            source=d["source"],
            llm_confidence=d.get("llm_confidence", 0),
            confidence=d["confidence"],
            priority=d["priority"],
            status=d["status"],
            finding_hash=d["finding_hash"],
        )
        for d in docs
    ]

    return PaginatedFindings(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, math.ceil(total / per_page)),
    )
