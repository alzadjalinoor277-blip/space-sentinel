import { Thermometer, BatteryMedium, Radio as RadioIcon, Radiation, Cpu, Fuel, Navigation } from 'lucide-react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';
import OrbitVisualization from '../components/OrbitVisualization';
import { formatDuration, riskLevelColor } from '../lib/format';

const SUBSYSTEMS = [
  { key: 'thermal', label: 'Thermal', icon: Thermometer },
  { key: 'power', label: 'Power', icon: BatteryMedium },
  { key: 'communication', label: 'Communication', icon: RadioIcon },
  { key: 'radiation', label: 'Radiation', icon: Radiation },
  { key: 'navigation', label: 'Navigation', icon: Navigation },
  { key: 'propulsion', label: 'Propulsion', icon: Fuel },
] as const;

export default function SpacecraftPage() {
  const { data: spacecraft } = usePoll(() => api.spacecraft(), { intervalMs: 2000 });
  const { data: telemetry } = usePoll(() => api.telemetryCurrent(), { intervalMs: 2000 });
  const { data: risk } = usePoll(() => api.risk(), { intervalMs: 2000 });

  const statusColor = spacecraft?.status === 'NOMINAL' ? '#39FFB6' : riskLevelColor((risk?.level ?? 'LOW') as any);

  return (
    <div className="space-y-5 animate-fade-up">
      <GlassCard>
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6 items-center">
          <div>
            <p className="text-[11px] uppercase tracking-widest text-[var(--color-text-dim)] font-semibold mb-2">
              Spacecraft Identification
            </p>
            <h1 className="text-2xl font-bold mb-4">{spacecraft?.name ?? '\u2014'}</h1>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Spacecraft ID</dt>
                <dd className="mono font-semibold">{spacecraft?.id ?? '\u2014'}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Mission</dt>
                <dd className="font-medium">{spacecraft?.mission ?? '\u2014'}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Orbit</dt>
                <dd className="mono font-semibold">{spacecraft?.orbit ?? '\u2014'}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Mission Elapsed Time</dt>
                <dd className="mono font-semibold">{formatDuration(spacecraft?.mission_time_seconds ?? 0)}</dd>
              </div>
            </dl>
          </div>
          <div className="h-52">
            <OrbitVisualization statusColor={statusColor} />
          </div>
        </div>
      </GlassCard>

      <div>
        <h2 className="text-sm font-semibold text-[var(--color-text-dim)] mb-3 uppercase tracking-wide">
          Subsystem Health
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {SUBSYSTEMS.map(({ key, label, icon: Icon }) => {
            const value = risk?.breakdown[key] ?? 0;
            const health = Math.max(0, 100 - value);
            const color = health > 80 ? '#39FFB6' : health > 55 ? '#00D9FF' : health > 30 ? '#FFCC66' : '#FF5577';
            return (
              <GlassCard key={key} subtle>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Icon size={16} style={{ color }} />
                    <span className="text-sm font-medium">{label}</span>
                  </div>
                  <span className="mono text-sm font-bold" style={{ color }}>
                    {Math.round(health)}%
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${health}%`, background: color }}
                  />
                </div>
              </GlassCard>
            );
          })}
        </div>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-[var(--color-text-dim)] mb-3 uppercase tracking-wide">
          Live Telemetry Snapshot
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {telemetry && (
            <>
              <Snapshot label="Temperature" value={telemetry.temperature_c.toFixed(1)} unit="\u00b0C" icon={<Thermometer size={15} />} />
              <Snapshot label="Battery" value={telemetry.battery_percent.toFixed(0)} unit="%" icon={<BatteryMedium size={15} />} />
              <Snapshot label="Power Draw" value={telemetry.power_consumption_w.toFixed(0)} unit="W" icon={<Cpu size={15} />} />
              <Snapshot label="Comm Signal" value={telemetry.comm_signal_strength_pct.toFixed(0)} unit="%" icon={<RadioIcon size={15} />} />
              <Snapshot label="Radiation" value={telemetry.radiation_level_msv.toFixed(2)} unit="mSv" icon={<Radiation size={15} />} />
              <Snapshot label="Fuel" value={telemetry.fuel_percent.toFixed(0)} unit="%" icon={<Fuel size={15} />} />
              <Snapshot label="Altitude" value={telemetry.altitude_km.toFixed(0)} unit="km" icon={<Navigation size={15} />} />
              <Snapshot label="CPU Load" value={telemetry.cpu_load_pct.toFixed(0)} unit="%" icon={<Cpu size={15} />} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Snapshot({ label, value, unit, icon }: { label: string; value: string; unit: string; icon: React.ReactNode }) {
  return (
    <GlassCard subtle className="text-center">
      <div className="flex items-center justify-center gap-1.5 text-[var(--color-text-faint)] mb-2">
        {icon}
        <span className="text-[11px] uppercase tracking-wide">{label}</span>
      </div>
      <p className="mono text-xl font-bold">
        {value}
        <span className="text-xs ml-1 text-[var(--color-text-dim)]">{unit}</span>
      </p>
    </GlassCard>
  );
}
