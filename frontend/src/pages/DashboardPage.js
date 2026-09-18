import React, { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  listServers,
  createServer,
  runScan,
  latestScan,
  dashboardSummary,
  demoScenarios,
  breakConfig,
  resetDemo,
} from "../api/servers";
import { logout } from "../api/auth";
import StatCard from "../components/StatCard";
import IncidentCard from "../components/IncidentCard";

export default function DashboardPage() {
  const [server, setServer] = useState(null);
  const [summary, setSummary] = useState(null);
  const [scan, setScan] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const refresh = useCallback(async (serverId) => {
    const [s, sc] = await Promise.all([dashboardSummary(serverId), latestScan(serverId).catch(() => null)]);
    setSummary(s);
    setScan(sc);
  }, []);

  useEffect(() => {
    (async () => {
      let servers = await listServers();
      let active = servers[0];
      if (!active) {
        active = await createServer({ name: "Demo EC2 Instance", host: "demo", is_demo: true });
      }
      setServer(active);
      const scen = await demoScenarios();
      setScenarios(scen.scenarios);
      await refresh(active.id);
    })();
  }, [refresh]);

  async function handleScanNow() {
    if (!server) return;
    setBusy(true);
    try {
      await runScan(server.id);
      await refresh(server.id);
    } finally {
      setBusy(false);
    }
  }

  async function handleSimulateDrift(scenario) {
    setBusy(true);
    try {
      await breakConfig(scenario);
      await runScan(server.id);
      await refresh(server.id);
    } finally {
      setBusy(false);
    }
  }

  async function handleReset() {
    setBusy(true);
    try {
      await resetDemo();
      await runScan(server.id);
      await refresh(server.id);
    } finally {
      setBusy(false);
    }
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  if (!server || !summary) {
    return <div className="loading-screen">Loading ConfigSentinel...</div>;
  }

  return (
    <div className="dashboard">
      <header className="topbar">
        <h1>🛡️ ConfigSentinel</h1>
        <div className="topbar-actions">
          <Link to="/history" className="btn-secondary">View History</Link>
          <button className="btn-link" onClick={handleLogout}>Log out</button>
        </div>
      </header>

      <section className="server-banner">
        <div>
          <strong>{server.name}</strong> &nbsp;
          <span className="pill">{server.is_demo ? "DEMO MODE" : server.host}</span>
        </div>
        <div className={`status-pill ${summary.server_status}`}>
          {summary.server_status.replace("_", " ").toUpperCase()}
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="Compliance" value={`${summary.compliance_percent}%`} />
        <StatCard label="Total Scans" value={summary.total_scans} />
        <StatCard label="Drift Incidents" value={summary.drift_incidents} tone={summary.drift_incidents > 0 ? "warn" : ""} />
        <StatCard label="Critical Issues" value={summary.critical_issues} tone={summary.critical_issues > 0 ? "danger" : ""} />
        <StatCard label="CPU Usage" value={summary.cpu_percent != null ? `${summary.cpu_percent}%` : "N/A"} />
        <StatCard label="Memory Usage" value={summary.memory_percent != null ? `${summary.memory_percent}%` : "N/A"} />
      </section>

      <section className="actions-bar">
        <button className="btn-primary" onClick={handleScanNow} disabled={busy}>
          {busy ? "Working..." : "Scan Now"}
        </button>
        {server.is_demo && (
          <>
            <div className="demo-scenarios">
              <span>Simulate drift:</span>
              {scenarios.map((s) => (
                <button key={s} className="btn-secondary" onClick={() => handleSimulateDrift(s)} disabled={busy}>
                  {s.replaceAll("_", " ")}
                </button>
              ))}
            </div>
            <button className="btn-link" onClick={handleReset} disabled={busy}>
              Reset demo server
            </button>
          </>
        )}
      </section>

      <section className="incidents-section">
        <h2>Latest Scan {scan && <span className="timestamp">({new Date(scan.scanned_at).toLocaleString()})</span>}</h2>
        {!scan || scan.incidents.length === 0 ? (
          <p className="all-clear">✅ No configuration drift detected. Server is compliant.</p>
        ) : (
          <div className="incidents-list">
            {scan.incidents.map((inc) => (
              <IncidentCard key={inc.id} incident={inc} onChanged={() => refresh(server.id)} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
