import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Security",
  description: "Guardian, kill switch, sandboxed files, secret handles, and audit.",
};

const rules = [
  {
    title: "Guardian: ALLOW / ASK / BLOCK",
    body: "Low-risk reads can proceed. Medium-risk work asks. High-risk work always asks. Forbidden actions — revealing secrets, bypassing Guardian, hidden work — are blocked even if the model requests them.",
  },
  {
    title: "Kill switch below the AI",
    body: "Stop Appi cancels the current task, stops browser automation, revokes temporary grants, and refuses new actions. The model does not get a vote.",
  },
  {
    title: "No full-drive access",
    body: "You choose approved folders. Paths are normalized against traversal. Windows, Program Files, and similar system locations stay out of reach.",
  },
  {
    title: "Secrets as handles",
    body: "The model sees secret://github/token/main, not the token. Logs, audit rows, API errors, and chat are redacted.",
  },
  {
    title: "Untrusted content stays untrusted",
    body: "Webpages, emails, and repository files cannot rewrite security policy. User instructions, model instructions, tool output, and external content are kept separate.",
  },
  {
    title: "Complete audit",
    body: "Every meaningful action records time, tool, target, risk, permission decision, result, and verification. You can read it on the Activity page.",
  },
];

export default function SecurityPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-4xl px-5 py-16">
        <p className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">SECURITY</p>
        <h1 className="font-[family-name:var(--font-display)] mt-4 text-4xl tracking-tight md:text-6xl">Power only with permission.</h1>
        <p className="mt-5 max-w-2xl text-lg text-[var(--fg-muted)]">
          Appi is designed to become capable without becoming reckless. Every tool is explicit, reviewable, and revocable.
        </p>
        <div className="mt-12 grid gap-4">
          {rules.map((rule) => (
            <article key={rule.title} className="glass rounded-[1.6rem] p-6">
              <h2 className="text-xl">{rule.title}</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--fg-muted)]">{rule.body}</p>
            </article>
          ))}
        </div>
        <p className="mt-10 text-sm text-[var(--fg-muted)]">
          Voice is an input method. It does not bypass Guardian.
        </p>
        <Link href="/register" className="mt-8 inline-flex rounded-full bg-[var(--accent)] px-5 py-3 text-sm text-white">
          Create an operator account
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}
