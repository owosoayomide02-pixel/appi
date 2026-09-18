"use client";

import { AppShell } from "@/components/AppShell";
import { TaskWorkspace } from "@/components/TaskWorkspace";
import { useParams } from "next/navigation";

export default function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  return (
    <AppShell>
      <TaskWorkspace taskId={params.id} />
    </AppShell>
  );
}
