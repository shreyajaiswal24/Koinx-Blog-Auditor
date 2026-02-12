"""Report download endpoint."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config.settings import OUTPUT_DIR

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/download")
def download_report():
    """Download the latest Excel audit report."""
    if not OUTPUT_DIR.exists():
        raise HTTPException(status_code=404, detail="No reports available.")

    xlsx_files = sorted(OUTPUT_DIR.glob("tax_audit_report_*.xlsx"), reverse=True)
    if not xlsx_files:
        raise HTTPException(status_code=404, detail="No reports available.")

    latest = xlsx_files[0]
    return FileResponse(
        path=str(latest),
        filename=latest.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
