"use client";

import { Step } from "@/lib/types";

const STATUS_COLOR: Record<string, string> = {
  pending: "text-[var(--fg-muted)]",
  running: "text-[var(--accent)]",
  waiting_for_approval: "text-[var(--warn)]",
  verifying: "text-[var(--accent)]",
  succeeded: "text-[var(--ok)]",
  failed: "text-[var(--danger)]",
  blocked: "text-[var(--danger)]",
  cancelled: "text-[var(--fg-muted)]",
};

export function TaskPlan({ goal, steps }: { goal: string; steps: Step[] }) {
  return (
    <section className="glass rounded-3xl p-6">
      <div className="text-xs tracking-[0.2em] text-[var(--fg-muted)]">GOAL</div>
      <h2 className="mt-1 text-xl font-medium">{goal || "Planning…"}</h2>
      <ol className="mt-6 space-y-3">
        {steps.map((step, index) => (
          <li key={step.id} className="flex gap-4 rounded-2xl border border-[var(--line)] px-4 py-3">
            <div className="font-mono text-xs text-[var(--fg-muted)]">{String(index + 1).padStart(2, "0")}</div>
            <div className="min-w-0 flex-1">
              <div className="text-sm">{step.description}</div>
              <div className="mt-1 font-mono text-[11px] text-[var(--fg-muted)]">
                {step.tool} · {step.risk}
              </div>
              {step.error && <div className="mt-1 text-xs text-[var(--danger)]">{step.error}</div>}
            </div>
            <div className={`text-xs uppercase tracking-wide ${STATUS_COLOR[step.status] || ""}`}>{step.status.replaceAll("_", " ")}</div>
          </li>
        ))}
      </ol>
    </section>
  );
}
