"""
ConfigSentinel - Pydantic Schemas
------------------------------------
Request/response validation models, kept separate from the SQLAlchemy
ORM models so internal DB fields never leak into the API and so FastAPI
gets automatic input validation (part of our security requirements).
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Server ----------
class ServerCreate(BaseModel):
    name: str
    host: str = "demo"
    is_demo: bool = True
    ssh_user: Optional[str] = "ec2-user"
    ssh_key_path: Optional[str] = None


class ServerOut(BaseModel):
    id: int
    name: str
    host: str
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Scan / Drift ----------
class DriftIncidentOut(BaseModel):
    id: int
    category: str
    item_name: str
    expected_value: str
    actual_value: str
    status: str
    detected_at: datetime

    class Config:
        from_attributes = True


class ScanResultOut(BaseModel):
    id: int
    server_id: int
    scanned_at: datetime
    compliance_percent: float
    drift_count: int
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    incidents: List[DriftIncidentOut] = []

    class Config:
        from_attributes = True


# ---------- AI ----------
class AIAnalysisOut(BaseModel):
    id: int
    incident_id: int
    what_changed: str
    why_problem: str
    severity: str
    possible_cause: str
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Remediation ----------
class RemediationRequest(BaseModel):
    incident_id: int
    confirm: bool = Field(..., description="Must be explicitly true; the API refuses otherwise.")


class RemediationOut(BaseModel):
    id: int
    incident_id: int
    approved_by: str
    action_taken: str
    success: bool
    executed_at: datetime

    class Config:
        from_attributes = True


# ---------- Demo ----------
class DemoScenarioRequest(BaseModel):
    scenario: str


# ---------- Dashboard ----------
class DashboardSummary(BaseModel):
    server_status: str
    compliance_percent: float
    total_scans: int
    drift_incidents: int
    critical_issues: int
    last_scan_time: Optional[datetime]
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
