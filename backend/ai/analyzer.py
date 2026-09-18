"""
ConfigSentinel - AI Drift Analyzer
---------------------------------------
Sends a DETECTED drift item (real data, produced by scanner/drift_engine.py)
to an LLM (Anthropic Claude) and asks it to explain the drift in plain
English for a dashboard user.

STRICT SAFETY RULES (enforced by design, not just by prompt):
1. The AI is given ONLY the drift facts (category, item, expected, actual).
   It is never given SSH access, credentials, or any tool that could
   reach the server.
2. The AI's response is parsed into fixed fields (what_changed,
   why_problem, severity, possible_cause, recommendation). It is TEXT
   ONLY - there is no code path anywhere in this file, or in
   remediation/, that takes the AI's output and executes it as a
   command. Remediation always runs a pre-written, human-reviewed
   Ansible task, chosen by category, and only after explicit user
   confirmation via the /remediation/execute endpoint.
3. If the AI API is unavailable or ANTHROPIC_API_KEY is not set, we fall
   back to a clearly-labeled rule-based explanation so the demo still
   works end-to-end - this is NOT presented as if it came from the AI.
"""

import json
import anthropic
from config import settings

SYSTEM_PROMPT = """You are a cloud configuration security assistant embedded in a \
DevOps dashboard called ConfigSentinel. You will be given a single detected \
configuration drift on a Linux server (what was expected vs what was found). \

Your job is ONLY to explain and advise - you have no ability to access the \
server and you must NEVER suggest that you can execute anything yourself. \
Always phrase recommendations as something a human operator should do.

Respond ONLY with a valid JSON object (no markdown, no commentary) with \
exactly these keys:
{
  "what_changed": "one or two sentence factual description of the drift",
  "why_problem": "why this could be a problem, in plain English",
  "severity": "LOW | MEDIUM | HIGH",
  "possible_cause": "one or two likely causes",
  "recommendation": "a clear, safe recommended fix a human should approve and run"
}"""


def _build_user_prompt(drift: dict) -> str:
    return (
        f"Detected configuration drift:\n"
        f"- Category: {drift['category']}\n"
        f"- Item: {drift['item_name']}\n"
        f"- Expected: {drift['expected_value']}\n"
        f"- Actual: {drift['actual_value']}\n\n"
        f"Explain this drift for a non-expert dashboard user."
    )


def analyze_drift(drift: dict) -> dict:
    """
    drift: {"category", "item_name", "expected_value", "actual_value"}
    returns: {"what_changed", "why_problem", "severity", "possible_cause",
              "recommendation", "raw_model_response"}
    """
    if not settings.ANTHROPIC_API_KEY:
        return _fallback_analysis(drift, reason="No ANTHROPIC_API_KEY configured")

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(drift)}],
        )
        raw_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        parsed = _safe_parse_json(raw_text)
        parsed["raw_model_response"] = raw_text
        return parsed
    except Exception as exc:  # noqa: BLE001 - we want a graceful demo fallback
        return _fallback_analysis(drift, reason=f"AI request failed: {exc}")


def _safe_parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1)
    try:
        data = json.loads(text)
        return {
            "what_changed": data.get("what_changed", ""),
            "why_problem": data.get("why_problem", ""),
            "severity": data.get("severity", "MEDIUM").upper(),
            "possible_cause": data.get("possible_cause", ""),
            "recommendation": data.get("recommendation", ""),
        }
    except json.JSONDecodeError:
        return {
            "what_changed": text[:300],
            "why_problem": "Could not fully parse AI response - showing raw text.",
            "severity": "MEDIUM",
            "possible_cause": "N/A",
            "recommendation": "Review manually.",
        }


# --- Rule-based fallback (used only if the AI API is unreachable/unset) -----
_SEVERITY_MAP = {
    "service": "MEDIUM",
    "package": "MEDIUM",
    "user": "HIGH",
    "file": "HIGH",
    "port": "HIGH",
}


def _fallback_analysis(drift: dict, reason: str) -> dict:
    category = drift["category"]
    return {
        "what_changed": (
            f"{drift['item_name']} was expected to be '{drift['expected_value']}' "
            f"but was found to be '{drift['actual_value']}'."
        ),
        "why_problem": (
            "This deviates from the approved desired-state configuration and "
            "may indicate misconfiguration, manual tampering, or a failed process."
        ),
        "severity": _SEVERITY_MAP.get(category, "MEDIUM"),
        "possible_cause": "Manual change, failed deployment, or crashed process.",
        "recommendation": f"Review and restore the expected {category} configuration.",
        "raw_model_response": f"[FALLBACK - not generated by AI: {reason}]",
    }
