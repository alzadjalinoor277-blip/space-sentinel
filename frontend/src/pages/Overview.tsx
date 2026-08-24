import { Gauge, AlertTriangle, Activity, Shield, BrainCircuit, TrendingUp } from 'lucide-react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard, KpiCard } from '../components/GlassCard';
import { RiskLevelBadge, SeverityBadge } from '../components/Badges';
import OrbitVisualization from '../components/OrbitVisualization';
import { formatDuration, formatRelativeTime, riskLevelColor } from '../lib/format';
import { Link } from 'react-router-dom';

export default function Overview() {
  const { data: spacecraft } = usePoll(() => api.spacecraft(), { intervalMs: 2000 });
  const { data: risk } = usePoll(() => api.risk(), { intervalMs: 2000 });
  const { data: anomalies } = usePoll(() => api.anomalies(false, 20), { intervalMs: 2000 });
  const { data: insights } = usePoll(() => api.aiInsights(), { intervalMs: 3000 });
  const { data: predictions } = usePoll(() => api.predictions(), { intervalMs: 3000 });
  const { data: logs } = usePoll(() => api.missionLogs(6), { intervalMs: 3000 });

  const activeAnomalies = anomalies ?? [];
  const nearThreshold = (predictions ?? []).filter((p) => p.time_to_threshold_minutes != null);
  const statusColor = spacecraft?.status === 'NOMINAL' ? '#39FFB6' : riskLevelColor((risk?.level ?? 'LOW') as any);

  return (
    <div className="space-y-5 animate-fade-up">
      {/* Hero mission status */}
      <GlassCard className="relative overflow-hidden">
        <div className="absolute inset-0 grid-overlay opacity-40 pointer-events-none" />
        <div className="relative grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-center">
          <div>
            <p className="text-[11px] uppercase tracking-widest text-[var(--color-text-dim)] font-semibold mb-2">
              Mission Overview
            </p>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-1">
              {spacecraft?.name ?? 'ORBIT-07'}
            </h1>
            <p className="text-sm text-[var(--color-text-dim)] mb-5">{spacecraft?.mission ?? 'SpaceSentinel Demonstration Mission'}</p>

            <div className="flex flex-wrap items-center gap-3 mb-6">
              <span
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-bold mono"
                style={{ color: statusColor, background: `${statusColor}1A`, border: `1px solid ${statusColor}40` }}
              >
                <span className="status-dot pulse" style={{ background: statusColor }} />
                {spacecraft?.status ?? 'CONNECTING'}
              </span>
              {risk && <RiskLevelBadge level={risk.level} />}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase tracking-wide mb-1">Orbit</p>
                <p className="mono font-semibold">{spacecraft?.orbit ?? '\u2014'}</p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase tracking-wide mb-1">Mission Time</p>
                <p className="mono font-semibold">{formatDuration(spacecraft?.mission_time_seconds ?? 0)}</p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase tracking-wide mb-1">Mission Risk</p>
                <p className="mono font-semibold" style={{ color: riskLevelColor((risk?.level ?? 'LOW') as any) }}>
                  {risk ? Math.round(risk.score) : 0} / 100
                </p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase tracking-wide mb-1">Active Anomalies</p>
                <p className="mono font-semibold">{activeAnomalies.length}</p>
              </div>
            </div>
          </div>

          <div className="h-56 lg:h-64">
            <OrbitVisualization statusColor={statusColor} />
          </div>
        </div>
      </GlassCard>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Mission Risk"
          value={risk ? Math.round(risk.score) : 0}
          unit="/100"
          icon={<Gauge size={18} />}
          accent={riskLevelColor((risk?.level ?? 'LOW') as any)}
          hint={risk?.level ?? 'LOW'}
        />
        <KpiCard
          label="Active Anomalies"
          value={activeAnomalies.length}
          icon={<AlertTriangle size={18} />}
          accent={activeAnomalies.length > 0 ? '#FFCC66' : '#39FFB6'}
          hint={activeAnomalies.length > 0 ? 'requires review' : 'all clear'}
        />
        <KpiCard
          label="Telemetry Health"
          value={activeAnomalies.length === 0 ? '100' : Math.max(0, 100 - activeAnomalies.length * 12)}
          unit="%"
          icon={<Activity size={18} />}
          accent="#00D9FF"
          hint="signal integrity"
        />
        <KpiCard
          label="Predicted Alerts"
          value={nearThreshold.length}
          icon={<TrendingUp size={18} />}
          accent="#6C63FF"
          hint="trending to threshold"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* AI Insights */}
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BrainCircuit size={17} className="text-[var(--color-ai-purple)]" />
              <h2 className="text-sm font-semibold">Recent AI Insights</h2>
            </div>
            <Link to="/ai-analysis" className="text-xs text-[var(--color-space-cyan)] hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {(insights ?? []).slice(0, 3).map((insight) => (
              <div key={insight.id} className="glass-panel-subtle p-3.5">
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-sm font-semibold">{insight.title}</p>
                  <span className="text-[11px] mono text-[var(--color-ai-purple)]">
                    {Math.round(insight.confidence * 100)}%
                  </span>
                </div>
                <p className="text-xs text-[var(--color-text-dim)] leading-relaxed line-clamp-2">
                  {insight.analysis}
                </p>
              </div>
            ))}
            {(insights ?? []).length === 0 && (
              <p className="text-xs text-[var(--color-text-faint)]">Awaiting telemetry analysis...</p>
            )}
          </div>
        </GlassCard>

        {/* Mission Activity */}
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Shield size={17} className="text-[var(--color-space-cyan)]" />
              <h2 className="text-sm font-semibold">Mission Activity</h2>
            </div>
            <Link to="/mission-logs" className="text-xs text-[var(--color-space-cyan)] hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-2.5">
            {(logs ?? []).map((event) => (
              <div key={event.id} className="flex items-start gap-3 text-xs">
                <SeverityBadge severity={event.severity} />
                <div className="flex-1 min-w-0">
                  <p className="text-[var(--color-text-primary)] truncate">{event.message}</p>
                </div>
                <span className="text-[var(--color-text-faint)] mono shrink-0">
                  {formatRelativeTime(event.timestamp)}
                </span>
              </div>
            ))}
            {(logs ?? []).length === 0 && (
              <p className="text-xs text-[var(--color-text-faint)]">No mission events yet.</p>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
