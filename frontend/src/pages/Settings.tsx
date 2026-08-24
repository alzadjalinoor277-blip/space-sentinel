import { useState } from 'react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';

export default function SettingsPage() {
  const { data: health } = usePoll(() => api.health(), { intervalMs: 5000 });
  const [pollInterval, setPollInterval] = useState(2);

  return (
    <div className="space-y-5 animate-fade-up max-w-2xl">
      <div>
        <h1 className="text-xl font-bold mb-1">Settings</h1>
        <p className="text-sm text-[var(--color-text-dim)]">System configuration and connection status.</p>
      </div>

      <GlassCard>
        <h2 className="text-sm font-semibold mb-4">Backend Connection</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">API Status</p>
            <p className="mono font-semibold" style={{ color: health?.status === 'ok' ? '#39FFB6' : '#FF5577' }}>
              {health?.status === 'ok' ? 'CONNECTED' : 'DISCONNECTED'}
            </p>
          </div>
          <div>
            <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">Simulation Engine</p>
            <p className="mono font-semibold">{health?.simulation_running ? 'RUNNING' : 'IDLE'}</p>
          </div>
          <div>
            <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1">API Endpoint</p>
            <p className="mono text-xs text-[var(--color-text-dim)]">
              {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
            </p>
          </div>
        </div>
      </GlassCard>

      <GlassCard>
        <h2 className="text-sm font-semibold mb-4">Display Preferences</h2>
        <div>
          <label className="flex items-center justify-between text-sm mb-2">
            <span>Dashboard refresh interval</span>
            <span className="mono text-[var(--color-space-cyan)]">{pollInterval}s</span>
          </label>
          <input
            type="range"
            min={1}
            max={5}
            step={1}
            value={pollInterval}
            onChange={(e) => setPollInterval(Number(e.target.value))}
            className="w-full accent-[var(--color-space-cyan)]"
          />
          <p className="text-xs text-[var(--color-text-faint)] mt-2">
            Note: this is a display-only preview control in the MVP; live pages currently poll on fixed
            intervals tuned per data type.
          </p>
        </div>
      </GlassCard>

      <GlassCard>
        <h2 className="text-sm font-semibold mb-2">About SpaceSentinel</h2>
        <p className="text-xs text-[var(--color-text-dim)] leading-relaxed">
          SpaceSentinel is a simulated spacecraft health-monitoring and mission-safety platform built as a
          proof-of-concept prototype. It does not control real spacecraft. All telemetry is synthetically
          generated for demonstration purposes.
        </p>
      </GlassCard>
    </div>
  );
}
