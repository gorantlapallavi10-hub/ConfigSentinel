"""
Demo-mode routes: let the frontend simulate configuration drift without
any AWS account, so the full workflow can be shown in a college viva.
"""
from fastapi import APIRouter, Depends, HTTPException
from database.schemas import DemoScenarioRequest
from database import models
from services.auth_service import get_current_user
from demo import simulated_server

router = APIRouter(prefix="/api/demo", tags=["demo"])

AVAILABLE_SCENARIOS = list(simulated_server.SCENARIOS.keys())


@router.get("/scenarios")
def list_scenarios(current_user: models.User = Depends(get_current_user)):
    return {"scenarios": AVAILABLE_SCENARIOS}


@router.post("/break-config")
def break_config(payload: DemoScenarioRequest, current_user: models.User = Depends(get_current_user)):
    try:
        state = simulated_server.apply_scenario(payload.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": f"Simulated drift scenario '{payload.scenario}' applied.", "state": state}


@router.post("/reset")
def reset_demo(current_user: models.User = Depends(get_current_user)):
    state = simulated_server.reset_state()
    return {"message": "Demo server reset to a fully compliant state.", "state": state}
