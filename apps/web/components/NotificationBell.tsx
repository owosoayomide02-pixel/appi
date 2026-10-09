"use client";

import { api } from "@/lib/api";
import { Bell } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

type Note = {
  id: string;
  title: string;
  body: string;
  read: boolean;
  task_id: string | null;
  created_at: string;
};

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notes, setNotes] = useState<Note[]>([]);

  async function load() {
    const rows = await api<Note[]>("/api/v1/notifications");
    setNotes(rows.slice(0, 8));
  }

  useEffect(() => {
    load().catch(() => undefined);
    const timer = window.setInterval(() => load().catch(() => undefined), 12000);
    return () => window.clearInterval(timer);
  }, []);

  const unread = notes.filter((n) => !n.read);

  async function mark(id: string) {
    await api(`/api/v1/notifications/${id}/read`, { method: "POST" });
    setNotes((rows) => rows.map((n) => (n.id === id ? { ...n, read: true } : n)));
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-full border border-[var(--line)] p-2"
        aria-label="Notifications"
      >
        <Bell size={16} className="text-[var(--fg-muted)]" />
        {unread.length > 0 && <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-[var(--danger)]" />}
      </button>
      {open && (
        <div className="glass absolute right-0 z-30 mt-3 w-80 rounded-2xl p-3">
          <div className="px-2 pb-2 text-xs tracking-[0.2em] text-[var(--fg-muted)]">NOTIFICATIONS</div>
          {notes.length === 0 && <p className="px-2 py-4 text-sm text-[var(--fg-muted)]">Nothing waiting.</p>}
          <div className="max-h-80 space-y-1 overflow-auto">
            {notes.map((note) => (
              <Link
                key={note.id}
                href={note.task_id ? `/tasks/${note.task_id}` : "/activity"}
                onClick={() => {
                  if (!note.read) mark(note.id).catch(() => undefined);
                  setOpen(false);
                }}
                className={`block rounded-xl px-3 py-2 text-sm ${note.read ? "text-[var(--fg-muted)]" : "bg-[var(--accent-soft)]"}`}
              >
                <div className="font-medium text-[var(--fg)]">{note.title}</div>
                <div className="mt-0.5 line-clamp-2 text-xs">{note.body}</div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
