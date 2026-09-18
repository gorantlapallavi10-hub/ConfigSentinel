"""
ConfigSentinel - FastAPI Application Entrypoint
----------------------------------------------------
Wires together the database, all route modules, and CORS so the React
frontend (running on a different port) can call the API.

Run locally with:
    cd backend
    uvicorn app:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.db import init_db
from routes import (
    auth_routes,
    server_routes,
    scan_routes,
    ai_routes,
    remediation_routes,
    dashboard_routes,
    demo_routes,
)

app = FastAPI(
    title="ConfigSentinel API",
    description="AI-Assisted Cloud Configuration Drift Detection & Remediation System",
    version="1.0.0",
)

# CORS: allow the React dev server / deployed frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend's real origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(server_routes.router)
app.include_router(scan_routes.router)
app.include_router(ai_routes.router)
app.include_router(remediation_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(demo_routes.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "service": "ConfigSentinel",
        "status": "running",
        "demo_mode": settings.DEMO_MODE,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
