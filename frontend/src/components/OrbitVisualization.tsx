import { useEffect, useState } from 'react';

export default function OrbitVisualization({ statusColor = '#39FFB6' }: { statusColor?: string }) {
  const [angle, setAngle] = useState(0);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;
    let raf: number;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = now - last;
      last = now;
      setAngle((a) => (a + dt * 0.00025) % (Math.PI * 2));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const cx = 200;
  const cy = 200;
  const rx = 150;
  const ry = 70;
  const x = cx + rx * Math.cos(angle);
  const y = cy + ry * Math.sin(angle);
  const inFront = Math.sin(angle) > 0;

  return (
    <svg viewBox="0 0 400 320" className="w-full h-full" role="img" aria-label="Spacecraft orbital position visualization">
      <defs>
        <radialGradient id="earthGlow" cx="50%" cy="45%" r="55%">
          <stop offset="0%" stopColor="#1a3a6e" />
          <stop offset="60%" stopColor="#0d1f42" />
          <stop offset="100%" stopColor="#050a18" />
        </radialGradient>
        <radialGradient id="earthAtmo" cx="50%" cy="45%" r="60%">
          <stop offset="85%" stopColor="rgba(0,217,255,0)" />
          <stop offset="100%" stopColor="rgba(0,217,255,0.35)" />
        </radialGradient>
      </defs>

      {/* orbit path (behind earth) */}
      <ellipse
        cx={cx} cy={cy} rx={rx} ry={ry}
        fill="none" stroke="rgba(108,99,255,0.25)" strokeWidth="1" strokeDasharray="3 5"
      />

      {!inFront && (
        <g>
          <circle cx={x} cy={y} r="4" fill={statusColor} />
          <circle cx={x} cy={y} r="8" fill={statusColor} opacity="0.25" />
        </g>
      )}

      {/* Earth */}
      <circle cx={cx} cy={cy + 30} r="62" fill="url(#earthGlow)" />
      <circle cx={cx} cy={cy + 30} r="66" fill="url(#earthAtmo)" />
      <circle cx={cx} cy={cy + 30} r="62" fill="none" stroke="rgba(0,217,255,0.2)" strokeWidth="1" />

      {inFront && (
        <g>
          <circle cx={x} cy={y} r="8" fill={statusColor} opacity="0.25" />
          <circle cx={x} cy={y} r="4" fill={statusColor} />
        </g>
      )}
    </svg>
  );
}
