"""FastAPI application assembly."""

from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.auth import get_current_user, seed_user
from api.ws import router as ws_router
from api.routes.auth import router as auth_router
from api.routes.audit import router as audit_router
from api.routes.findings import router as findings_router
from api.routes.stats import router as stats_router
from api.routes.runs import router as runs_router
from api.routes.reports import router as reports_router


def create_app() -> FastAPI:
    app = FastAPI(title="KoinX Tax Auditor API")

    # CORS — allow Vite dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Public routes (no auth required)
    app.include_router(auth_router)

    # Protected routes (auth required)
    app.include_router(ws_router)
    app.include_router(audit_router, dependencies=[Depends(get_current_user)])
    app.include_router(findings_router, dependencies=[Depends(get_current_user)])
    app.include_router(stats_router, dependencies=[Depends(get_current_user)])
    app.include_router(runs_router, dependencies=[Depends(get_current_user)])
    app.include_router(reports_router, dependencies=[Depends(get_current_user)])

    # Seed default admin user on startup
    @app.on_event("startup")
    def _seed_default_users():
        seed_user("admin@koinx.com", "admin123", "Admin")

    # Serve built frontend in production (if exists)
    dist_dir = Path(__file__).parent.parent / "frontend" / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app


app = create_app()
