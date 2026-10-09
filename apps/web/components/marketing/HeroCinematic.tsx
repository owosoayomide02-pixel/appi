"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

type Props = {
  title: string;
  subtitle: string;
  primaryHref?: string;
  primaryLabel?: string;
  secondaryHref?: string;
  secondaryLabel?: string;
  brandFirst?: boolean;
  /** full = landing hero; panel = auth side column (fills parent height) */
  variant?: "full" | "panel";
  showCtas?: boolean;
};

type Particle = { a: number; r: number; s: number; size: number; z: number };

function useQuantumCore(canvasRef: React.RefObject<HTMLCanvasElement | null>) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let raf = 0;
    let t = 0;
    let w = 0;
    let h = 0;
    let dpr = 1;
    const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
    const particles: Particle[] = Array.from({ length: 90 }, () => ({
      a: Math.random() * Math.PI * 2,
      r: 0.35 + Math.random() * 0.9,
      s: 0.2 + Math.random() * 0.9,
      size: 0.6 + Math.random() * 1.8,
      z: 0.35 + Math.random() * 0.65,
    }));

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.tx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      pointer.ty = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    };

    const project = (x: number, y: number, z: number, cx: number, cy: number, scale: number) => {
      const depth = 1 / (1.35 + z);
      return {
        x: cx + x * scale * depth,
        y: cy + y * scale * depth * 0.92,
        d: depth,
      };
    };

    const drawRing = (
      cx: number,
      cy: number,
      rx: number,
      ry: number,
      rot: number,
      tilt: number,
      color: string,
      lw: number,
    ) => {
      ctx.beginPath();
      for (let i = 0; i <= 96; i++) {
        const a = (i / 96) * Math.PI * 2;
        const x = Math.cos(a) * rx;
        const y = Math.sin(a) * ry;
        const xr = x * Math.cos(rot) - y * Math.sin(rot);
        const yr = x * Math.sin(rot) + y * Math.cos(rot);
        const p = project(xr, yr * Math.cos(tilt), yr * Math.sin(tilt) * 0.35, cx, cy, 1);
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.closePath();
      ctx.strokeStyle = color;
      ctx.lineWidth = lw;
      ctx.stroke();
    };

    const draw = () => {
      t += reduced ? 0.006 : 0.016;
      const ease = 0.07;
      pointer.x += (pointer.tx - pointer.x) * ease;
      pointer.y += (pointer.ty - pointer.y) * ease;

      ctx.clearRect(0, 0, w, h);

      const cx = w * (0.5 + pointer.x * 0.035);
      const cy = h * (0.5 + pointer.y * 0.03);
      const base = Math.min(w, h);

      // atmospheric volume
      const haze = ctx.createRadialGradient(cx, cy, base * 0.04, cx, cy, base * 0.55);
      haze.addColorStop(0, "rgba(0, 242, 254, 0.28)");
      haze.addColorStop(0.25, "rgba(13, 148, 136, 0.14)");
      haze.addColorStop(0.55, "rgba(79, 70, 229, 0.16)");
      haze.addColorStop(1, "rgba(15, 23, 42, 0)");
      ctx.fillStyle = haze;
      ctx.fillRect(0, 0, w, h);

      // outer soft disc
      const outer = ctx.createRadialGradient(cx, cy, base * 0.02, cx, cy, base * 0.22);
      outer.addColorStop(0, "rgba(255,255,255,0.12)");
      outer.addColorStop(0.4, "rgba(0,242,254,0.08)");
      outer.addColorStop(1, "rgba(15,23,42,0)");
      ctx.fillStyle = outer;
      ctx.beginPath();
      ctx.arc(cx, cy, base * 0.22, 0, Math.PI * 2);
      ctx.fill();

      // orbital rings (layered perspective)
      const rings = [
        { rx: base * 0.2, ry: base * 0.072, rot: t * 0.55, tilt: 0.95, c: "rgba(0,242,254,0.55)", lw: 1.6 },
        { rx: base * 0.255, ry: base * 0.09, rot: -t * 0.38 + 0.8, tilt: 1.15, c: "rgba(45,212,191,0.35)", lw: 1.2 },
        { rx: base * 0.31, ry: base * 0.11, rot: t * 0.28 + 1.6, tilt: 0.75, c: "rgba(79,70,229,0.4)", lw: 1.4 },
        { rx: base * 0.36, ry: base * 0.13, rot: -t * 0.22 + 2.4, tilt: 1.35, c: "rgba(0,242,254,0.18)", lw: 1 },
      ];
      for (const ring of rings) {
        drawRing(cx, cy, ring.rx, ring.ry, ring.rot, ring.tilt, ring.c, ring.lw);
        // specular arc highlight
        ctx.save();
        ctx.globalCompositeOperation = "lighter";
        drawRing(
          cx,
          cy,
          ring.rx,
          ring.ry,
          ring.rot,
          ring.tilt,
          "rgba(255,255,255,0.08)",
          ring.lw * 0.5,
        );
        ctx.restore();
      }

      // meridian ribbons
      for (let i = 0; i < 3; i++) {
        const phase = t * (0.6 + i * 0.15) + i * 1.1;
        ctx.beginPath();
        for (let s = 0; s <= 64; s++) {
          const u = s / 64;
          const a = u * Math.PI * 2 + phase;
          const r = base * (0.12 + Math.sin(u * Math.PI * 3 + t + i) * 0.02);
          const x = Math.cos(a) * r;
          const y = Math.sin(a * 1.3) * r * 0.55;
          const px = cx + x * (1 + pointer.x * 0.05);
          const py = cy + y * (1 + pointer.y * 0.04);
          if (s === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.strokeStyle = `rgba(0, 242, 254, ${0.12 + i * 0.04})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      // particle field orbiting core
      for (const p of particles) {
        const a = p.a + t * p.s * 0.55;
        const orbit = base * 0.1 * p.r;
        const x = Math.cos(a) * orbit * (1.1 + Math.sin(t + p.a) * 0.08);
        const y = Math.sin(a) * orbit * 0.42;
        const z = Math.cos(a * 0.7 + p.z) * 0.5;
        const depth = 1 / (1.2 + z);
        const px = cx + x * depth + pointer.x * 8 * p.z;
        const py = cy + y * depth + pointer.y * 6 * p.z;
        const alpha = 0.15 + p.z * 0.55;
        ctx.beginPath();
        ctx.arc(px, py, p.size * depth * dpr * 0.7, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 242, 254, ${alpha})`;
        ctx.fill();
      }

      // crystalline core
      const coreR = base * (0.068 + Math.sin(t * 1.6) * 0.004);
      const core = ctx.createRadialGradient(
        cx - coreR * 0.35,
        cy - coreR * 0.4,
        coreR * 0.05,
        cx,
        cy,
        coreR,
      );
      core.addColorStop(0, "#ffffff");
      core.addColorStop(0.18, "#b8fdff");
      core.addColorStop(0.42, "#00f2fe");
      core.addColorStop(0.72, "#4f46e5");
      core.addColorStop(1, "#0b1224");
      ctx.beginPath();
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
      ctx.fillStyle = core;
      ctx.fill();

      // fresnel rim
      ctx.beginPath();
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255,255,255,0.55)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(cx, cy, coreR * 1.18, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(0,242,254,0.25)";
      ctx.lineWidth = 2;
      ctx.stroke();

      // inner pulse rings
      for (let i = 0; i < 3; i++) {
        const pulse = ((t * 0.7 + i * 0.33) % 1);
        ctx.beginPath();
        ctx.arc(cx, cy, coreR * (1.3 + pulse * 1.8), 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 254, ${(1 - pulse) * 0.22})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      // glass specular
      ctx.beginPath();
      ctx.ellipse(cx - coreR * 0.28, cy - coreR * 0.32, coreR * 0.28, coreR * 0.14, -0.6, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255,255,255,0.35)";
      ctx.fill();

      raf = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onMove, { passive: true });
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onMove);
    };
  }, [canvasRef]);
}

