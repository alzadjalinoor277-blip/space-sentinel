import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { formatDuration } from '../lib/format';
import { riskLevelColor } from '../lib/format';

export default function Topbar() {
  const { data: spacecraft } = usePoll(() => api.spacecraft(), { intervalMs: 2000 });
  const { data: risk } = usePoll(() => api.risk(), { intervalMs: 2000 });

  const statusColor =
    spacecraft?.status === 'NOMINAL' ? 'var(--color-success)' : riskLevelColor((risk?.level ?? 'LOW') as any);

  return (
    <header className="flex items-center justify-between px-6 py-3.5 border-b border-white/[0.06] bg-[var(--color-bg-primary)]/60 backdrop-blur-xl sticky top-0 z-20">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="status-dot pulse" style={{ background: statusColor }} />
          <span className="text-sm font-semibold mono" style={{ color: statusColor }}>
            {spacecraft?.status ?? 'CONNECTING'}
          </span>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-[var(--color-text-dim)]">
          <span className="mono">{spacecraft?.name ?? '\u2014'}</span>
          <span className="text-[var(--color-text-faint)]">&middot;</span>
          <span>{spacecraft?.orbit ?? '\u2014'}</span>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <div className="hidden md:flex items-center gap-2 text-xs text-[var(--color-text-dim)]">
          <span>MISSION TIME</span>
          <span className="mono text-[var(--color-text-primary)]">
            {formatDuration(spacecraft?.mission_time_seconds ?? 0)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[var(--color-text-dim)]">RISK</span>
          <span className="mono font-bold" style={{ color: riskLevelColor((risk?.level ?? 'LOW') as any) }}>
            {risk ? Math.round(risk.score) : 0}/100
          </span>
        </div>
      </div>
    </header>
  );
}
