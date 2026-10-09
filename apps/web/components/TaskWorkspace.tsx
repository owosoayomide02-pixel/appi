"use client";

import { ApprovalModal } from "@/components/ApprovalModal";
import { DiffViewer } from "@/components/DiffViewer";
import { TaskPlan } from "@/components/TaskPlan";
import { api, wsUrl } from "@/lib/api";
import { ApprovalRequest, Task } from "@/lib/types";
import { ArrowUpRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export function TaskWorkspace({ taskId }: { taskId?: string }) {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [task, setTask] = useState<Task | null>(null);
  const [projects, setProjects] = useState<{ id: string; name: string }[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [approval, setApproval] = useState<ApprovalRequest | null>(null);
  const [diffs, setDiffs] = useState<{ path: string; before: string; after: string }[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const poll = useRef<number | null>(null);

  useEffect(() => {
    api<{ id: string; name: string }[]>("/api/v1/projects")
      .then(setProjects)
      .catch(() => undefined);
    let ws: WebSocket | undefined;
    api<{ token: string }>("/api/v1/auth/ws-token")
      .then((data) => {
        ws = new WebSocket(wsUrl("/api/v1/ws/ui", data.token));
        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.type === "approval.requested") {
            setApproval({
              id: msg.request_id,
              task_id: msg.task_id,
              action: msg.action,
              tool: msg.tool,
              target: "",
              command: msg.command,
              risk: msg.risk,
              reason: msg.reason,
              status: "pending",
              created_at: new Date().toISOString(),
              metadata: msg.metadata || {},
            });
          }
        };
      })
      .catch(() => undefined);
    return () => ws?.close();
  }, []);

  useEffect(() => {
    if (!taskId) return;
    refresh(taskId).catch((err) => {
      setError(err instanceof Error ? err.message : "Could not load task");
    });
    return () => {
      if (poll.current) window.clearInterval(poll.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  async function refresh(id: string) {
    const next = await api<Task>(`/api/v1/tasks/${id}`);
    setTask(next);
    const done = ["COMPLETED", "FAILED", "CANCELLED", "BLOCKED"].includes(next.status);
    if (done) {
      if (poll.current) {
        window.clearInterval(poll.current);
        poll.current = null;
      }
      const d = await api<{ path: string; before: string; after: string }[]>(`/api/v1/diffs/${id}`);
      setDiffs(d);
    } else if (!poll.current) {
      poll.current = window.setInterval(() => refresh(id), 1500);
    }
  }

  async function submit() {
    if (!input.trim() || busy) return;
    setError("");
    setBusy(true);
    try {
      const created = await api<Task>("/api/v1/tasks", {
        method: "POST",
        body: JSON.stringify({ input_text: input, project_id: projectId || null }),
      });
      setInput("");
      setDiffs([]);
      setTask(created);
      if (poll.current) window.clearInterval(poll.current);
      poll.current = window.setInterval(() => refresh(created.id), 1500);
      router.push(`/tasks/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create task");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <section className="glass cmd-shadow rounded-[2rem] p-6">
        <h1 className="text-4xl font-semibold tracking-tight">Tell it what you need done.</h1>
        <p className="mt-2 max-w-2xl text-sm text-[var(--fg-muted)]">
          Appi will plan, ask before sensitive actions, use tools on this device, verify results, and keep an audit trail.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="rounded-full border border-[var(--line)] bg-transparent px-4 py-2 text-sm"
          >
            <option value="">No project selected</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="mt-5 flex items-end gap-3 rounded-[1.6rem] border border-[var(--line)] bg-black/10 p-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Open the project, find why npm run dev is failing, fix it, run the tests and tell me what you changed."
            className="min-h-28 flex-1 resize-none bg-transparent p-3 text-base outline-none"
          />
          <button
            onClick={submit}
            disabled={!input.trim() || busy}
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent)] text-white disabled:opacity-40"
            aria-label="Submit task"
          >
            <ArrowUpRight size={18} />
          </button>
        </div>
        <p className="mt-2 text-xs text-[var(--fg-muted)]">Ctrl+Enter to send. Guardian still authorizes every action.</p>
        {error && <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>}
      </section>

      {task && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2 px-2 text-sm text-[var(--fg-muted)]">
            <span>Status: {task.status}</span>
            {task.verified && <span className="text-[var(--ok)]">Verified</span>}
            {task.error_message && <span className="text-[var(--danger)]">{task.error_message}</span>}
          </div>
          <TaskPlan goal={task.goal || task.title} steps={task.steps} />
          {task.result_summary && (
            <section className="glass rounded-3xl p-6">
              <div className="text-xs tracking-[0.2em] text-[var(--fg-muted)]">REPORT</div>
              <p className="mt-2 whitespace-pre-wrap text-sm">{task.result_summary}</p>
            </section>
          )}
          {diffs.map((diff) => (
            <DiffViewer key={diff.path} {...diff} />
          ))}
        </>
      )}
      {approval && <ApprovalModal request={approval} onDone={() => setApproval(null)} />}
    </div>
  );
}
