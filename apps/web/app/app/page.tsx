"use client";

import { AppShell } from "@/components/AppShell";
import { TaskWorkspace } from "@/components/TaskWorkspace";

export default function OperatorHomePage() {
  return (
    <AppShell>
      <TaskWorkspace />
    </AppShell>
  );
}
