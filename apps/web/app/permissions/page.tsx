"use client";

import { AppShell } from "@/components/AppShell";
import { ApprovalModal } from "@/components/ApprovalModal";
import { api } from "@/lib/api";
import { ApprovalRequest } from "@/lib/types";
import { useEffect, useState } from "react";

export default function PermissionsPage() {
  const [policy, setPolicy] = useState<Record<string, string>>({});
  const [grants, setGrants] = useState<{ id: string; resource: string; scope: string; actions: string[]; kind: string }[]>([]);
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [active, setActive] = useState<ApprovalRequest | null>(null);

  async function load() {
    setPolicy(await api("/api/v1/permissions/policy"));
    setGrants(await api("/api/v1/permissions"));
    setRequests(await api("/api/v1/permissions/requests"));
  }
  useEffect(() => { load().catch(() => undefined); }, []);

  async function update(key: string, value: string) {
    const next = { ...policy, [key]: value };
    setPolicy(next);
    await api("/api/v1/permissions/policy", { method: "PUT", body: JSON.stringify(next) });
  }

  return (
    <AppShell>
      <h1 className="mb-2 text-3xl font-semibold">Permissions</h1>
      <p className="mb-6 text-sm text-[var(--fg-muted)]">ALLOW · ASK · BLOCK. High-risk actions always ask. Forbidden actions are blocked.</p>
      <section className="glass mb-6 space-y-3 rounded-3xl p-5">
        {Object.entries(policy).map(([key, value]) => (
          <label key={key} className="flex items-center justify-between text-sm">
            <span>{key.replaceAll("_", " ")}</span>
            <select className="rounded-full border border-[var(--line)] bg-transparent px-3 py-1" value={value} onChange={(e) => update(key, e.target.value)}>
              <option>ALLOW</option>
              <option>ASK</option>
              <option>BLOCK</option>
            </select>
          </label>
        ))}
      </section>
      <h2 className="mb-3 text-xl">Grants</h2>
      <div className="mb-8 space-y-2">
        {grants.map((g) => (
          <div key={g.id} className="glass flex items-center justify-between gap-3 rounded-2xl p-4 text-sm">
            <span>
              {g.kind} · {g.resource} · {g.scope} · {g.actions.join(", ")}
            </span>
            <button
              onClick={async () => {
                await api(`/api/v1/permissions/${g.id}/revoke`, { method: "POST" });
                await load();
              }}
              className="text-xs text-[var(--danger)]"
            >
              Revoke
            </button>
          </div>
        ))}
        {grants.length === 0 && <p className="text-sm text-[var(--fg-muted)]">No temporary or permanent grants yet.</p>}
      </div>
      <h2 className="mb-3 text-xl">Requests</h2>
      <div className="space-y-2">
        {requests.map((r) => (
          <button key={r.id} onClick={() => r.status === "pending" && setActive(r)} className="glass block w-full rounded-2xl p-4 text-left text-sm">
            {r.status} · {r.action} · {r.risk}
          </button>
        ))}
        {requests.length === 0 && <p className="text-sm text-[var(--fg-muted)]">No approval requests yet.</p>}
      </div>
      {active && <ApprovalModal request={active} onDone={() => { setActive(null); load(); }} />}
    </AppShell>
  );
}
