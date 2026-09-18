"""
Remediation routes. This is the ONLY place that can change server state,
and it strictly REQUIRES `confirm: true` from an authenticated user.
The AI's recommendation text is never used to build a command - only the
drift's structured category/item are passed to remediation/ansible_runner.py,
which maps them to a small fixed set of pre-written, reviewed playbook tags.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database import models
from database.schemas import RemediationRequest, RemediationOut
from services.auth_service import get_current_user
from remediation.ansible_runner import remediate

router = APIRouter(prefix="/api/remediation", tags=["remediation"])


@router.post("", response_model=RemediationOut, status_code=201)
def remediate_incident(payload: RemediationRequest, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    if not payload.confirm:
        # Defense in depth: refuse to act without an explicit, logged approval.
        raise HTTPException(status_code=400, detail="Remediation requires confirm=true")

    incident = db.query(models.DriftIncident).get(payload.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Drift incident not found")

    scan = db.query(models.ScanResult).get(incident.scan_id)
    server = db.query(models.Server).get(scan.server_id)

    result = remediate(
        drift={
            "category": incident.category,
            "item_name": incident.item_name,
            "expected_value": incident.expected_value,
            "actual_value": incident.actual_value,
        },
        approved_by=current_user.username,
        is_demo=server.is_demo,
    )

    log = models.RemediationLog(
        incident_id=incident.id,
        approved_by=current_user.username,
        action_taken=result["action_taken"],
        playbook_used=result["playbook_used"],
        success=result["success"],
        output_log=result["output_log"],
    )
    db.add(log)
    if result["success"]:
        incident.status = "remediated"
    db.commit()
    db.refresh(log)
    return log
