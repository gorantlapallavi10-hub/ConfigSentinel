"""
ConfigSentinel - Database Models
----------------------------------
Tables:
- User            : login accounts for the dashboard
- Server          : cloud/Linux servers being monitored (EC2 or demo)
- ScanResult      : one row per configuration scan performed
- DriftIncident   : a specific detected difference between desired and actual state
- AIAnalysis      : AI-generated explanation for a drift incident
- RemediationLog  : record of remediation actions taken (and who approved them)
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    host = Column(String(255), nullable=False)            # EC2 public IP/DNS, or "demo"
    is_demo = Column(Boolean, default=True)                # True => uses simulated scanner
    ssh_user = Column(String(80), default="ec2-user")
    ssh_key_path = Column(String(255), nullable=True)      # path to .pem key; never store key contents in DB
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("ScanResult", back_populates="server", cascade="all, delete-orphan")


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    scanned_at = Column(DateTime, default=datetime.utcnow)
    actual_state_json = Column(Text)        # raw JSON snapshot of what the scanner found
    compliance_percent = Column(Float, default=100.0)
    drift_count = Column(Integer, default=0)
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)

    server = relationship("Server", back_populates="scans")
    incidents = relationship("DriftIncident", back_populates="scan", cascade="all, delete-orphan")


class DriftIncident(Base):
    __tablename__ = "drift_incidents"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scan_results.id"))
    category = Column(String(50))            # package | service | port | user | file
    item_name = Column(String(120))          # e.g. "nginx"
    expected_value = Column(String(255))
    actual_value = Column(String(255))
    status = Column(String(30), default="open")     # open | remediated | ignored
    detected_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("ScanResult", back_populates="incidents")
    analysis = relationship("AIAnalysis", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    remediations = relationship("RemediationLog", back_populates="incident", cascade="all, delete-orphan")


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("drift_incidents.id"))
    what_changed = Column(Text)
    why_problem = Column(Text)
    severity = Column(String(20))            # LOW | MEDIUM | HIGH
    possible_cause = Column(Text)
    recommendation = Column(Text)
    raw_model_response = Column(Text)        # full response text, kept for audit/transparency
    created_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("DriftIncident", back_populates="analysis")


class RemediationLog(Base):
    __tablename__ = "remediation_log"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("drift_incidents.id"))
    approved_by = Column(String(80))
    action_taken = Column(String(255))
    playbook_used = Column(String(120))
    success = Column(Boolean, default=False)
    output_log = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("DriftIncident", back_populates="remediations")
