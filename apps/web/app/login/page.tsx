"use client";

import { api } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await api<{ onboarding_completed: boolean }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      router.push(user.onboarding_completed ? "/app" : "/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
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
          <h2 className="font-[family-name:var(--font-display)] text-4xl leading-tight">Think. Act. Verify.</h2>
          <p className="mt-4 max-w-sm text-sm text-[var(--fg-muted)]">
            Sign in to operate this device. Guardian still authorizes every action.
          </p>
        </div>
        <p className="text-xs text-[var(--fg-muted)]">MELIX STUDIOS</p>
      </div>
      <div className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="glass w-full max-w-md rounded-[2rem] p-8">
          <div className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">APPI</div>
          <h1 className="mt-2 text-3xl font-semibold">Welcome back</h1>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">Sign in to continue operating this device.</p>
          <input
            className="mt-8 w-full rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3"
            placeholder="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="mt-3 w-full rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3"
            placeholder="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>}
          <button disabled={busy} className="mt-6 w-full rounded-full bg-[var(--accent)] py-3 text-white disabled:opacity-50">
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <p className="mt-4 text-sm text-[var(--fg-muted)]">
            New here? <Link href="/register" className="text-[var(--accent)]">Create an account</Link>
          </p>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">
            <Link href="/">Back to the website</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
