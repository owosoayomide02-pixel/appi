"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { useEffect, useState } from "react";

type Memory = { id: string; kind: string; topic: string; content: string; created_at: string };

export default function MemoryPage() {
  const [rows, setRows] = useState<Memory[]>([]);
  const [kind, setKind] = useState("preference");
  const [content, setContent] = useState("");
  const [topic, setTopic] = useState("");

  async function load() {
    setRows(await api("/api/v1/memory"));
  }
  useEffect(() => { load().catch(() => undefined); }, []);

  async function add() {
    await api("/api/v1/memory", { method: "POST", body: JSON.stringify({ kind, content, topic }) });
    setContent("");
    await load();
  }

  async function remove(id: string) {
    await api(`/api/v1/memory/${id}`, { method: "DELETE" });
    await load();
  }

  return (
    <AppShell>
      <h1 className="mb-2 text-3xl font-semibold">Memory</h1>
      <p className="mb-6 text-sm text-[var(--fg-muted)]">Working, project, preference, and secure handles. The model never receives the full memory database.</p>
      <div className="glass mb-6 grid gap-3 rounded-3xl p-5 md:grid-cols-4">
        <select className="rounded-2xl border border-[var(--line)] bg-transparent px-3 py-3" value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="preference">preference</option>
          <option value="project">project</option>
          <option value="working">working</option>
        </select>
        <input className="rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3" placeholder="Topic" value={topic} onChange={(e) => setTopic(e.target.value)} />
        <input className="rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3" placeholder="Preferred package manager: npm" value={content} onChange={(e) => setContent(e.target.value)} />
        <button onClick={add} className="rounded-full bg-[var(--accent)] px-5 py-3 text-white">Store</button>
      </div>
      <div className="space-y-3">
        {rows.map((row) => (
          <article key={row.id} className="glass flex items-start justify-between gap-4 rounded-3xl p-5">
            <div>
              <div className="text-xs uppercase tracking-wide text-[var(--fg-muted)]">{row.kind} · {row.topic}</div>
              <p className="mt-1 text-sm">{row.content}</p>
            </div>
            <button onClick={() => remove(row.id)} className="text-xs text-[var(--danger)]">
              Forget
            </button>
          </article>
        ))}
        {rows.length === 0 && <p className="text-sm text-[var(--fg-muted)]">No memories stored yet.</p>}
      </div>
    </AppShell>
  );
}
