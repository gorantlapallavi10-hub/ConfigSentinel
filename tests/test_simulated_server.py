"""Unit tests for the demo/simulated_server module (drift scenarios + remediation)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from demo import simulated_server


def setup_function():
    simulated_server.reset_state()


def test_initial_state_is_compliant():
    state = simulated_server.get_state()
    assert state["services"]["nginx"]["state"] == "running"
    assert "admin" in state["users"]


def test_stop_nginx_scenario():
    simulated_server.apply_scenario("stop_nginx")
    state = simulated_server.get_state()
    assert state["services"]["nginx"]["state"] == "stopped"


def test_remediate_service_restores_state():
    simulated_server.apply_scenario("stop_nginx")
    simulated_server.remediate_service("nginx", "running")
    state = simulated_server.get_state()
    assert state["services"]["nginx"]["state"] == "running"


def test_reset_restores_full_compliance():
    simulated_server.apply_scenario("remove_user")
    simulated_server.reset_state()
    state = simulated_server.get_state()
    assert "admin" in state["users"]
