import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Product",
  description: "How Appi plans, authorizes, acts, and verifies on your device.",
};

const layers = [
  {
    title: "Operator UI",
    body: "A Next.js dashboard for tasks, projects, memory, devices, connections, permissions, and the activity log. Stop Appi is always visible.",
  },
  {
    title: "Cloud brain",
    body: "FastAPI plans the work, classifies risk, talks to the model provider you configure, and records audit events. Without an API key it uses a heuristic planner — still gated by Guardian.",
  },
  {
    title: "Device runtime",
    body: "A Windows background assistant that stays running when the window closes. Pair once with a six-digit code. Heartbeats and capabilities are reported honestly.",
  },
  {
    title: "Voice",
    body: "Wake word Appi, or Ctrl+Shift+A. The greeting is not a bypass. Spoken commands become the same tasks you would type.",
  },
];

export default function ProductPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-4xl px-5 py-16">
        <p className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">PRODUCT</p>
        <h1 className="font-[family-name:var(--font-display)] mt-4 text-4xl tracking-tight md:text-6xl">An action layer, not a chat window.</h1>
        <p className="mt-5 max-w-2xl text-lg text-[var(--fg-muted)]">
          You describe a goal. Appi produces an executable plan, waits when the risk requires it, uses tools that actually exist on the paired device, then refuses to mark the task complete until verification passes.
        </p>

        <ol className="mt-14 space-y-6">
          {layers.map((layer, i) => (
            <li key={layer.title} className="glass rounded-[1.6rem] p-6">
              <div className="font-mono text-xs text-[var(--fg-muted)]">{String(i + 1).padStart(2, "0")}</div>
              <h2 className="mt-2 text-2xl">{layer.title}</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--fg-muted)]">{layer.body}</p>
            </li>
          ))}
        </ol>

        <section className="mt-14">
          <h2 className="text-2xl">What stays out of V0.1</h2>
          <p className="mt-3 text-sm leading-6 text-[var(--fg-muted)]">
            Payments, banking, calls, SMS, social posting, account creation on third-party sites, CAPTCHA/MFA bypass, and unrestricted desktop control are not implemented. If a capability is missing, Appi says so.
          </p>
        </section>

        <div className="mt-12 flex flex-wrap gap-3">
          <Link href="/download" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm text-white">
            Install on Windows
          </Link>
          <Link href="/security" className="rounded-full border border-[var(--line)] px-5 py-3 text-sm">
            Security
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
