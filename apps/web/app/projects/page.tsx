"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { useEffect, useState } from "react";

type Project = { id: string; name: string; root_path: string; framework?: string | null; language?: string | null };

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setProjects(await api("/api/v1/projects"));
  }
  useEffect(() => { load().catch(() => undefined); }, []);

  async function create() {
    setError("");
    try {
      await api("/api/v1/projects", { method: "POST", body: JSON.stringify({ name, root_path: path }) });
      setName("");
      setPath("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add project");
    }
  }

  return (
    <AppShell>
      <h1 className="mb-2 text-3xl font-semibold">Projects</h1>
      <p className="mb-6 text-sm text-[var(--fg-muted)]">Coding agent workspace. Paths must sit inside an approved folder.</p>
      <div className="glass mb-6 flex flex-col gap-3 rounded-3xl p-5 md:flex-row">
        <input className="flex-1 rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3" placeholder="Nestora" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="flex-[2] rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3" placeholder="C:\Users\User\Projects\Nestora" value={path} onChange={(e) => setPath(e.target.value)} />
        <button onClick={create} className="rounded-full bg-[var(--accent)] px-5 py-3 text-white">Add</button>
      </div>
      {error && <p className="mb-4 text-sm text-[var(--danger)]">{error}</p>}
      <div className="space-y-3">
        {projects.map((p) => (
          <article key={p.id} className="glass rounded-3xl p-5">
            <div className="text-lg">{p.name}</div>
            <div className="font-mono text-xs text-[var(--fg-muted)]">{p.root_path}</div>
            <div className="mt-2 text-sm text-[var(--fg-muted)]">{p.framework || "Unindexed"} · {p.language || "—"}</div>
          </article>
        ))}
        {projects.length === 0 && (
          <p className="text-sm text-[var(--fg-muted)]">No projects yet. Add one inside an approved folder.</p>
        )}
      </div>
    </AppShell>
  );
}
