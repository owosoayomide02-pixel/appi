"use client";

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
      await api("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, display_name: displayName }),
      });
      router.push("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not register");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <div className="hidden flex-col justify-between border-r border-[var(--line)] p-10 md:flex">
        <Link href="/" className="font-[family-name:var(--font-display)] tracking-[0.2em]">
          APPI
        </Link>
        <div>
          <h2 className="font-[family-name:var(--font-display)] text-4xl leading-tight">Tell it what you need done.</h2>
          <p className="mt-4 max-w-sm text-sm text-[var(--fg-muted)]">
            Create an operator account, pair this Windows device, and choose the folders Appi may use.
          </p>
        </div>
        <p className="text-xs text-[var(--fg-muted)]">MELIX STUDIOS</p>
      </div>
      <div className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="glass w-full max-w-md rounded-[2rem] p-8">
          <div className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">APPI</div>
          <h1 className="mt-2 text-3xl font-semibold">Create your operator account</h1>
          {intent && (
            <p className="mt-3 rounded-2xl border border-[var(--line)] p-3 text-sm text-[var(--fg-muted)]">
              First task after setup: {intent}
            </p>
          )}
          <input
            className="mt-8 w-full rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3"
            placeholder="Name"
            autoComplete="name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
          <input
            className="mt-3 w-full rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3"
            placeholder="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="mt-3 w-full rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3"
            placeholder="Password (8+ characters)"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          {error && <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>}
          <button disabled={busy} className="mt-6 w-full rounded-full bg-[var(--accent)] py-3 text-white disabled:opacity-50">
            {busy ? "Creating…" : "Continue"}
          </button>
          <p className="mt-4 text-sm text-[var(--fg-muted)]">
            Already have an account? <Link href="/login" className="text-[var(--accent)]">Sign in</Link>
          </p>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">
            <Link href="/">Back to the website</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-sm text-[var(--fg-muted)]">Loading…</div>}>
      <RegisterForm />
    </Suspense>
  );
}
