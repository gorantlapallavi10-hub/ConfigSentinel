"""
ConfigSentinel - Simulated Server (Demo Mode)
-------------------------------------------------
This module fakes a Linux server's configuration state entirely in memory,
so the whole ConfigSentinel workflow (scan -> detect drift -> AI analysis
-> remediate -> re-scan) can be demonstrated WITHOUT any AWS account or
real EC2 instance.

It is intentionally simple: a single in-memory dictionary that starts out
matching desired_state.yaml exactly ("compliant"), and can be mutated by
the /demo/break-config endpoint to simulate real-world drift (e.g. someone
stops nginx, or a package gets removed).

This is not a fake AI feature - it only fakes the *server*. The scanner,
drift engine and AI analysis all run for real against this simulated data,
exactly as they would against a real EC2 instance.
"""

import copy

# The "actual" live state of the simulated server. Starts fully compliant.
_INITIAL_STATE = {
    "packages": ["nginx", "openssh-server"],
    "services": {
        "nginx": {"state": "running"},
        "ssh": {"state": "running"},
    },
    "ports": [22, 80],
    "users": ["admin", "ec2-user"],
    "files": {
        "/etc/nginx/nginx.conf": {"exists": True},
    },
    "cpu_percent": 12.4,
    "memory_percent": 38.2,
}

_state = copy.deepcopy(_INITIAL_STATE)


def get_state():
    """Return the current simulated actual state (as the scanner would see it)."""
    return copy.deepcopy(_state)


def reset_state():
    """Restore the simulated server to a fully compliant state."""
    global _state
    _state = copy.deepcopy(_INITIAL_STATE)
    return get_state()


# --- Scenario helpers used by the "Simulate Drift" demo button -------------

def break_stop_nginx():
    """Scenario 1: nginx service gets stopped unexpectedly."""
    _state["services"]["nginx"]["state"] = "stopped"


def break_remove_package():
    """Scenario 2: a required package gets uninstalled."""
    if "openssh-server" in _state["packages"]:
        _state["packages"].remove("openssh-server")


def break_open_port():
    """Scenario 3: an unexpected/unauthorized port gets opened (e.g. 8080)."""
    if 8080 not in _state["ports"]:
        _state["ports"].append(8080)


def break_remove_user():
    """Scenario 4: a required admin user is missing."""
    if "admin" in _state["users"]:
        _state["users"].remove("admin")


def break_delete_config_file():
    """Scenario 5: an important configuration file is deleted."""
    _state["files"]["/etc/nginx/nginx.conf"]["exists"] = False


SCENARIOS = {
    "stop_nginx": break_stop_nginx,
    "remove_package": break_remove_package,
    "open_port": break_open_port,
    "remove_user": break_remove_user,
    "delete_config_file": break_delete_config_file,
}


def apply_scenario(name: str):
    if name not in SCENARIOS:
        raise ValueError(f"Unknown demo scenario: {name}")
    SCENARIOS[name]()
    return get_state()


# --- Remediation hooks (used by demo remediation instead of real Ansible) ---

def remediate_service(service_name: str, desired_state: str):
    if service_name in _state["services"]:
        _state["services"][service_name]["state"] = desired_state


def remediate_install_package(package_name: str):
    if package_name not in _state["packages"]:
        _state["packages"].append(package_name)


def remediate_close_port(port: int):
    if port in _state["ports"]:
        _state["ports"].remove(port)


def remediate_create_user(username: str):
    if username not in _state["users"]:
        _state["users"].append(username)


def remediate_restore_file(path: str):
    if path in _state["files"]:
        _state["files"][path]["exists"] = True
