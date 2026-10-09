"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { Device } from "@/lib/types";
import Link from "next/link";
import { useEffect, useState } from "react";

const HIGHLIGHT = ["filesystem", "terminal", "browser", "desktop_ui", "contacts", "calendar", "camera", "phone_calls"];

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [code, setCode] = useState("");
  const [kill, setKill] = useState(false);

  async function load() {
    setDevices(await api("/api/v1/devices"));
    setKill((await api<{ active: boolean }>("/api/v1/kill-switch")).active);
  }
  useEffect(() => {
    load().catch(() => undefined);
    const timer = window.setInterval(() => load().catch(() => undefined), 8000);
    return () => window.clearInterval(timer);
  }, []);

  async function pair() {
    const data = await api<{ pairing_code: string }>("/api/v1/devices/pair/start", { method: "POST" });
    setCode(data.pairing_code);
  }

  return (
    <AppShell>
      <h1 className="mb-2 text-3xl font-semibold">Appi devices</h1>
      <p className="mb-6 text-sm text-[var(--fg-muted)]">
        Each runtime reports only capabilities it actually implements. Kill switch {kill ? "is on" : "is off"}.
      </p>
      <button onClick={pair} className="mb-6 rounded-full border border-[var(--line)] px-4 py-2 text-sm">
        Generate pairing code
      </button>
      {code && (
        <pre className="glass mb-6 rounded-3xl p-5 font-mono text-sm">
          python -m app.main pair --code {code}
          {"\n"}python -m app.main run
        </pre>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        {devices.map((d) => {
          const groups = d.capability_groups || {};
          return (
            <Link key={d.id} href={`/device/${d.id}`} className="glass rounded-3xl p-6">
              <div className="text-xl">{d.name}</div>
              <div className="text-sm text-[var(--fg-muted)]">
                {d.os || d.platform} · {d.status}
                {d.last_heartbeat_at ? ` · heartbeat ${d.last_heartbeat_at.slice(11, 19)}` : ""}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                {HIGHLIGHT.map((key) => (
                  <div key={key}>
                    {key.replaceAll("_", " ")} {groups[key] ? "✅" : groups[key] === false ? "❌" : "Not configured"}
                  </div>
                ))}
              </div>
            </Link>
          );
        })}
        {devices.length === 0 && <p className="text-sm text-[var(--fg-muted)]">No devices paired yet.</p>}
      </div>
    </AppShell>
  );
}
