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

export type User = {
  id: string;
  email: string;
  display_name: string;
  onboarding_completed: boolean;
  kill_switch_active: boolean;
  theme: string;
};

export type Step = {
  id: string;
  step_key: string;
  description: string;
  tool: string;
  risk: string;
  status: string;
  depends_on: string[];
  approval_required: boolean;
  sequence: number;
  error?: string | null;
  output?: Record<string, unknown> | null;
};

export type Task = {
  id: string;
  title: string;
  goal: string;
  input_text: string;
  status: TaskStatus;
  result_summary: string | null;
  error_message: string | null;
  verified: boolean;
  project_id: string | null;
  device_id: string | null;
  created_at: string;
  steps: Step[];
};

export type ApprovalRequest = {
  id: string;
  task_id: string | null;
  action: string;
  tool: string;
  target: string;
  command: string | null;
  risk: string;
  reason: string;
  status: string;
  created_at: string;
  metadata?: Record<string, unknown>;
};

export type Device = {
  id: string;
  name: string;
  os: string;
  platform: string;
  runtime_version: string;
  status: string;
  last_seen_at: string | null;
  last_heartbeat_at: string | null;
  revoked: boolean;
  capabilities: Record<string, boolean>;
  capability_groups: Record<string, boolean>;
  voice?: {
    enabled?: boolean;
    muted?: boolean;
    tts_voice?: string;
    tts_gender?: string;
    culture?: string;
    min_confidence?: number;
    voices?: { name: string; culture: string; gender: string; enabled?: boolean }[];
    recognizers?: { id: string; name: string; culture: string }[];
  };
  granted_permissions?: { id: string; resource: string; scope: string; actions: string[]; kind: string; expires_at: string | null }[];
  temporary_permissions?: { id: string; resource: string; scope: string; actions: string[]; kind: string; expires_at: string | null }[];
};

export type Connection = {
  provider: string;
  name: string;
  category: string;
  oauth: boolean;
  status: "connected" | "not_connected" | "permission_required" | "unsupported";
  connected: boolean;
  oauth_ready?: boolean;
  account?: string | null;
};
