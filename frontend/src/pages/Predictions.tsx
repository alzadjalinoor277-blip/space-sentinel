import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';
import TelemetryChart from '../components/TelemetryChart';
import { metricLabel, metricUnit, subsystemLabel } from '../lib/format';
import type { TelemetryPoint } from '../lib/types';

const TREND_ICON = { increasing: TrendingUp, decreasing: TrendingDown, stable: Minus };

export default function PredictionsPage() {
  const { data: predictions } = usePoll(() => api.predictions(), { intervalMs: 3000 });
  const { data: telemetry } = usePoll(() => api.telemetry(150), { intervalMs: 2000 });

  const sorted = [...(predictions ?? [])].sort((a, b) => {
    const at = a.time_to_threshold_minutes ?? Infinity;
    const bt = b.time_to_threshold_minutes ?? Infinity;
    return at - bt;
  });

  return (
    <div className="space-y-5 animate-fade-up">
      <div>
        <h1 className="text-xl font-bold mb-1">Predictive Monitoring</h1>
        <p className="text-sm text-[var(--color-text-dim)]">
          Trend projections from recent telemetry. This is a statistical simulation estimate, not
          flight-grade predictive certainty.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {sorted.map((p) => {
          const Icon = TREND_ICON[p.trend];
          const urgent = p.time_to_threshold_minutes != null && p.time_to_threshold_minutes < 15;
          const color = urgent ? '#FF5577' : p.trend === 'stable' ? '#39FFB6' : '#FFCC66';
          return (
            <GlassCard key={p.metric}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Icon size={16} style={{ color }} />
                  <h3 className="text-sm font-semibold">{metricLabel(p.metric)}</h3>
                  <span className="text-[10px] mono px-1.5 py-0.5 rounded bg-white/[0.05] text-[var(--color-text-faint)]">
                    {subsystemLabel(p.subsystem)}
                  </span>
                </div>
                <span className="mono text-sm font-bold" style={{ color }}>
                  {p.current_value.toFixed(1)} {metricUnit(p.metric)}
                </span>
              </div>

              <TelemetryChart
                data={telemetry ?? []}
                metric={p.metric as keyof TelemetryPoint}
                color={color}
                max={p.trend !== 'decreasing' ? p.threshold : undefined}
                min={p.trend === 'decreasing' ? p.threshold : undefined}
                height={160}
              />

              <div className="mt-3 pt-3 border-t border-white/[0.06] grid grid-cols-3 gap-3 text-xs">
                <div>
                  <p className="text-[10px] text-[var(--color-text-faint)] uppercase mb-0.5">Threshold</p>
                  <p className="mono font-semibold">{p.threshold.toFixed(1)} {metricUnit(p.metric)}</p>
                </div>
                <div>
                  <p className="text-[10px] text-[var(--color-text-faint)] uppercase mb-0.5">Confidence</p>
                  <p className="mono font-semibold">{Math.round(p.confidence * 100)}%</p>
                </div>
                <div>
                  <p className="text-[10px] text-[var(--color-text-faint)] uppercase mb-0.5">Time to Threshold</p>
                  <p className="mono font-semibold" style={{ color: urgent ? '#FF5577' : undefined }}>
                    {p.time_to_threshold_minutes != null ? `${p.time_to_threshold_minutes.toFixed(0)}m` : '\u2014'}
                  </p>
                </div>
              </div>
              <p className="mt-3 text-xs text-[var(--color-text-dim)] leading-relaxed">{p.insight}</p>
            </GlassCard>
          );
        })}
        {sorted.length === 0 && (
          <GlassCard className="lg:col-span-2">
            <p className="text-sm text-[var(--color-text-faint)] text-center py-8">
              Gathering telemetry history for trend analysis...
            </p>
          </GlassCard>
        )}
      </div>
    </div>
  );
}
