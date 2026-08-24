import { useState } from 'react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';
import { SeverityBadge } from '../components/Badges';
import { formatTime } from '../lib/format';
import type { Severity } from '../lib/types';

const CATEGORIES = ['ALL', 'SIMULATION', 'ANOMALY', 'SYSTEM', 'RISK'] as const;

export default function MissionLogsPage() {
  const { data: logs } = usePoll(() => api.missionLogs(300), { intervalMs: 2500 });
  const [filter, setFilter] = useState<(typeof CATEGORIES)[number]>('ALL');

  const filtered = (logs ?? []).filter((e) => filter === 'ALL' || e.category === filter);

  return (
    <div className="space-y-5 animate-fade-up">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold mb-1">Mission Logs</h1>
          <p className="text-sm text-[var(--color-text-dim)]">Chronological record of all mission events.</p>
        </div>
        <div className="flex gap-1.5">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setFilter(c)}
              className="px-3 py-1.5 rounded-full text-xs font-medium transition-colors"
              style={
                filter === c
                  ? { background: 'rgba(0,217,255,0.15)', color: '#00D9FF', border: '1px solid rgba(0,217,255,0.4)' }
                  : { background: 'rgba(255,255,255,0.03)', color: '#8892B0', border: '1px solid rgba(255,255,255,0.06)' }
              }
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <GlassCard className="!p-0 overflow-hidden">
        <div className="max-h-[70vh] overflow-y-auto divide-y divide-white/[0.05]">
          {filtered.map((event) => (
            <div key={event.id} className="flex items-start gap-4 px-4 py-3">
              <span className="mono text-[11px] text-[var(--color-text-faint)] shrink-0 pt-0.5 w-20">
                {formatTime(event.timestamp)}
              </span>
              <SeverityBadge severity={event.severity as Severity} />
              <span className="text-[10px] mono px-1.5 py-0.5 rounded bg-white/[0.04] text-[var(--color-text-faint)] shrink-0">
                {event.category}
              </span>
              <p className="text-sm text-[var(--color-text-primary)] flex-1">{event.message}</p>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="text-sm text-[var(--color-text-faint)] text-center py-10">No events recorded yet.</p>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
