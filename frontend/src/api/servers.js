import api from "./client";

export const listServers = () => api.get("/api/servers").then((r) => r.data);
export const createServer = (payload) => api.post("/api/servers", payload).then((r) => r.data);

export const runScan = (serverId) => api.post(`/api/scans/${serverId}/run`).then((r) => r.data);
export const scanHistory = (serverId) => api.get(`/api/scans/${serverId}/history`).then((r) => r.data);
export const latestScan = (serverId) => api.get(`/api/scans/${serverId}/latest`).then((r) => r.data);

export const analyzeIncident = (incidentId) =>
  api.post(`/api/ai/analyze/${incidentId}`).then((r) => r.data);
export const getAnalysis = (incidentId) =>
  api.get(`/api/ai/analysis/${incidentId}`).then((r) => r.data);

export const remediateIncident = (incidentId, confirm) =>
  api.post("/api/remediation", { incident_id: incidentId, confirm }).then((r) => r.data);

export const dashboardSummary = (serverId) =>
  api.get(`/api/dashboard/${serverId}`).then((r) => r.data);

export const demoScenarios = () => api.get("/api/demo/scenarios").then((r) => r.data);
export const breakConfig = (scenario) =>
  api.post("/api/demo/break-config", { scenario }).then((r) => r.data);
export const resetDemo = () => api.post("/api/demo/reset").then((r) => r.data);
