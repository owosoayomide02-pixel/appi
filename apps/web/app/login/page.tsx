"use client";

import { HeroCinematic } from "@/components/marketing/HeroCinematic";
import { OAuthButtons } from "@/components/OAuthButtons";
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
      const user = await api<{ onboarding_completed: boolean; access_token?: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (user.access_token) {
        try {
          localStorage.setItem("appi_access_token", user.access_token);
        } catch {
          /* ignore */
        }
      }
      router.push(user.onboarding_completed ? "/app" : "/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
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
          title="Think. Act. Verify."
          subtitle="Sign in to operate this device. Guardian still authorizes every action."
        />
      </div>
      <div className="flex items-center justify-center bg-[#0f172a] p-6">
        <form onSubmit={submit} className="glass w-full max-w-md rounded-[2rem] p-8">
          <div className="text-xs tracking-[0.28em] text-cyan-400/80">APPI</div>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-3xl text-white">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-400">Sign in to continue operating this device.</p>
          <input
            className="mt-8 w-full rounded-2xl border border-cyan-500/20 bg-transparent px-4 py-3 text-white"
            placeholder="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="mt-3 w-full rounded-2xl border border-cyan-500/20 bg-transparent px-4 py-3 text-white"
            placeholder="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>}
          <button
            disabled={busy}
            className="mt-6 w-full rounded-full bg-[#00f2fe] py-3 font-medium text-[#0f172a] disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <OAuthButtons mode="login" />
          <p className="mt-4 text-sm text-slate-400">
            New here?{" "}
            <Link href="/register" className="text-[#00f2fe]">
              Create an account
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
