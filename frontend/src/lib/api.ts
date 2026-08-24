import type {
  Spacecraft,
  TelemetryPoint,
  Anomaly,
  RiskAssessment,
  Prediction,
  MissionEvent,
  AIInsight,
  SimulationStatus,
  ScenarioType,
} from './types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API error ${res.status} on ${path}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; simulation_running: boolean; time: number }>('/api/health'),
  spacecraft: () => request<Spacecraft>('/api/spacecraft'),
  telemetry: (limit = 120) => request<TelemetryPoint[]>(`/api/telemetry?limit=${limit}`),
  telemetryCurrent: () => request<TelemetryPoint>('/api/telemetry/current'),
  anomalies: (includeResolved = true, limit = 100) =>
    request<Anomaly[]>(`/api/anomalies?include_resolved=${includeResolved}&limit=${limit}`),
  anomaly: (id: string) => request<Anomaly>(`/api/anomalies/${id}`),
  risk: () => request<RiskAssessment>('/api/risk'),
  predictions: () => request<Prediction[]>('/api/predictions'),
  aiInsights: () => request<AIInsight[]>('/api/ai-insights'),
  missionLogs: (limit = 200) => request<MissionEvent[]>(`/api/mission-logs?limit=${limit}`),
  simulationStatus: () => request<SimulationStatus>('/api/simulation/status'),
  startSimulation: () => request<SimulationStatus>('/api/simulation/start', { method: 'POST' }),
  stopSimulation: () => request<SimulationStatus>('/api/simulation/stop', { method: 'POST' }),
  setScenario: (scenario: ScenarioType) =>
    request<SimulationStatus>('/api/simulation/scenario', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    }),
};
