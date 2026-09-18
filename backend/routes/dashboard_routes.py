"""Dashboard summary routes - aggregated stats for the frontend's main view."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database import models
from database.schemas import DashboardSummary
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{server_id}", response_model=DashboardSummary)
def get_dashboard(server_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    server = db.query(models.Server).get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    total_scans = db.query(models.ScanResult).filter(models.ScanResult.server_id == server_id).count()
    last_scan = (
        db.query(models.ScanResult)
        .filter(models.ScanResult.server_id == server_id)
        .order_by(models.ScanResult.scanned_at.desc())
        .first()
    )

    open_incidents = (
        db.query(models.DriftIncident)
        .join(models.ScanResult)
        .filter(models.ScanResult.server_id == server_id, models.DriftIncident.status == "open")
        .count()
    )

    critical = (
        db.query(models.AIAnalysis)
        .join(models.DriftIncident)
        .join(models.ScanResult)
        .filter(models.ScanResult.server_id == server_id, models.AIAnalysis.severity == "HIGH")
        .count()
    )

    return DashboardSummary(
        server_status="compliant" if (last_scan and last_scan.drift_count == 0) else
                      ("drift_detected" if last_scan else "unknown"),
        compliance_percent=last_scan.compliance_percent if last_scan else 100.0,
        total_scans=total_scans,
        drift_incidents=open_incidents,
        critical_issues=critical,
        last_scan_time=last_scan.scanned_at if last_scan else None,
        cpu_percent=last_scan.cpu_percent if last_scan else None,
        memory_percent=last_scan.memory_percent if last_scan else None,
    )
