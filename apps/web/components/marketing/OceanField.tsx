"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

/**
 * Full-page liquid field: cursor wakes ripples through cyan/teal currents.
 * Fixed behind content; pointer-events none; respects reduced motion.
 * Disabled on /app operator routes for clarity.
 */
export function OceanField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pathname = usePathname();
  const enabled = !pathname?.startsWith("/app");

  useEffect(() => {
    if (!enabled) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let raf = 0;
    let w = 0;
    let h = 0;
    let dpr = 1;
    let t = 0;
    const pointer = { x: 0.5, y: 0.4, tx: 0.5, ty: 0.4, active: false };
    const ripples: { x: number; y: number; life: number; max: number }[] = [];

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const onMove = (e: PointerEvent) => {
      pointer.tx = e.clientX / w;
      pointer.ty = e.clientY / h;
      pointer.active = true;
      if (ripples.length < 18) {
        ripples.push({ x: e.clientX, y: e.clientY, life: 0, max: 1.8 + Math.random() * 0.6 });
      }
    };
    const onLeave = () => {
      pointer.active = false;
    };

    const drawWaveMesh = () => {
      const cols = Math.max(18, Math.floor(w / 72));
      const rows = Math.max(12, Math.floor(h / 72));
      const cellW = w / cols;
      const cellH = h / rows;
      const px = pointer.x * w;
      const py = pointer.y * h;

      for (let row = 0; row <= rows; row++) {
        ctx.beginPath();
        for (let col = 0; col <= cols; col++) {
          const x0 = col * cellW;
          const y0 = row * cellH;
          const dx = x0 - px;
          const dy = y0 - py;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const pull = Math.exp(-dist / 280) * (pointer.active ? 28 : 10);
          const angle = Math.atan2(dy, dx) + t * 0.4;
          const swell =
            Math.sin(x0 * 0.008 + t * 1.1 + row * 0.35) * 7 +
            Math.cos(y0 * 0.01 - t * 0.85 + col * 0.2) * 5;
          const x = x0 + Math.cos(angle) * pull + swell;
          const y = y0 + Math.sin(angle) * pull * 0.55 + swell * 0.4;
          if (col === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        const alpha = 0.035 + (row / rows) * 0.04;
        ctx.strokeStyle = `rgba(0, 242, 254, ${alpha})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      for (let col = 0; col <= cols; col += 2) {
        ctx.beginPath();
        for (let row = 0; row <= rows; row++) {
          const x0 = col * cellW;
          const y0 = row * cellH;
          const dx = x0 - px;
          const dy = y0 - py;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const pull = Math.exp(-dist / 280) * (pointer.active ? 22 : 8);
          const angle = Math.atan2(dy, dx) - t * 0.3;
          const swell = Math.sin(y0 * 0.009 + t + col * 0.25) * 6;
          const x = x0 + Math.cos(angle) * pull + swell * 0.3;
          const y = y0 + Math.sin(angle) * pull * 0.5 + swell;
          if (row === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = "rgba(13, 148, 136, 0.05)";
        ctx.stroke();
      }
    };

    const drawRipples = () => {
      for (let i = ripples.length - 1; i >= 0; i--) {
        const r = ripples[i];
        r.life += 0.016;
        const p = r.life / r.max;
        if (p >= 1) {
          ripples.splice(i, 1);
          continue;
        }
        const radius = 20 + p * 160;
        const alpha = (1 - p) * 0.28;
        ctx.beginPath();
        ctx.arc(r.x, r.y, radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 254, ${alpha})`;
        ctx.lineWidth = 1.5 * (1 - p);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(r.x, r.y, radius * 0.55, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(79, 70, 229, ${alpha * 0.7})`;
        ctx.stroke();
      }
    };

    const drawCaustic = () => {
      const px = pointer.x * w;
      const py = pointer.y * h;
      const g = ctx.createRadialGradient(px, py, 0, px, py, 420);
      g.addColorStop(0, "rgba(0, 242, 254, 0.14)");
      g.addColorStop(0.35, "rgba(13, 148, 136, 0.07)");
      g.addColorStop(0.7, "rgba(79, 70, 229, 0.05)");
      g.addColorStop(1, "rgba(15, 23, 42, 0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);

      const bx = w * (0.7 + Math.sin(t * 0.25) * 0.08);
      const by = h * (0.25 + Math.cos(t * 0.2) * 0.06);
      const g2 = ctx.createRadialGradient(bx, by, 0, bx, by, 380);
      g2.addColorStop(0, "rgba(79, 70, 229, 0.1)");
      g2.addColorStop(1, "rgba(15, 23, 42, 0)");
      ctx.fillStyle = g2;
      ctx.fillRect(0, 0, w, h);
    };

    const tick = () => {
      t += reduced ? 0.004 : 0.016;
      const ease = reduced ? 0.04 : 0.08;
      pointer.x += (pointer.tx - pointer.x) * ease;
      pointer.y += (pointer.ty - pointer.y) * ease;

      ctx.clearRect(0, 0, w, h);
      drawCaustic();
      drawWaveMesh();
      if (!reduced) drawRipples();
      raf = requestAnimationFrame(tick);
    };

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
    };
  }, [enabled]);

  if (!enabled) return null;

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 z-[1] h-full w-full"
    />
  );
}
