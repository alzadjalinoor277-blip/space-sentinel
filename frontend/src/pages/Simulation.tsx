import { Play, Square, Thermometer, BatteryWarning, RadioIcon as RadioIconType, Zap } from 'lucide-react';
import { Radio, Waves } from 'lucide-react';
import { useState } from 'react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';
import OrbitVisualization from '../components/OrbitVisualization';
import { RiskLevelBadge, SeverityBadge } from '../components/Badges';
import { formatRelativeTime, riskLevelColor, scenarioLabel } from '../lib/format';
import type { ScenarioType } from '../lib/types';

const SCENARIOS: { id: ScenarioType; label: string; description: string; icon: any }[] = [
  { id: 'NORMAL', label: 'Normal Mission', description: 'Nominal operations, all systems stable.', icon: Waves },
  { id: 'THERMAL_EVENT', label: 'Thermal Event', description: 'Temperature and power rise gradually.', icon: Thermometer },
  { id: 'POWER_INSTABILITY', label: 'Power Instability', description: 'Battery voltage and level behave erratically.', icon: BatteryWarning },
  { id: 'COMMUNICATION_DEGRADATION', label: 'Communication Degradation', description: 'Signal strength decays over time.', icon: RadioIconType },
  { id: 'MULTI_SUBSYSTEM_ANOMALY', label: 'Multi-Subsystem Anomaly', description: 'Correlated failure across several subsystems.', icon: Zap },
];

export default function SimulationPage() {
  const { data: status, refetch: refetchStatus } = usePoll(() => api.simulationStatus(), { intervalMs: 1500 });
  const { data: risk } = usePoll(() => api.risk(), { intervalMs: 1500 });
  const { data: anomalies } = usePoll(() => api.anomalies(false, 10), { intervalMs: 1500 });
  const { data: logs } = usePoll(() => api.missionLogs(15), { intervalMs: 2000 });
  const [busy, setBusy] = useState(false);

  const statusColor = riskLevelColor((risk?.level ?? 'LOW') as any);

  async function handleStart() {
    setBusy(true);
    try { await api.startSimulation(); await refetchStatus(); } finally { setBusy(false); }
  }
  async function handleStop() {
    setBusy(true);
    try { await api.stopSimulation(); await refetchStatus(); } finally { setBusy(false); }
  }
  async function handleScenario(id: ScenarioType) {
    setBusy(true);
    try { await api.setScenario(id); await refetchStatus(); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-5 animate-fade-up">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold mb-1">Simulation</h1>
          <p className="text-sm text-[var(--color-text-dim)]">
            Drive the full detection pipeline live: trigger a scenario and watch telemetry, anomalies,
            risk, AI analysis, and predictions react in real time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!status?.running ? (
            <button
              onClick={handleStart}
              disabled={busy}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-[var(--color-success)]/15 text-[var(--color-success)] border border-[var(--color-success)]/40 hover:bg-[var(--color-success)]/25 transition-colors disabled:opacity-50"
            >
              <Play size={15} /> Start Simulation
            </button>
          ) : (
            <button
              onClick={handleStop}
              disabled={busy}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-[var(--color-critical)]/15 text-[var(--color-critical)] border border-[var(--color-critical)]/40 hover:bg-[var(--color-critical)]/25 transition-colors disabled:opacity-50"
            >
              <Square size={15} /> Stop Simulation
            </button>
          )}
        </div>
      </div>

      <GlassCard className="relative overflow-hidden">
        <div className="absolute inset-0 grid-overlay opacity-30 pointer-events-none" />
        <div className="relative grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6 items-center">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <span className="status-dot pulse" style={{ background: status?.running ? statusColor : '#545E7A' }} />
              <span className="mono text-sm font-semibold" style={{ color: status?.running ? statusColor : '#545E7A' }}>
                {status?.running ? 'SIMULATION RUNNING' : 'SIMULATION STOPPED'}
              </span>
              <span className="text-xs text-[var(--color-text-dim)]">
                &middot; Scenario: {scenarioLabel(status?.scenario ?? 'NORMAL')}
              </span>
            </div>
            <div className="flex items-center gap-4">
              {risk && <RiskLevelBadge level={risk.level} />}
              <span className="text-sm text-[var(--color-text-dim)]">
                {(anomalies ?? []).length} active anomaly signal(s)
              </span>
            </div>
          </div>
          <div className="h-40">
            <OrbitVisualization statusColor={status?.running ? statusColor : '#545E7A'} />
          </div>
        </div>
      </GlassCard>

      <div>
        <h2 className="text-sm font-semibold text-[var(--color-text-dim)] mb-3 uppercase tracking-wide">
          Scenario Selector
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {SCENARIOS.map(({ id, label, description, icon: Icon }) => {
            const active = status?.scenario === id;
            return (
              <button
                key={id}
                onClick={() => handleScenario(id)}
                disabled={busy}
                className="text-left glass-panel p-4 transition-all hover:border-[var(--color-space-cyan)]/40 disabled:opacity-50"
                style={active ? { borderColor: 'rgba(0,217,255,0.5)', boxShadow: '0 0 0 1px rgba(0,217,255,0.3)' } : undefined}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon size={16} className={active ? 'text-[var(--color-space-cyan)]' : 'text-[var(--color-text-dim)]'} />
                  <span className="text-sm font-semibold">{label}</span>
                  {active && <Radio size={11} className="text-[var(--color-space-cyan)] ml-auto" />}
                </div>
                <p className="text-xs text-[var(--color-text-dim)] leading-relaxed">{description}</p>
              </button>
            );
          })}
        </div>
      </div>

      <GlassCard>
        <h2 className="text-sm font-semibold mb-3">Event Timeline</h2>
        <div className="space-y-2.5 max-h-72 overflow-y-auto">
          {(logs ?? []).map((event) => (
            <div key={event.id} className="flex items-start gap-3 text-xs">
              <SeverityBadge severity={event.severity} />
              <p className="flex-1 text-[var(--color-text-primary)]">{event.message}</p>
              <span className="text-[var(--color-text-faint)] mono shrink-0">{formatRelativeTime(event.timestamp)}</span>
            </div>
          ))}
          {(logs ?? []).length === 0 && (
            <p className="text-xs text-[var(--color-text-faint)]">No events yet. Start the simulation to begin.</p>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
