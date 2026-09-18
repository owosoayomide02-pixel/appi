import { DashboardPreview } from "@/components/marketing/DashboardPreview";
import { HeroCommand } from "@/components/marketing/HeroCommand";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import Link from "next/link";

const pipeline = ["Understand", "Plan", "Authorize", "Act", "Verify", "Report"];

const capabilities = [
  {
    title: "Files, sandboxed",
    body: "Read and write only inside folders you approve. System paths and full-drive access are blocked.",
  },
  {
    title: "Terminal, structured",
    body: "Commands are executable + arguments + cwd + timeout — not a raw shell string from the model.",
  },
  {
    title: "Browser, with policy",
    body: "Playwright navigation, click, type, and screenshots. Unknown domains ask. CAPTCHA and MFA pause.",
  },
  {
    title: "Coding workspace",
    body: "Inspect a project, edit approved files, run tests, restart a local server, then show a before/after diff.",
  },
  {
    title: "Voice on Windows",
    body: "Say Appi, wait for the greeting, then speak. Ctrl+Shift+A if the wake word misses. Voice never bypasses Guardian.",
  },
  {
    title: "Honest connectors",
    body: "GitHub, Gmail, and Calendar connect only after a verified credential. Everything else stays Not connected.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main>
        <section className="mx-auto max-w-6xl px-5 pb-20 pt-16 text-center md:pt-24">
          <p className="text-xs tracking-[0.32em] text-[var(--fg-muted)]">MELIX STUDIOS · OPERATOR</p>
          <h1 className="font-[family-name:var(--font-display)] mx-auto mt-6 max-w-4xl text-5xl leading-[1.05] tracking-tight md:text-7xl">
            Tell it what you need done.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--fg-muted)]">
            Appi is a persistent AI operator. It plans the work, asks before sensitive actions, uses real tools on your machine, verifies the result, and keeps an audit trail. It is not a chatbot that pretends.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/register" className="rounded-full bg-[var(--accent)] px-6 py-3 text-sm text-white">
              Create an account
            </Link>
            <Link href="/download" className="rounded-full border border-[var(--line)] px-6 py-3 text-sm">
              Download for Windows
            </Link>
          </div>
          <HeroCommand />
          <p className="mt-4 text-xs text-[var(--fg-muted)]">Think. Act. Verify. Unsupported abilities return CAPABILITY_UNAVAILABLE — not a fake success.</p>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-20">
          <DashboardPreview />
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-20">
          <div className="grid gap-3 md:grid-cols-6">
            {pipeline.map((step, i) => (
              <div key={step} className="glass rounded-3xl p-5">
                <div className="font-mono text-xs text-[var(--fg-muted)]">{String(i + 1).padStart(2, "0")}</div>
                <div className="mt-2 text-lg">{step}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-20">
          <h2 className="font-[family-name:var(--font-display)] text-3xl tracking-tight md:text-4xl">What Appi actually does</h2>
          <p className="mt-3 max-w-2xl text-[var(--fg-muted)]">
            Every action goes through a registered tool, then Guardian, then verification. The model cannot skip the permission engine.
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-2">
            {capabilities.map((item) => (
              <article key={item.title} className="glass rounded-[1.6rem] p-6">
                <h3 className="text-xl">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[var(--fg-muted)]">{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-24">
          <div className="glass rounded-[2rem] p-8 md:flex md:items-center md:justify-between md:p-12">
            <div className="max-w-xl">
              <h2 className="font-[family-name:var(--font-display)] text-3xl tracking-tight">Guardian sits below the model</h2>
              <p className="mt-3 text-sm leading-6 text-[var(--fg-muted)]">
                ALLOW, ASK, or BLOCK. A visible Stop Appi kill switch cancels work without asking the AI. Folders are opt-in. Secrets reach the model as handles, never as raw keys.
              </p>
            </div>
            <div className="mt-6 flex flex-wrap gap-3 md:mt-0">
              <Link href="/security" className="rounded-full border border-[var(--line)] px-5 py-3 text-sm">
                Read the security model
              </Link>
              <Link href="/app" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm text-white">
                Open the operator
              </Link>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
