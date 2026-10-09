"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { useEffect, useState } from "react";

type Event = {
  id: string;
  timestamp: string;
  action: string;
  tool: string | null;
  target: string | null;
  risk_level: string;
  permission_decision: string | null;
  result: string | null;
  verification_status: string | null;
  task_id: string | null;
};

export default function ActivityPage() {
  const [rows, setRows] = useState<Event[]>([]);
  useEffect(() => {
    api<Event[]>("/api/v1/audit").then(setRows).catch(() => undefined);
  }, []);
  return (
    <AppShell>
      <h1 className="mb-2 text-3xl font-semibold">Activity log</h1>
      <p className="mb-6 text-sm text-[var(--fg-muted)]">Every meaningful action. Secrets are redacted.</p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-[var(--fg-muted)]">
            <tr>
              <th className="p-3">Time</th>
              <th className="p-3">Action</th>
              <th className="p-3">Target</th>
              <th className="p-3">Risk</th>
              <th className="p-3">Permission</th>
              <th className="p-3">Result</th>
              <th className="p-3">Verified</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-[var(--line)]">
                <td className="p-3 font-mono text-xs">{row.timestamp.slice(11, 19)}</td>
                <td className="p-3">{row.tool || row.action}</td>
                <td className="p-3 font-mono text-xs">{row.target || "—"}</td>
                <td className="p-3">{row.risk_level}</td>
                <td className="p-3">{row.permission_decision || "—"}</td>
                <td className="p-3">{row.result || "—"}</td>
                <td className="p-3">{row.verification_status || "—"}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr className="border-t border-[var(--line)]">
                <td className="p-6 text-[var(--fg-muted)]" colSpan={7}>
                  No actions recorded yet. Every tool call Appi makes will appear here.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
