import { useState } from 'react';
import { X } from 'lucide-react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';
import { SeverityBadge, StatusPill } from '../components/Badges';
import { metricLabel, metricUnit, formatRelativeTime, formatTime, subsystemLabel } from '../lib/format';
import type { Anomaly } from '../lib/types';

export default function AnomaliesPage() {
  const { data: anomalies } = usePoll(() => api.anomalies(true, 100), { intervalMs: 2000 });
  const [selected, setSelected] = useState<Anomaly | null>(null);

  const list = anomalies ?? [];
  const activeCount = list.filter((a) => a.status === 'ACTIVE').length;

  return (
    <div className="space-y-5 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold mb-1">Anomaly Center</h1>
          <p className="text-sm text-[var(--color-text-dim)]">
            {activeCount} active &middot; {list.length} total detected
          </p>
        </div>
      </div>

      <GlassCard className="!p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-left text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">
                <th className="px-4 py-3 font-medium">Severity</th>
                <th className="px-4 py-3 font-medium">Subsystem</th>
                <th className="px-4 py-3 font-medium">Metric</th>
                <th className="px-4 py-3 font-medium">Detected</th>
                <th className="px-4 py-3 font-medium">Confidence</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {list.map((a) => (
                <tr
                  key={a.id}
                  onClick={() => setSelected(a)}
                  className="border-b border-white/[0.04] hover:bg-white/[0.03] cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3"><SeverityBadge severity={a.severity} /></td>
                  <td className="px-4 py-3">{subsystemLabel(a.subsystem)}</td>
                  <td className="px-4 py-3 mono text-xs">{metricLabel(a.metric)}</td>
                  <td className="px-4 py-3 text-xs text-[var(--color-text-dim)] mono">{formatRelativeTime(a.timestamp)}</td>
                  <td className="px-4 py-3 mono text-xs">{Math.round(a.confidence * 100)}%</td>
                  <td className="px-4 py-3"><StatusPill status={a.status} /></td>
                </tr>
              ))}
              {list.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-sm text-[var(--color-text-faint)]">
                    No anomalies detected. All subsystems nominal.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setSelected(null)}>
          <div className="glass-panel max-w-lg w-full p-6 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <SeverityBadge severity={selected.severity} />
                  <StatusPill status={selected.status} />
                </div>
                <h2 className="text-lg font-bold">{metricLabel(selected.metric)}</h2>
                <p className="text-xs text-[var(--color-text-dim)] mono">
                  {subsystemLabel(selected.subsystem)} subsystem &middot; {formatTime(selected.timestamp)}
                </p>
              </div>
              <button onClick={() => setSelected(null)} className="text-[var(--color-text-dim)] hover:text-white p-1">
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-5 text-sm">
              <div className="glass-panel-subtle p-3">
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Observed Value</p>
                <p className="mono font-bold text-[var(--color-critical)]">
                  {selected.observed_value.toFixed(2)} {metricUnit(selected.metric)}
                </p>
              </div>
              <div className="glass-panel-subtle p-3">
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Expected Range</p>
                <p className="mono font-bold">
                  {selected.expected_min.toFixed(1)}&ndash;{selected.expected_max.toFixed(1)} {metricUnit(selected.metric)}
                </p>
              </div>
              <div className="glass-panel-subtle p-3">
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Confidence</p>
                <p className="mono font-bold">{Math.round(selected.confidence * 100)}%</p>
              </div>
              <div className="glass-panel-subtle p-3">
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Detection Layer</p>
                <p className="mono font-bold text-xs">{selected.detection_layer.replace(/_/g, ' ')}</p>
              </div>
            </div>

            <div className="mb-5">
              <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1.5">Possible Cause / Analysis</p>
              <p className="text-sm leading-relaxed text-[var(--color-text-primary)]">{selected.explanation}</p>
            </div>

            <div>
              <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1.5">Recommended Action</p>
              <p className="text-sm leading-relaxed p-3 rounded-lg bg-[var(--color-ai-purple)]/10 border border-[var(--color-ai-purple)]/25">
                {selected.recommended_action}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
