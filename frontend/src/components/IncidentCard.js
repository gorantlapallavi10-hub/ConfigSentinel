import React, { useState } from "react";
import { analyzeIncident, remediateIncident } from "../api/servers";

const severityColor = { LOW: "#22c55e", MEDIUM: "#f59e0b", HIGH: "#ef4444" };

export default function IncidentCard({ incident, onChanged }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [remediated, setRemediated] = useState(incident.status === "remediated");

  async function handleAnalyze() {
    setLoading(true);
    try {
      const data = await analyzeIncident(incident.id);
      setAnalysis(data);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemediate() {
    setLoading(true);
    try {
      const result = await remediateIncident(incident.id, true);
      if (result.success) setRemediated(true);
      setConfirmOpen(false);
      onChanged && onChanged();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="incident-card">
      <div className="incident-header">
        <span className="incident-category">{incident.category.toUpperCase()}</span>
        <strong>{incident.item_name}</strong>
        {remediated && <span className="badge-ok">Remediated</span>}
      </div>
      <div className="incident-diff">
        Expected: <code>{incident.expected_value}</code> &nbsp;|&nbsp; Actual:{" "}
        <code>{incident.actual_value}</code>
      </div>

      {!analysis && (
        <button className="btn-secondary" onClick={handleAnalyze} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze with AI"}
        </button>
      )}

      {analysis && (
        <div className="ai-analysis">
          <div className="severity" style={{ color: severityColor[analysis.severity] || "#999" }}>
            Severity: {analysis.severity}
          </div>
          <p><strong>What changed:</strong> {analysis.what_changed}</p>
          <p><strong>Why it matters:</strong> {analysis.why_problem}</p>
          <p><strong>Possible cause:</strong> {analysis.possible_cause}</p>
          <p><strong>Recommendation:</strong> {analysis.recommendation}</p>

          {!remediated && (
            <>
              {!confirmOpen ? (
                <button className="btn-primary" onClick={() => setConfirmOpen(true)}>
                  Remediate
                </button>
              ) : (
                <div className="confirm-box">
                  <p>This will run an approved fix on the server. Proceed?</p>
                  <button className="btn-primary" onClick={handleRemediate} disabled={loading}>
                    {loading ? "Applying..." : "Yes, apply fix"}
                  </button>
                  <button className="btn-link" onClick={() => setConfirmOpen(false)}>
                    Cancel
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
