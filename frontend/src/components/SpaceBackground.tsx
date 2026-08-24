import { useEffect, useRef } from 'react';

interface Star {
  x: number;
  y: number;
  r: number;
  baseAlpha: number;
  twinkleSpeed: number;
  phase: number;
}

export default function SpaceBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let stars: Star[] = [];
    let width = 0;
    let height = 0;
    let raf = 0;

    function resize() {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas!.width = width;
      canvas!.height = height;
      const count = Math.floor((width * height) / 9000);
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        r: Math.random() * 1.1 + 0.2,
        baseAlpha: Math.random() * 0.5 + 0.15,
        twinkleSpeed: Math.random() * 0.015 + 0.003,
        phase: Math.random() * Math.PI * 2,
      }));
    }

    function draw(t: number) {
      ctx!.clearRect(0, 0, width, height);

      // soft nebula glows
      const g1 = ctx!.createRadialGradient(width * 0.15, height * 0.1, 0, width * 0.15, height * 0.1, width * 0.5);
      g1.addColorStop(0, 'rgba(108, 99, 255, 0.05)');
      g1.addColorStop(1, 'rgba(108, 99, 255, 0)');
      ctx!.fillStyle = g1;
      ctx!.fillRect(0, 0, width, height);

      const g2 = ctx!.createRadialGradient(width * 0.9, height * 0.75, 0, width * 0.9, height * 0.75, width * 0.4);
      g2.addColorStop(0, 'rgba(0, 217, 255, 0.04)');
      g2.addColorStop(1, 'rgba(0, 217, 255, 0)');
      ctx!.fillStyle = g2;
      ctx!.fillRect(0, 0, width, height);

      for (const s of stars) {
        const twinkle = prefersReducedMotion ? 0 : Math.sin(t * s.twinkleSpeed + s.phase) * 0.35;
        const alpha = Math.max(0, Math.min(1, s.baseAlpha + twinkle));
        ctx!.beginPath();
        ctx!.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(232, 236, 247, ${alpha})`;
        ctx!.fill();
      }

      if (!prefersReducedMotion) {
        raf = requestAnimationFrame(draw);
      }
    }

    resize();
    window.addEventListener('resize', resize);
    raf = requestAnimationFrame(draw);
    if (prefersReducedMotion) draw(0);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 -z-10 pointer-events-none"
      style={{ background: 'var(--color-bg-primary)' }}
    />
  );
}
