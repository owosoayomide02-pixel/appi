"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { Device } from "@/lib/types";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function DeviceDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [device, setDevice] = useState<Device | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api<Device>(`/api/v1/devices/${params.id}`)
      .then((data) => {
        if (!cancelled) setDevice(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Not found");
      });
    return () => {
      cancelled = true;
    };
  }, [params.id]);

  async function revoke() {
    await api(`/api/v1/devices/${params.id}/revoke`, { method: "POST" });
    router.push("/device");
  }

  if (!device) {
    return (
      <AppShell>
        <p className="text-sm text-[var(--fg-muted)]">{error || "Loading…"}</p>
      </AppShell>
    );
  }

  const caps = device.capabilities || {};
  const supported = Object.entries(caps).filter(([, v]) => v);
  const missing = Object.entries(caps).filter(([, v]) => !v);

  return (
    <AppShell>
      <h1 className="text-3xl font-semibold">{device.name}</h1>
      <p className="mt-1 text-sm text-[var(--fg-muted)]">
        {device.platform} · {device.status} · runtime {device.runtime_version}
      </p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <section className="glass rounded-3xl p-5">
          <h2 className="text-sm uppercase tracking-wide text-[var(--fg-muted)]">Supported capabilities</h2>
          <ul className="mt-3 space-y-1 text-sm">
            {supported.map(([k]) => (
              <li key={k}>{k} ✅</li>
            ))}
            {supported.length === 0 && <li>None reported</li>}
          </ul>
        </section>
        <section className="glass rounded-3xl p-5">
          <h2 className="text-sm uppercase tracking-wide text-[var(--fg-muted)]">Unavailable on this runtime</h2>
          <ul className="mt-3 max-h-64 space-y-1 overflow-auto text-sm text-[var(--fg-muted)]">
            {missing.slice(0, 24).map(([k]) => (
              <li key={k}>{k} — CAPABILITY_UNAVAILABLE</li>
            ))}
          </ul>
        </section>
        <section className="glass rounded-3xl p-5">
          <h2 className="text-sm uppercase tracking-wide text-[var(--fg-muted)]">Granted permissions</h2>
          <ul className="mt-3 space-y-1 text-sm">
            {(device.granted_permissions || []).filter((g) => g.kind === "permanent").map((g) => (
              <li key={g.id}>{g.kind} · {g.resource} · {g.scope}</li>
            ))}
            {(device.granted_permissions || []).filter((g) => g.kind === "permanent").length === 0 && <li>None</li>}
          </ul>
        </section>
        <section className="glass rounded-3xl p-5">
          <h2 className="text-sm uppercase tracking-wide text-[var(--fg-muted)]">Temporary permissions</h2>
          <ul className="mt-3 space-y-1 text-sm">
            {(device.temporary_permissions || []).map((g) => (
              <li key={g.id}>{g.kind} · {g.resource} · {g.scope}{g.expires_at ? ` · until ${g.expires_at}` : ""}</li>
            ))}
            {(device.temporary_permissions || []).length === 0 && <li>None</li>}
          </ul>
        </section>
        <section className="glass rounded-3xl p-5">
          <h2 className="text-sm uppercase tracking-wide text-[var(--fg-muted)]">Connection</h2>
          <p className="mt-3 text-sm">Last heartbeat: {device.last_heartbeat_at || "never"}</p>
          <p className="text-sm">Last activity: {device.last_seen_at || "never"}</p>
          <button onClick={revoke} className="mt-4 rounded-full border border-[var(--danger)] px-4 py-2 text-sm text-[var(--danger)]">
            Revoke device
          </button>
        </section>
      </div>
    </AppShell>
  );
}
