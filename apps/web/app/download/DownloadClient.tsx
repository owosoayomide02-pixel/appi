"use client";

import { PlatformInstall } from "@/components/PlatformInstall";
import { HeroCinematic } from "@/components/marketing/HeroCinematic";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

export function DownloadClient() {
  const params = useSearchParams();
  const fromSignup = params.get("from") === "signup";
  const os = params.get("os");

  return (
    <div className="min-h-screen">
      <SiteHeader />
      <HeroCinematic
        title={fromSignup ? "Account ready. Install Appi." : "Install for your OS."}
        subtitle="We detect Windows (.exe), macOS, or Linux and serve the matching installer from your env. Pair once, then open the operator."
        primaryHref="/register"
        primaryLabel="Create account"
        secondaryHref="/onboarding"
        secondaryLabel="Onboarding"
      />
      <main className="mx-auto max-w-4xl px-5 py-16">
        <div className="mt-2">
          <PlatformInstall preferred={os} />
        </div>
        <ol className="mt-14 space-y-4">
          {[
            ["Create an account", "Register, then finish onboarding for folders and permissions."],
            ["Install for your OS", "Windows: Appi.exe zip. macOS/Linux: setup scripts from .env URLs."],
            ["Pair once", "Devices page → six-digit code → pair command for your platform."],
            ["Operate", "Dashboard at /app. On Windows: say Appi or Ctrl+Shift+A."],
          ].map(([title, body], i) => (
            <li key={title} className="border-b border-cyan-500/20 pb-5">
              <div className="font-mono text-xs text-slate-500">STEP {i + 1}</div>
              <h2 className="mt-2 text-xl text-white">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">{body}</p>
            </li>
          ))}
        </ol>
        <div className="mt-10 flex flex-wrap gap-3">
          <Link href="/register" className="rounded-full bg-[#00f2fe] px-5 py-3 text-sm font-medium text-[#0f172a]">
            Create account
          </Link>
          <Link href="/onboarding" className="rounded-full border border-cyan-400/40 px-5 py-3 text-sm text-cyan-100">
            Continue onboarding
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
