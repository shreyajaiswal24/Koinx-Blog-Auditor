"""Findings endpoint: paginated, filterable list."""

import math
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from storage.database import get_db
from api.schemas import FindingOut, PaginatedFindings


class UpdateFindingRequest(BaseModel):
    status: str

router = APIRouter(prefix="/api", tags=["findings"])


@router.get("/findings", response_model=PaginatedFindings)
def get_findings(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    run_id: Optional[int] = Query(None),
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
    if run_id is not None:
        query["run_id"] = run_id

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


@router.patch("/findings/{finding_id}")
def update_finding_status(finding_id: int, body: UpdateFindingRequest):
    allowed = {"completed", "ignored", "new", "previously_identified", "resolved"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(sorted(allowed))}")

    db = get_db()
    result = db.audit_findings.update_one(
        {"id": finding_id},
        {"$set": {"status": body.status}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Finding not found")

    return {"message": "Status updated", "id": finding_id, "status": body.status}
