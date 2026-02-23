"""Audit control endpoints: start and status."""

import asyncio

from fastapi import APIRouter, HTTPException, Depends

from api.schemas import AuditStartRequest, AuditStartResponse, AuditStatusResponse
from api.state import audit_state
from api.audit_runner import start_audit
from api.auth import get_current_user
from storage.database import get_db, get_next_id
import time

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.post("/start", response_model=AuditStartResponse)
async def start_audit_endpoint(
    body: AuditStartRequest,
    user: dict = Depends(get_current_user),
):
    db = get_db()

    # Check if there's already a started audit for this category
    existing = db.audit_runs.find_one({
        "category": body.category,
        "status": "started",
    })
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"An audit is already in progress for '{body.category}'.",
        )

    # Create the run document immediately with status "started"
    run_id = get_next_id("audit_runs")
    now = time.time()
    db.audit_runs.insert_one({
        "id": run_id,
        "started_at": now,
        "completed_at": None,
        "total_posts": 0,
        "total_findings": 0,
        "total_api_calls": 0,
        "total_tokens": 0,
        "started_by": user["name"],
        "category": body.category,
        "status": "started",
    })

    # Launch the audit in the background
    asyncio.ensure_future(
        start_audit(
            run_id=run_id,
            post_id=body.post_id,
            started_by=user["name"],
            category=body.category,
        )
    )
    return AuditStartResponse(
        message="Audit started",
        status="started",
        run_id=run_id,
    )


@router.get("/status", response_model=AuditStatusResponse)
async def audit_status():
    return AuditStatusResponse(
        running=audit_state.is_running,
        progress=audit_state.progress if audit_state.progress else None,
    )
