"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Cable,
  FolderGit2,
  History,
  LayoutDashboard,
  ListTodo,
  MemoryStick,
  MonitorSmartphone,
  Plus,
  Settings,
  Shield,
} from "lucide-react";

const items = [
  { href: "/app", label: "New Task", icon: Plus },
  { href: "/tasks", label: "Active Tasks", icon: ListTodo },
  { href: "/history", label: "History", icon: History },
  { href: "/projects", label: "Projects", icon: FolderGit2 },
  { href: "/memory", label: "Memory", icon: MemoryStick },
  { href: "/connections", label: "Connections", icon: Cable },
  { href: "/permissions", label: "Permissions", icon: Shield },
  { href: "/device", label: "Devices", icon: MonitorSmartphone },
  { href: "/activity", label: "Activity Log", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="glass flex h-full w-64 shrink-0 flex-col rounded-3xl p-5">
      <Link href="/" className="mb-8">
        <div className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">OPERATOR</div>
        <div className="mt-1 font-[family-name:var(--font-display)] text-2xl tracking-tight">APPI</div>
        <div className="mt-1 text-xs text-[var(--fg-muted)]">Think. Act. Verify.</div>
      </Link>
      <nav className="flex flex-1 flex-col gap-1">
        {items.map((item) => {
          const active =
            item.href === "/app"
              ? pathname === "/app"
              : item.href === "/tasks"
                ? pathname === "/tasks" || pathname.startsWith("/tasks/")
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm transition ${
                active ? "bg-[var(--accent-soft)] text-[var(--accent)]" : "text-[var(--fg-muted)] hover:bg-[var(--accent-soft)] hover:text-[var(--fg)]"
              }`}
            >
              <Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-6 flex items-center gap-2 text-xs text-[var(--fg-muted)]">
        <LayoutDashboard size={14} />
        Universal runtime
      </div>
    </aside>
  );
}
