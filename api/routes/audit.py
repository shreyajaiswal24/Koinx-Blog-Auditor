"""Audit control endpoints: start and status."""

import asyncio

from fastapi import APIRouter, HTTPException, Depends

from api.schemas import AuditStartRequest, AuditStartResponse, AuditStatusResponse
from api.state import audit_state
from api.audit_runner import start_audit
from api.auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.post("/start", response_model=AuditStartResponse)
async def start_audit_endpoint(
    body: AuditStartRequest,
    user: dict = Depends(get_current_user),
):
    if audit_state.is_running:
        raise HTTPException(status_code=409, detail="An audit is already running.")
    asyncio.ensure_future(
        start_audit(
            post_id=body.post_id,
            started_by=user["name"],
            category=body.category,
        )
    )
    return AuditStartResponse(message="Audit started", status="running")


@router.get("/status", response_model=AuditStatusResponse)
async def audit_status():
    return AuditStatusResponse(
        running=audit_state.is_running,
        progress=audit_state.progress if audit_state.progress else None,
    )
