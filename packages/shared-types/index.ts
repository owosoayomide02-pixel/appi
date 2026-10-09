export type TaskStatus =
  | "CREATED"
  | "PLANNING"
  | "WAITING_FOR_APPROVAL"
  | "RUNNING"
  | "VERIFYING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "BLOCKED";

export type StepStatus =
  | "pending"
  | "waiting_for_approval"
  | "running"
  | "verifying"
  | "succeeded"
  | "failed"
  | "skipped"
  | "blocked"
  | "cancelled";

export type RiskLevel = "low" | "medium" | "high" | "forbidden";

export type PermissionDecision = "ALLOW" | "ASK" | "BLOCK";

export type PermissionKind =
  | "one_time"
  | "session"
  | "time_limited"
  | "permanent"
  | "amount_limited"
  | "resource_limited";

export type MemoryKind = "working" | "project" | "preference" | "secure";

export type DeviceStatus = "online" | "offline" | "pairing";

export interface DeviceCapabilities {
  filesystem: boolean;
  terminal: boolean;
  browser: boolean;
  desktop_ui: boolean;
  microphone: boolean;
  camera: boolean;
}

export interface PlanStep {
  id: string;
  description: string;
  tool: string;
  risk: RiskLevel;
  status: StepStatus;
  depends_on?: string[];
  approval_required?: boolean;
  input?: Record<string, unknown>;
}

export interface TaskPlan {
  goal: string;
  steps: PlanStep[];
}

export interface AuditEvent {
  timestamp: string;
  user_id: string;
  agent_id?: string | null;
  task_id?: string | null;
  step_id?: string | null;
  action: string;
  tool?: string | null;
  target?: string | null;
  risk_level: RiskLevel;
  permission_decision?: PermissionDecision | null;
  approved_by?: string | null;
  result?: string | null;
  verification_status?: string | null;
}

export const TASK_STATUSES: TaskStatus[] = [
  "CREATED",
  "PLANNING",
  "WAITING_FOR_APPROVAL",
  "RUNNING",
  "VERIFYING",
  "COMPLETED",
  "FAILED",
  "CANCELLED",
  "BLOCKED",
];
