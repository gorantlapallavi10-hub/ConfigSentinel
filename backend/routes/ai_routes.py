"""
AI analysis routes. Sends ONLY the structured drift facts (category,
item, expected, actual) to the LLM and stores its explanation. The AI
response is never executed - see ai/analyzer.py for the safety design.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database import models
from database.schemas import AIAnalysisOut
from services.auth_service import get_current_user
from ai.analyzer import analyze_drift

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/analyze/{incident_id}", response_model=AIAnalysisOut, status_code=201)
def analyze_incident(incident_id: int, db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user)):
    incident = db.query(models.DriftIncident).get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Drift incident not found")

    result = analyze_drift({
        "category": incident.category,
        "item_name": incident.item_name,
        "expected_value": incident.expected_value,
        "actual_value": incident.actual_value,
    })

    analysis = models.AIAnalysis(
        incident_id=incident.id,
        what_changed=result["what_changed"],
        why_problem=result["why_problem"],
        severity=result["severity"],
        possible_cause=result["possible_cause"],
        recommendation=result["recommendation"],
        raw_model_response=result.get("raw_model_response", ""),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("/analysis/{incident_id}", response_model=AIAnalysisOut)
def get_analysis(incident_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    analysis = db.query(models.AIAnalysis).filter(models.AIAnalysis.incident_id == incident_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No AI analysis yet for this incident")
    return analysis
