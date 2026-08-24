import type { ReactNode } from 'react';
import clsx from 'clsx';

export function GlassCard({
  children,
  className,
  subtle = false,
}: {
  children: ReactNode;
  className?: string;
  subtle?: boolean;
}) {
  return (
    <div className={clsx(subtle ? 'glass-panel-subtle' : 'glass-panel', 'p-5', className)}>
      {children}
    </div>
  );
}

export function KpiCard({
  label,
  value,
  unit,
  icon,
  accent = 'var(--color-space-cyan)',
  hint,
}: {
  label: string;
  value: string | number;
  unit?: string;
  icon?: ReactNode;
  accent?: string;
  hint?: string;
}) {
  return (
    <GlassCard className="relative overflow-hidden">
      <div
        className="absolute -top-8 -right-8 w-24 h-24 rounded-full blur-2xl opacity-20"
        style={{ background: accent }}
      />
      <div className="flex items-start justify-between relative">
        <div>
          <p className="text-[11px] uppercase tracking-wider text-[var(--color-text-dim)] font-semibold">
            {label}
          </p>
          <p className="mt-2 text-3xl font-bold mono" style={{ color: accent }}>
            {value}
            {unit && <span className="text-base ml-1 font-medium text-[var(--color-text-dim)]">{unit}</span>}
          </p>
          {hint && <p className="mt-1.5 text-xs text-[var(--color-text-faint)]">{hint}</p>}
        </div>
        {icon && (
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `${accent}1A`, color: accent }}
          >
            {icon}
          </div>
        )}
      </div>
    </GlassCard>
  );
}
