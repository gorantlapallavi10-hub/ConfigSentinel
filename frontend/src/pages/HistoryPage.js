import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listServers, scanHistory } from "../api/servers";

export default function HistoryPage() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    (async () => {
      const servers = await listServers();
      if (servers[0]) {
        const history = await scanHistory(servers[0].id);
        setRows(history);
      }
    })();
  }, []);

  return (
    <div className="dashboard">
      <header className="topbar">
        <h1>🛡️ ConfigSentinel - Scan History</h1>
        <Link to="/" className="btn-secondary">Back to Dashboard</Link>
      </header>

      <table className="history-table">
        <thead>
          <tr>
            <th>Date/Time</th>
            <th>Compliance %</th>
            <th>Drift Count</th>
            <th>CPU %</th>
            <th>Memory %</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.scanned_at).toLocaleString()}</td>
              <td>{r.compliance_percent}%</td>
              <td>{r.drift_count}</td>
              <td>{r.cpu_percent ?? "N/A"}</td>
              <td>{r.memory_percent ?? "N/A"}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr><td colSpan={5}>No scans yet. Run a scan from the dashboard.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
