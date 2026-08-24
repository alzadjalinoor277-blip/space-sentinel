import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';
import TelemetryChart from '../components/TelemetryChart';
import type { TelemetryPoint } from '../lib/types';
import { metricLabel, metricUnit } from '../lib/format';

const CHARTS: { metric: keyof TelemetryPoint; color: string; min?: number; max?: number }[] = [
  { metric: 'temperature_c', color: '#FF5577', max: 85 },
  { metric: 'battery_percent', color: '#39FFB6', min: 20 },
  { metric: 'power_consumption_w', color: '#FFCC66', max: 900 },
  { metric: 'comm_signal_strength_pct', color: '#00D9FF', min: 35 },
  { metric: 'radiation_level_msv', color: '#6C63FF', max: 2.5 },
  { metric: 'cpu_load_pct', color: '#00D9FF', max: 95 },
  { metric: 'memory_usage_pct', color: '#6C63FF', max: 92 },
  { metric: 'fuel_percent', color: '#FFCC66', min: 5 },
];

export default function TelemetryPage() {
  const { data: telemetry } = usePoll(() => api.telemetry(150), { intervalMs: 2000 });
  const { data: current } = usePoll(() => api.telemetryCurrent(), { intervalMs: 2000 });

  return (
    <div className="space-y-5 animate-fade-up">
      <div>
        <h1 className="text-xl font-bold mb-1">Telemetry</h1>
        <p className="text-sm text-[var(--color-text-dim)]">
          Live spacecraft telemetry across all monitored subsystems, updated every 2 seconds.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {CHARTS.map(({ metric, color, min, max }) => {
          const value = current ? (current[metric] as number) : undefined;
          return (
            <GlassCard key={metric}>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold">{metricLabel(metric as string)}</h3>
                <span className="mono text-sm font-bold" style={{ color }}>
                  {value !== undefined ? value.toFixed(metric === 'radiation_level_msv' ? 3 : 1) : '\u2014'}
                  <span className="text-xs ml-1 text-[var(--color-text-dim)]">{metricUnit(metric as string)}</span>
                </span>
              </div>
              <TelemetryChart data={telemetry ?? []} metric={metric} color={color} min={min} max={max} />
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
