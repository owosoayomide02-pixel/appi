"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { Task } from "@/lib/types";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function HistoryPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  useEffect(() => {
    api<Task[]>("/api/v1/tasks").then(setTasks).catch(() => undefined);
  }, []);
  return (
    <AppShell>
      <h1 className="mb-4 text-3xl font-semibold">History</h1>
      <div className="space-y-3">
        {tasks.map((task) => (
          <Link key={task.id} href={`/tasks/${task.id}`} className="glass block rounded-3xl p-5">
            <div className="text-xs text-[var(--fg-muted)]">{task.created_at} · {task.status}{task.verified ? " · verified" : ""}</div>
            <h2 className="mt-1 text-lg">{task.title || task.input_text}</h2>
            {task.result_summary && <p className="mt-2 text-sm text-[var(--fg-muted)]">{task.result_summary}</p>}
          </Link>
        ))}
        {tasks.length === 0 && (
          <div className="glass rounded-3xl p-8 text-[var(--fg-muted)]">
            No history yet. <Link href="/app" className="text-[var(--accent)]">Tell Appi what you need done</Link>.
          </div>
        )}
      </div>
    </AppShell>
  );
}
