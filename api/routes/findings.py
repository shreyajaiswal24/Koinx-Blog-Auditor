"""Findings endpoint: paginated, filterable list."""

import math
from typing import Optional

from fastapi import APIRouter, Query

from storage.database import Database
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
    db = Database()
    try:
        where_clauses = []
        params = []

        if priority:
            where_clauses.append("priority = ?")
            params.append(priority)
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if issue_type:
            where_clauses.append("issue_type = ?")
            params.append(issue_type)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Count total
        count_row = db.execute(
            f"SELECT COUNT(*) FROM audit_findings {where_sql}", params
        ).fetchone()
        total = count_row[0]

        # Fetch page
        offset = (page - 1) * per_page
        rows = db.execute(
            f"SELECT id, run_id, blog_url, blog_title, section_heading, exact_quote, "
            f"issue_type, description, suggested_update, source, llm_confidence, "
            f"confidence, priority, status, finding_hash "
            f"FROM audit_findings {where_sql} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()

        items = [
            FindingOut(
                id=r[0], run_id=r[1], blog_url=r[2], blog_title=r[3],
                section_heading=r[4], exact_quote=r[5], issue_type=r[6],
                description=r[7], suggested_update=r[8], source=r[9],
                llm_confidence=r[10], confidence=r[11], priority=r[12],
                status=r[13], finding_hash=r[14],
            )
            for r in rows
        ]

        return PaginatedFindings(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=max(1, math.ceil(total / per_page)),
        )
    finally:
        db.close()
