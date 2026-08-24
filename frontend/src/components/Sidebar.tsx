import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Satellite,
  Activity,
  AlertTriangle,
  BrainCircuit,
  TrendingUp,
  PlayCircle,
  ScrollText,
  Settings as SettingsIcon,
  Radio,
} from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/spacecraft', label: 'Spacecraft', icon: Satellite },
  { to: '/telemetry', label: 'Telemetry', icon: Activity },
  { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle },
  { to: '/ai-analysis', label: 'AI Analysis', icon: BrainCircuit },
  { to: '/predictions', label: 'Predictions', icon: TrendingUp },
  { to: '/simulation', label: 'Simulation', icon: PlayCircle },
  { to: '/mission-logs', label: 'Mission Logs', icon: ScrollText },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex md:w-60 shrink-0 flex-col border-r border-white/[0.06] bg-[var(--color-bg-secondary)]/40 backdrop-blur-xl">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, #6C63FF, #00D9FF)' }}
        >
          <Radio size={17} className="text-[#05070D]" strokeWidth={2.5} />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-bold tracking-tight">SpaceSentinel</p>
          <p className="text-[10px] text-[var(--color-text-faint)] mono">MISSION CONTROL</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[var(--color-ai-purple)]/15 text-[var(--color-text-primary)] border border-[var(--color-ai-purple)]/30'
                  : 'text-[var(--color-text-dim)] hover:text-[var(--color-text-primary)] hover:bg-white/[0.04] border border-transparent'
              )
            }
          >
            <Icon size={17} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 text-[10px] text-[var(--color-text-faint)] border-t border-white/[0.06] mono">
        SIMULATION &middot; PROOF OF CONCEPT
      </div>
    </aside>
  );
}
