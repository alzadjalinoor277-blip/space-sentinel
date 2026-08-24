import type { RiskLevel, Severity, Subsystem } from './types';

export function severityColor(sev: Severity): string {
  switch (sev) {
    case 'CRITICAL': return '#FF5577';
    case 'WARNING': return '#FFCC66';
    case 'INFO': return '#00D9FF';
    default: return '#39FFB6';
  }
}

export function riskLevelColor(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL': return '#FF5577';
    case 'HIGH': return '#FFCC66';
    case 'MODERATE': return '#00D9FF';
    default: return '#39FFB6';
  }
}

export function subsystemLabel(s: Subsystem): string {
  return s.charAt(0) + s.slice(1).toLowerCase();
}

export function metricLabel(metric: string): string {
  const map: Record<string, string> = {
    temperature_c: 'Temperature',
    battery_voltage_v: 'Battery Voltage',
    battery_percent: 'Battery Level',
    power_consumption_w: 'Power Consumption',
    radiation_level_msv: 'Radiation Level',
    comm_signal_strength_pct: 'Comm Signal Strength',
    cpu_load_pct: 'CPU Load',
    memory_usage_pct: 'Memory Usage',
    fuel_percent: 'Fuel Level',
    altitude_km: 'Altitude',
    velocity_kms: 'Velocity',
  };
  return map[metric] ?? metric;
}

export function metricUnit(metric: string): string {
  const map: Record<string, string> = {
    temperature_c: '\u00b0C',
    battery_voltage_v: 'V',
    battery_percent: '%',
    power_consumption_w: 'W',
    radiation_level_msv: 'mSv',
    comm_signal_strength_pct: '%',
    cpu_load_pct: '%',
    memory_usage_pct: '%',
    fuel_percent: '%',
    altitude_km: 'km',
    velocity_kms: 'km/s',
  };
  return map[metric] ?? '';
}

export function formatValue(value: number, decimals = 1): string {
  return value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString(undefined, {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

export function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() / 1000 - timestamp;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export function scenarioLabel(scenario: string): string {
  return scenario
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}
