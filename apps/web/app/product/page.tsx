import { HeroCinematic } from "@/components/marketing/HeroCinematic";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Product",
  description: "How Appi plans, authorizes, acts, and verifies on your device.",
};

export default function ProductPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <HeroCinematic
        title="An action layer, not a chat window."
        subtitle="Describe a goal. Appi plans, waits on risk, uses real tools, then verifies before it claims success."
        primaryHref="/register"
        primaryLabel="Create account"
        secondaryHref="/download"
        secondaryLabel="Install"
      />
      <main className="mx-auto max-w-4xl px-5 py-16">
        <div className="grid gap-8 md:grid-cols-2">
          {[
            ["Operator UI", "Tasks, devices, permissions, audit. Stop Appi always visible."],
            ["Cloud brain", "FastAPI + Guardian. Heuristic planner if no AI key."],
            ["Device runtime", "Windows-first background assistant with honest capabilities."],
            ["Voice", "Wake word Appi or Ctrl+Shift+A. Quantum Core reacts to speech."],
          ].map(([t, b]) => (
            <article key={t} className="border-b border-cyan-500/20 pb-5">
              <h2 className="text-xl text-white">{t}</h2>
              <p className="mt-2 text-sm text-slate-400">{b}</p>
            </article>
          ))}
        </div>
        <Link href="/app" className="mt-10 inline-block text-cyan-300 hover:underline">
          Open operator
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}
