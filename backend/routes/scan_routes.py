"""
Scan routes: trigger a configuration scan (demo simulator or real EC2 over
SSH), run drift detection against the desired state, and persist results.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from config import settings
from database.db import get_db
from database import models
from database.schemas import ScanResultOut
from services.auth_service import get_current_user
from scanner.drift_engine import load_desired_state, detect_drift, compliance_percent
from demo import simulated_server

router = APIRouter(prefix="/api/scans", tags=["scans"])


def _get_actual_state(server: models.Server) -> dict:
    if server.is_demo:
        return simulated_server.get_state()
    # Real mode - import lazily so paramiko isn't required for a pure demo setup
    from scanner.ec2_scanner import EC2Scanner
    scanner = EC2Scanner(host=server.host, username=server.ssh_user, key_path=server.ssh_key_path)
    return scanner.scan()


@router.post("/{server_id}/run", response_model=ScanResultOut, status_code=201)
def run_scan(server_id: int, db: Session = Depends(get_db),
             current_user: models.User = Depends(get_current_user)):
    server = db.query(models.Server).get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    desired = load_desired_state(settings.DESIRED_STATE_PATH)
    actual = _get_actual_state(server)

    drifts = detect_drift(desired, actual)
    compliance = compliance_percent(desired, drifts)

    scan = models.ScanResult(
        server_id=server.id,
        actual_state_json=json.dumps(actual),
        compliance_percent=compliance,
        drift_count=len(drifts),
        cpu_percent=actual.get("cpu_percent"),
        memory_percent=actual.get("memory_percent"),
    )
    db.add(scan)
    db.flush()  # get scan.id before adding children

    for d in drifts:
        db.add(models.DriftIncident(scan_id=scan.id, **d))

    db.commit()
    db.refresh(scan)
    return scan


@router.get("/{server_id}/history", response_model=List[ScanResultOut])
def scan_history(server_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    return (
        db.query(models.ScanResult)
        .filter(models.ScanResult.server_id == server_id)
        .order_by(models.ScanResult.scanned_at.desc())
        .limit(50)
        .all()
    )


@router.get("/{server_id}/latest", response_model=ScanResultOut)
def latest_scan(server_id: int, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    scan = (
        db.query(models.ScanResult)
        .filter(models.ScanResult.server_id == server_id)
        .order_by(models.ScanResult.scanned_at.desc())
        .first()
    )
    if not scan:
        raise HTTPException(status_code=404, detail="No scans yet for this server")
    return scan
