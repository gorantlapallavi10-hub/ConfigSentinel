"""
ConfigSentinel - Remediation Engine
----------------------------------------
Executes a FIXED, human-written Ansible task for a given drift category.
This is the ONLY place in the whole application that changes server state.

SAFETY DESIGN:
- The caller (routes/remediation_routes.py) requires `confirm: true` from
  the user before this module is ever invoked.
- The AI's recommendation text is NEVER passed into a shell or into
  Ansible. We only use the drift's `category` and `item_name` (structured
  data that came from our own scanner) to pick ONE of a small, fixed set
  of pre-written Ansible tags below.
- In demo mode, no real Ansible/SSH call is made - the simulated server
  state is mutated instead, so the whole workflow can be shown safely
  without any real infrastructure.
"""

import subprocess
from config import settings
from demo import simulated_server

# Maps a drift category to a fixed, reviewed Ansible tag. Nothing here is
# built dynamically from AI text or free-form user input.
_CATEGORY_TO_TAG = {
    "service": "fix_service",
    "package": "install_package",
    "user": "create_user",
    "file": "restore_file",
    "port": "review_port",   # ports are informational -> flagged for manual review, not auto-changed
}


def remediate(drift: dict, approved_by: str, is_demo: bool = True) -> dict:
    """
    drift: {"category", "item_name", "expected_value", "actual_value"}
    Returns {"success": bool, "action_taken": str, "output_log": str, "playbook_used": str}
    """
    category = drift["category"]
    item = drift["item_name"]

    if category == "port":
        return {
            "success": False,
            "action_taken": f"Manual review required for {item} (ports are not auto-remediated).",
            "output_log": "Port changes are flagged for manual review for security reasons.",
            "playbook_used": "n/a",
        }

    if is_demo:
        return _remediate_demo(drift)

    return _remediate_real(drift, approved_by)


def _remediate_demo(drift: dict) -> dict:
    """Mutates the in-memory simulated server instead of calling real Ansible."""
    category, item = drift["category"], drift["item_name"]

    if category == "service":
        simulated_server.remediate_service(item, drift["expected_value"])
        action = f"Started/restored service '{item}' to state '{drift['expected_value']}'."
    elif category == "package":
        simulated_server.remediate_install_package(item)
        action = f"Installed missing package '{item}'."
    elif category == "user":
        simulated_server.remediate_create_user(item)
        action = f"Created missing user '{item}'."
    elif category == "file":
        simulated_server.remediate_restore_file(item)
        action = f"Restored missing configuration file '{item}'."
    else:
        return {"success": False, "action_taken": "Unsupported category", "output_log": "", "playbook_used": "n/a"}

    return {
        "success": True,
        "action_taken": action,
        "output_log": f"[DEMO MODE] {action} (simulated - no real server was touched)",
        "playbook_used": f"remediation.yml --tags {_CATEGORY_TO_TAG.get(category)} (simulated)",
    }


def _remediate_real(drift: dict, approved_by: str) -> dict:
    """Runs the real Ansible playbook against the configured EC2 inventory."""
    category = drift["category"]
    tag = _CATEGORY_TO_TAG.get(category)
    if not tag:
        return {"success": False, "action_taken": "No remediation available", "output_log": "", "playbook_used": "n/a"}

    extra_vars = f"target_item={drift['item_name']} desired_value={drift['expected_value']}"
    cmd = [
        "ansible-playbook",
        settings.ANSIBLE_PLAYBOOK_PATH,
        "-i", settings.ANSIBLE_INVENTORY_PATH,
        "--tags", tag,
        "--extra-vars", extra_vars,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        success = result.returncode == 0
        return {
            "success": success,
            "action_taken": f"Ran Ansible tag '{tag}' for {drift['item_name']} (approved by {approved_by})",
            "output_log": result.stdout + "\n" + result.stderr,
            "playbook_used": f"remediation.yml --tags {tag}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "action_taken": "Ansible execution failed",
            "output_log": str(exc),
            "playbook_used": f"remediation.yml --tags {tag}",
        }
