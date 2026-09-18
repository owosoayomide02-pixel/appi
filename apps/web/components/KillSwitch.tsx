"use client";

import { api } from "@/lib/api";
import { useEffect, useState } from "react";

export function KillSwitch({ active, onChange }: { active: boolean; onChange?: (active: boolean) => void }) {
  const [busy, setBusy] = useState(false);

  async function toggle() {
    setBusy(true);
    try {
      if (active) {
        await api("/api/v1/kill-switch/resume", { method: "POST" });
        onChange?.(false);
      } else {
        await api("/api/v1/kill-switch/stop", { method: "POST" });
        onChange?.(true);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={toggle}
      disabled={busy}
      className={`rounded-full px-4 py-2 text-xs font-semibold tracking-[0.14em] uppercase border transition ${
        active
          ? "bg-[var(--danger)] text-white border-transparent"
          : "border-[var(--danger)] text-[var(--danger)] hover:bg-[var(--danger)] hover:text-white"
      }`}
    >
      {active ? "Resume Appi" : "Stop Appi"}
    </button>
  );
}

export function useKillSwitch(initial = false) {
  const [active, setActive] = useState(initial);
  useEffect(() => {
    api<{ active: boolean }>("/api/v1/kill-switch")
      .then((d) => setActive(d.active))
      .catch(() => undefined);
  }, []);
  return { active, setActive };
}
