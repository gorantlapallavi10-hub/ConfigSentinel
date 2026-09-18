"""
ConfigSentinel - Drift Detection Engine
--------------------------------------------
Pure comparison logic: takes the DESIRED state (parsed from
demo/desired_state.yaml) and the ACTUAL state (from either the demo
simulator or the real EC2 scanner) and returns a list of drift items.

This module has no side effects, does not touch the network, and does
not call the AI. It is deliberately kept small so it is easy to explain
and defend in a viva.
"""

import yaml
from typing import List, Dict, Any


def load_desired_state(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def detect_drift(desired: Dict[str, Any], actual: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Compares desired vs actual configuration and returns a list of drift
    dicts, each shaped as:
        {
            "category": "package" | "service" | "port" | "user" | "file",
            "item_name": str,
            "expected_value": str,
            "actual_value": str,
        }
    """
    drifts: List[Dict[str, str]] = []

    # --- Packages: every desired package must be installed ---
    actual_packages = set(actual.get("packages", []))
    for pkg in desired.get("packages", []):
        if pkg not in actual_packages:
            drifts.append({
                "category": "package",
                "item_name": pkg,
                "expected_value": "installed",
                "actual_value": "missing",
            })

    # --- Services: each must be in the expected state (e.g. running) ---
    desired_services = desired.get("services", {})
    actual_services = actual.get("services", {})
    for svc_name, svc_cfg in desired_services.items():
        expected_state = svc_cfg.get("state", "running")
        actual_state = actual_services.get(svc_name, {}).get("state", "unknown")
        if actual_state != expected_state:
            drifts.append({
                "category": "service",
                "item_name": svc_name,
                "expected_value": expected_state,
                "actual_value": actual_state,
            })

    # --- Ports: desired ports must be open; unexpected extra ports flagged ---
    desired_ports = set(desired.get("ports", []))
    actual_ports = set(actual.get("ports", []))

    for port in desired_ports - actual_ports:
        drifts.append({
            "category": "port",
            "item_name": f"port {port}",
            "expected_value": "open",
            "actual_value": "closed",
        })

    for port in actual_ports - desired_ports:
        drifts.append({
            "category": "port",
            "item_name": f"port {port}",
            "expected_value": "closed",
            "actual_value": "open (unexpected)",
        })

    # --- Users: every desired user must exist ---
    actual_users = set(actual.get("users", []))
    for user in desired.get("users", []):
        if user not in actual_users:
            drifts.append({
                "category": "user",
                "item_name": user,
                "expected_value": "exists",
                "actual_value": "missing",
            })

    # --- Files: important config files must exist ---
    desired_files = desired.get("files", [])
    actual_files = actual.get("files", {})
    for f in desired_files:
        path = f["path"]
        must_exist = f.get("must_exist", True)
        exists = actual_files.get(path, {}).get("exists", False)
        if must_exist and not exists:
            drifts.append({
                "category": "file",
                "item_name": path,
                "expected_value": "exists",
                "actual_value": "missing",
            })

    return drifts


def compliance_percent(desired: Dict[str, Any], drifts: List[Dict[str, str]]) -> float:
    """A simple, explainable compliance score: 1 check per desired item."""
    total_checks = (
        len(desired.get("packages", []))
        + len(desired.get("services", {}))
        + len(desired.get("ports", []))
        + len(desired.get("users", []))
        + len(desired.get("files", []))
    )
    if total_checks == 0:
        return 100.0
    passed = max(total_checks - len(drifts), 0)
    return round((passed / total_checks) * 100, 1)
