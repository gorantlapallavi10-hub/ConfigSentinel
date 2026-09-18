"""
Tests for the AI analyzer's safe fallback path (runs without any real API
key/network access, so it's safe for CI).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from ai.analyzer import analyze_drift

SAMPLE_DRIFT = {
    "category": "service",
    "item_name": "nginx",
    "expected_value": "running",
    "actual_value": "stopped",
}


def test_fallback_analysis_used_without_api_key(monkeypatch):
    monkeypatch.setattr("config.settings.ANTHROPIC_API_KEY", "")
    result = analyze_drift(SAMPLE_DRIFT)
    assert result["severity"] in {"LOW", "MEDIUM", "HIGH"}
    assert "nginx" in result["what_changed"]
    assert "FALLBACK" in result["raw_model_response"]


def test_analysis_never_contains_a_shell_command_field():
    result = analyze_drift(SAMPLE_DRIFT)
    # Safety check: the AI's output schema has no field that could be
    # interpreted as an executable command - only explanatory text fields.
    assert set(result.keys()) <= {
        "what_changed", "why_problem", "severity",
        "possible_cause", "recommendation", "raw_model_response",
    }
