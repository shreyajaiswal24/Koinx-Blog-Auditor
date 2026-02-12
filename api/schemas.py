"""Pydantic models for API request/response shapes."""

from typing import List, Optional
from pydantic import BaseModel


class AuditStartRequest(BaseModel):
    post_id: Optional[int] = None


class AuditStartResponse(BaseModel):
    message: str
    status: str


class AuditStatusResponse(BaseModel):
    running: bool
    progress: Optional[dict] = None


class FindingOut(BaseModel):
    id: int
    run_id: int
    blog_url: str
    blog_title: str
    section_heading: str
    exact_quote: str
    issue_type: str
    description: str
    suggested_update: str
    source: str
    llm_confidence: float
    confidence: float
    priority: str
    status: str
    finding_hash: str


class PaginatedFindings(BaseModel):
    items: List[FindingOut]
    total: int
    page: int
    per_page: int
    pages: int


class RunOut(BaseModel):
    id: int
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_posts: int
    total_findings: int
    total_api_calls: int
    total_tokens: int


class StatsResponse(BaseModel):
    total_findings: int
    high: int
    medium: int
    low: int
    new: int
    previously_identified: int
    resolved: int
    total_runs: int
    last_run: Optional[RunOut] = None