export function HeroCinematic({
  title,
  subtitle,
  primaryHref = "/register",
  primaryLabel = "Get started",
  secondaryHref = "/download",
  secondaryLabel = "Download",
  brandFirst = true,
  variant = "full",
  showCtas = true,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sectionRef = useRef<HTMLElement>(null);
  useQuantumCore(canvasRef);
  const panel = variant === "panel";

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const onMove = (e: PointerEvent) => {
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      el.style.setProperty("--hx", `${x * 18}px`);
      el.style.setProperty("--hy", `${y * 12}px`);
      el.style.setProperty("--htilt", `${x * 4}deg`);
    };
    el.addEventListener("pointermove", onMove, { passive: true });
    return () => el.removeEventListener("pointermove", onMove);
  }, []);

  return (
    <section
      ref={sectionRef}
      className={
        panel
          ? "hero-cinematic relative isolate h-full min-h-[100svh] overflow-hidden"
          : "hero-cinematic relative isolate min-h-[100svh] overflow-hidden"
      }
      style={{ ["--hx" as string]: "0px", ["--hy" as string]: "0px", ["--htilt" as string]: "0deg" }}
    >
      <video
        className="absolute inset-0 h-full w-full scale-110 object-cover opacity-40"
        autoPlay
        muted
        loop
        playsInline
        style={{
          animation: "appi-drift 22s ease-in-out infinite",
          transform: "translate3d(var(--hx), var(--hy), 0) scale(1.12)",
          transition: "transform 0.45s cubic-bezier(0.22, 1, 0.36, 1)",
        }}
      >
        <source
          src="https://videos.pexels.com/video-files/3129671/3129671-uhd_2560_1440_30fps.mp4"
          type="video/mp4"
        />
      </video>

      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_40%,rgba(15,23,42,0.15),rgba(15,23,42,0.78)_55%,#0f172a_100%)]" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#0f172a]/40 via-transparent to-[#0f172a]" />

      <div
        className="absolute inset-0 opacity-90"
        style={{
          transform: "translate3d(calc(var(--hx) * -0.4), calc(var(--hy) * -0.4), 0)",
          transition: "transform 0.5s cubic-bezier(0.22, 1, 0.36, 1)",
          animation: "appi-pulse 6s ease-in-out infinite",
        }}
      >
        <div className="absolute left-[18%] top-[28%] h-72 w-72 rounded-full bg-[#00f2fe]/18 blur-[100px]" />
        <div className="absolute right-[16%] top-[42%] h-80 w-80 rounded-full bg-[#4f46e5]/22 blur-[110px]" />
        <div className="absolute bottom-[18%] left-[40%] h-56 w-56 rounded-full bg-[#0d9488]/16 blur-[90px]" />
      </div>

      <canvas
        ref={canvasRef}
        className="absolute inset-0 h-full w-full"
        aria-hidden
        style={{
          transform: "perspective(900px) rotateY(var(--htilt)) translate3d(calc(var(--hx) * 0.25), calc(var(--hy) * 0.25), 0)",
          transition: "transform 0.4s cubic-bezier(0.22, 1, 0.36, 1)",
        }}
      />

      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#0f172a] to-transparent" />

      <div
        className={
          panel
            ? "relative z-10 flex h-full min-h-[100svh] flex-col justify-end p-10 pb-14"
            : "relative z-10 mx-auto flex min-h-[100svh] max-w-6xl flex-col justify-end px-5 pb-16 pt-28 md:pb-24"
        }
        style={{
          transform: "translate3d(calc(var(--hx) * 0.15), calc(var(--hy) * 0.12), 0)",
          transition: "transform 0.55s cubic-bezier(0.22, 1, 0.36, 1)",
        }}
      >
        {brandFirst && (
          <p
            className={`font-[family-name:var(--font-display)] tracking-[0.28em] text-[#00f2fe] drop-shadow-[0_0_28px_rgba(0,242,254,0.45)] ${
              panel ? "text-3xl" : "text-4xl md:text-6xl"
            }`}
          >
            APPI
          </p>
        )}
        <h1
          className={`font-[family-name:var(--font-display)] mt-4 max-w-3xl leading-[1.05] tracking-tight text-white ${
            panel ? "text-3xl" : "text-4xl md:text-6xl"
          }`}
        >
          {title}
        </h1>
        <p className={`mt-4 max-w-xl text-slate-300/95 ${panel ? "text-sm" : "text-base md:text-lg"}`}>{subtitle}</p>
        {showCtas && (
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href={primaryHref}
              className="cyan-glow magnetic-cta rounded-full bg-[#00f2fe] px-6 py-3 text-sm font-medium text-[#0f172a] transition-transform duration-300 hover:scale-[1.03]"
            >
              {primaryLabel}
            </Link>
            <Link
              href={secondaryHref}
              className="rounded-full border border-cyan-400/45 bg-white/5 px-6 py-3 text-sm text-cyan-50 backdrop-blur-md transition-colors duration-300 hover:border-cyan-300/70 hover:bg-white/10"
            >
              {secondaryLabel}
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}
