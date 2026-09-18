"use client";

import { KillSwitch } from "@/components/KillSwitch";
import { NotificationBell } from "@/components/NotificationBell";
import { Sidebar } from "@/components/Sidebar";
import { api } from "@/lib/api";
import { User } from "@/lib/types";
import { Menu, Moon, Sun, X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [kill, setKill] = useState(false);
  const [dark, setDark] = useState(true);
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

  useEffect(() => {
    const stored = localStorage.getItem("appi-theme") || "dark";
    const isDark = stored === "dark";
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
    api<User>("/api/v1/auth/me")
      .then((me) => {
        setUser(me);
        setKill(me.kill_switch_active);
        if (!me.onboarding_completed) router.replace("/onboarding");
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("appi-theme", next ? "dark" : "light");
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[var(--fg-muted)]">
        Loading APPI…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen gap-4 p-4">
      <div className="hidden md:flex">
        <Sidebar />
      </div>
      {navOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <button className="absolute inset-0 bg-black/50" aria-label="Close menu" onClick={() => setNavOpen(false)} />
          <div className="relative z-50 m-4">
            <Sidebar />
          </div>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col gap-4">
        <header className="glass flex items-center justify-between rounded-3xl px-4 py-4 md:px-6">
          <div className="flex items-center gap-3">
            <button className="rounded-full border border-[var(--line)] p-2 md:hidden" onClick={() => setNavOpen((v) => !v)} aria-label="Open menu">
              {navOpen ? <X size={16} /> : <Menu size={16} />}
            </button>
            <div>
              <div className="text-xs tracking-[0.22em] text-[var(--fg-muted)]">TELL IT WHAT YOU NEED DONE</div>
              <div className="text-sm text-[var(--fg-muted)]">Signed in as {user.display_name}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={toggleTheme} className="rounded-full border border-[var(--line)] p-2" aria-label="Toggle theme">
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <NotificationBell />
            <KillSwitch active={kill} onChange={setKill} />
          </div>
        </header>
        {kill && (
          <div className="rounded-2xl border border-[var(--danger)] bg-[var(--danger)]/10 px-4 py-3 text-sm">
            Kill switch is active. Appi will not start new actions until you resume.
          </div>
        )}
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
