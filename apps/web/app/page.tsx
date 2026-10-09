import { HeroCinematic } from "@/components/marketing/HeroCinematic";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main>
        <HeroCinematic
          title="Tell it what you need done."
          subtitle="A persistent AI operator that plans, asks before risk, acts on your machine, and verifies — never a chatbot that pretends."
          primaryHref="/register"
          primaryLabel="Create account"
          secondaryHref="/download"
          secondaryLabel="Install runtime"
        />
        <section className="mx-auto max-w-6xl px-5 py-20">
          <h2 className="font-[family-name:var(--font-display)] text-3xl tracking-tight text-cyan-100">
            Understand → Plan → Act → Verify
          </h2>
          <p className="mt-3 max-w-2xl text-slate-400">
            Guardian gates every step. Unsupported work returns CAPABILITY_UNAVAILABLE.
          </p>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {[
              ["Voice + Quantum Core", "Say Appi. Cyan rings listen, think, and speak with Windows recognition."],
              ["Real tools only", "Files, terminal, browser, and apps — sandboxed to approved folders."],
              ["OS-aware install", "Signup detects Windows, macOS, or Linux and serves installers from .env."],
            ].map(([t, b]) => (
              <article key={t} className="border-b border-cyan-500/20 pb-6">
                <h3 className="text-xl text-white">{t}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{b}</p>
              </article>
            ))}
          </div>
          <div className="mt-12 flex flex-wrap gap-4">
            <Link href="/product" className="text-sm text-cyan-300 hover:underline">Product</Link>
            <Link href="/security" className="text-sm text-cyan-300 hover:underline">Security</Link>
            <Link href="/app" className="text-sm text-cyan-300 hover:underline">Operator</Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
