"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { Task } from "@/lib/types";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  useEffect(() => {
    api<Task[]>("/api/v1/tasks?active=true").then(setTasks).catch(() => undefined);
  }, []);
  return (
    <AppShell>
      <h1 className="mb-4 text-3xl font-semibold">Active tasks</h1>
      <div className="space-y-3">
        {tasks.map((task) => (
          <Link key={task.id} href={`/tasks/${task.id}`} className="glass block rounded-3xl p-5">
            <div className="text-sm text-[var(--fg-muted)]">{task.status}</div>
            <div className="text-lg">{task.title || task.input_text}</div>
          </Link>
        ))}
        {tasks.length === 0 && (
          <div className="glass rounded-3xl p-8 text-[var(--fg-muted)]">
            No running tasks. <Link href="/app" className="text-[var(--accent)]">Start one</Link>.
          </div>
        )}
      </div>
    </AppShell>
  );
}
