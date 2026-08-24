import type { Severity, AnomalyStatus, RiskLevel } from '../lib/types';
import { severityColor, riskLevelColor } from '../lib/format';

export function SeverityBadge({ severity }: { severity: Severity }) {
  const color = severityColor(severity);
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide mono"
      style={{
        color,
        background: `${color}1A`,
        border: `1px solid ${color}40`,
      }}
    >
      <span className="status-dot" style={{ background: color }} />
      {severity}
    </span>
  );
}

export function RiskLevelBadge({ level }: { level: RiskLevel }) {
  const color = riskLevelColor(level);
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold tracking-wider mono"
      style={{ color, background: `${color}1A`, border: `1px solid ${color}40` }}
    >
      {level}
    </span>
  );
}

export function StatusPill({ status }: { status: AnomalyStatus }) {
  const map: Record<AnomalyStatus, string> = {
    ACTIVE: '#FF5577',
    INVESTIGATING: '#FFCC66',
    RESOLVED: '#39FFB6',
  };
  const color = map[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold mono"
      style={{ color, background: `${color}1A`, border: `1px solid ${color}40` }}
    >
      {status === 'ACTIVE' && <span className="status-dot pulse" style={{ background: color }} />}
      {status}
    </span>
  );
}
