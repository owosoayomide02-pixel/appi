"use client";

import { HeroCinematic } from "@/components/marketing/HeroCinematic";
import { OAuthButtons } from "@/components/OAuthButtons";
import { api } from "@/lib/api";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const intent = params.get("intent");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await api<{ access_token?: string }>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, display_name: displayName }),
      });
      if (user.access_token) {
        try {
          localStorage.setItem("appi_access_token", user.access_token);
        } catch {
          /* ignore */
        }
      }
      const ua = typeof navigator !== "undefined" ? navigator.userAgent.toLowerCase() : "";
      let os = "windows";
      if (ua.includes("mac") || ua.includes("iphone") || ua.includes("ipad")) os = "macos";
      else if (ua.includes("linux") || ua.includes("android")) os = "linux";
      const q = new URLSearchParams();
      q.set("os", os);
      if (intent) q.set("intent", intent);
      router.push(`/onboarding?${q.toString()}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not register");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <div className="relative hidden md:block">
        <HeroCinematic
          variant="panel"
          showCtas={false}
          title="Tell it what you need done."
          subtitle="Create an operator account. We detect Windows, macOS, or Linux and give you the right installer."
        />
      </div>
      <div className="flex items-center justify-center bg-[#0f172a] p-6">
        <form onSubmit={submit} className="glass w-full max-w-md rounded-[2rem] p-8">
          <div className="text-xs tracking-[0.28em] text-cyan-400/80">APPI</div>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-3xl text-white">
            Create your operator account
          </h1>
          {intent && (
            <p className="mt-3 rounded-2xl border border-cyan-500/20 p-3 text-sm text-slate-400">
              First task after setup: {intent}
            </p>
          )}
          <input
            className="mt-8 w-full rounded-2xl border border-cyan-500/20 bg-transparent px-4 py-3 text-white"
            placeholder="Name"
            autoComplete="name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
          <input
            className="mt-3 w-full rounded-2xl border border-cyan-500/20 bg-transparent px-4 py-3 text-white"
            placeholder="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="mt-3 w-full rounded-2xl border border-cyan-500/20 bg-transparent px-4 py-3 text-white"
            placeholder="Password (8+ characters)"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          {error && <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>}
          <button
            disabled={busy}
            className="mt-6 w-full rounded-full bg-[#00f2fe] py-3 font-medium text-[#0f172a] disabled:opacity-50"
          >
            {busy ? "Creating…" : "Continue"}
          </button>
          <OAuthButtons mode="register" />
          <p className="mt-4 text-sm text-slate-400">
            Already have an account?{" "}
            <Link href="/login" className="text-[#00f2fe]">
              Sign in
            </Link>
          </p>
          <p className="mt-2 text-sm text-slate-500">
            <Link href="/">Back to the website</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={<div className="flex min-h-screen items-center justify-center text-sm text-slate-400">Loading…</div>}
    >
      <RegisterForm />
    </Suspense>
  );
}
