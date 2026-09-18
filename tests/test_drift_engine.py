"""
Unit tests for the drift detection engine (backend/scanner/drift_engine.py).
Run with:  cd backend && pytest ../tests -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from scanner.drift_engine import detect_drift, compliance_percent

DESIRED = {
    "packages": ["nginx"],
    "services": {"nginx": {"state": "running"}},
    "ports": [22, 80],
    "users": ["admin"],
    "files": [{"path": "/etc/nginx/nginx.conf", "must_exist": True}],
}


def test_no_drift_when_state_matches():
    actual = {
        "packages": ["nginx"],
        "services": {"nginx": {"state": "running"}},
        "ports": [22, 80],
        "users": ["admin"],
        "files": {"/etc/nginx/nginx.conf": {"exists": True}},
    }
    drifts = detect_drift(DESIRED, actual)
    assert drifts == []
    assert compliance_percent(DESIRED, drifts) == 100.0


def test_detects_stopped_service():
    actual = {
        "packages": ["nginx"],
        "services": {"nginx": {"state": "stopped"}},
        "ports": [22, 80],
        "users": ["admin"],
        "files": {"/etc/nginx/nginx.conf": {"exists": True}},
    }
    drifts = detect_drift(DESIRED, actual)
    assert len(drifts) == 1
    assert drifts[0]["category"] == "service"
    assert drifts[0]["item_name"] == "nginx"
    assert drifts[0]["expected_value"] == "running"
    assert drifts[0]["actual_value"] == "stopped"


def test_detects_missing_package():
    actual = {
        "packages": [],
        "services": {"nginx": {"state": "running"}},
        "ports": [22, 80],
        "users": ["admin"],
        "files": {"/etc/nginx/nginx.conf": {"exists": True}},
    }
    drifts = detect_drift(DESIRED, actual)
    assert any(d["category"] == "package" and d["item_name"] == "nginx" for d in drifts)


def test_detects_unexpected_open_port():
    actual = {
        "packages": ["nginx"],
        "services": {"nginx": {"state": "running"}},
        "ports": [22, 80, 8080],
        "users": ["admin"],
        "files": {"/etc/nginx/nginx.conf": {"exists": True}},
    }
    drifts = detect_drift(DESIRED, actual)
    assert any(d["item_name"] == "port 8080" for d in drifts)


def test_detects_missing_user():
    actual = {
        "packages": ["nginx"],
        "services": {"nginx": {"state": "running"}},
        "ports": [22, 80],
        "users": [],
        "files": {"/etc/nginx/nginx.conf": {"exists": True}},
    }
    drifts = detect_drift(DESIRED, actual)
    assert any(d["category"] == "user" and d["item_name"] == "admin" for d in drifts)


def test_detects_missing_file():
    actual = {
        "packages": ["nginx"],
        "services": {"nginx": {"state": "running"}},
        "ports": [22, 80],
        "users": ["admin"],
        "files": {"/etc/nginx/nginx.conf": {"exists": False}},
    }
    drifts = detect_drift(DESIRED, actual)
    assert any(d["category"] == "file" for d in drifts)


def test_compliance_percent_drops_with_more_drift():
    actual_bad = {
        "packages": [],
        "services": {"nginx": {"state": "stopped"}},
        "ports": [],
        "users": [],
        "files": {},
    }
    drifts = detect_drift(DESIRED, actual_bad)
    percent = compliance_percent(DESIRED, drifts)
    assert percent < 100.0
