-- APPI core schema (mirrors services/api SQLAlchemy models)
-- Applied to linked Supabase project for hosted Postgres.

create extension if not exists "pgcrypto";

-- users
create table if not exists public.users (
  id text primary key,
  email varchar(320) not null unique,
  password_hash varchar(255) not null,
  display_name varchar(120) not null default '',
  onboarding_completed boolean not null default false,
  kill_switch_active boolean not null default false,
  theme varchar(16) not null default 'dark',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists ix_users_email on public.users (email);

-- devices
create table if not exists public.devices (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  name varchar(120) not null,
  os varchar(80) not null default 'Windows',
  status varchar(32) not null default 'offline',
  token_hash varchar(128) not null unique,
  pairing_code_hash varchar(128),
  pairing_expires_at timestamptz,
  last_seen_at timestamptz,
  platform varchar(32) not null default 'windows',
  runtime_version varchar(32) not null default '0.2.0',
  capabilities_json jsonb not null default '{}'::jsonb,
  voice_json jsonb not null default '{}'::jsonb,
  last_heartbeat_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists ix_devices_user_id on public.devices (user_id);

-- device_capabilities
create table if not exists public.device_capabilities (
  id text primary key,
  device_id text not null unique references public.devices (id) on delete cascade,
  filesystem boolean not null default true,
  terminal boolean not null default true,
  browser boolean not null default true,
  desktop_ui boolean not null default false,
  microphone boolean not null default false,
  camera boolean not null default false
);

-- agent_sessions
create table if not exists public.agent_sessions (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  device_id text references public.devices (id) on delete set null,
  status varchar(32) not null default 'active',
  kill_switch_active boolean not null default false,
  created_at timestamptz not null default now(),
  ended_at timestamptz
);
create index if not exists ix_agent_sessions_user_id on public.agent_sessions (user_id);

-- allowed_folders
create table if not exists public.allowed_folders (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  device_id text references public.devices (id) on delete set null,
  path text not null,
  created_at timestamptz not null default now()
);
create index if not exists ix_allowed_folders_user_id on public.allowed_folders (user_id);

-- domain_permissions
create table if not exists public.domain_permissions (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  domain varchar(255) not null,
  policy varchar(32) not null default 'ask',
  created_at timestamptz not null default now()
);
create index if not exists ix_domain_permissions_user_id on public.domain_permissions (user_id);

-- projects
create table if not exists public.projects (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  name varchar(160) not null,
  root_path text not null,
  framework varchar(80),
  language varchar(80),
  last_indexed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists ix_projects_user_id on public.projects (user_id);

-- project_files
create table if not exists public.project_files (
  id text primary key,
  project_id text not null references public.projects (id) on delete cascade,
  path text not null,
  language varchar(40),
  content_hash varchar(64),
  summary text,
  indexed_at timestamptz not null default now()
);
create index if not exists ix_project_files_project_id on public.project_files (project_id);

-- tasks
create table if not exists public.tasks (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  device_id text references public.devices (id) on delete set null,
  project_id text references public.projects (id) on delete set null,
  session_id text references public.agent_sessions (id) on delete set null,
  title varchar(200) not null default '',
  goal text not null default '',
  input_text text not null,
  status varchar(32) not null default 'created',
  result_summary text,
  error_message text,
  verified boolean not null default false,
  budget_max_model_calls integer not null default 40,
  budget_max_tool_calls integer not null default 80,
  budget_max_runtime_seconds integer not null default 1800,
  budget_max_external_spend double precision not null default 0,
  model_calls_used integer not null default 0,
  tool_calls_used integer not null default 0,
  retry_count integer not null default 0,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists ix_tasks_user_id on public.tasks (user_id);
create index if not exists ix_tasks_status on public.tasks (status);

-- task_steps
create table if not exists public.task_steps (
  id text primary key,
  task_id text not null references public.tasks (id) on delete cascade,
  step_key varchar(64) not null,
  description text not null,
  tool varchar(80) not null,
  risk varchar(16) not null default 'low',
  status varchar(32) not null default 'pending',
  depends_on jsonb not null default '[]'::jsonb,
  approval_required boolean not null default false,
  sequence integer not null default 0,
  input_json jsonb not null default '{}'::jsonb,
  output_json jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists ix_task_steps_task_id on public.task_steps (task_id);

-- tool_calls
create table if not exists public.tool_calls (
  id text primary key,
  task_id text not null references public.tasks (id) on delete cascade,
  step_id text references public.task_steps (id) on delete set null,
  tool_name varchar(80) not null,
  input_json jsonb not null default '{}'::jsonb,
  output_json jsonb,
  success boolean not null default false,
  verification_required boolean not null default true,
  verification_status varchar(32) not null default 'pending',
  created_at timestamptz not null default now()
);
create index if not exists ix_tool_calls_task_id on public.tool_calls (task_id);

-- permissions
create table if not exists public.permissions (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  subject varchar(120) not null,
  resource varchar(80) not null,
  scope text not null default '*',
  actions jsonb not null default '[]'::jsonb,
  kind varchar(32) not null default 'permanent',
  expires_at timestamptz,
  requires_confirmation boolean not null default false,
  max_amount double precision,
  used_amount double precision not null default 0,
  currency varchar(8),
  merchant_type varchar(80),
  task_id text references public.tasks (id) on delete set null,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists ix_permissions_user_id on public.permissions (user_id);

-- permission_requests
create table if not exists public.permission_requests (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  task_id text references public.tasks (id) on delete set null,
  step_id text references public.task_steps (id) on delete set null,
  action varchar(120) not null,
  tool varchar(80) not null,
  target text not null default '',
  command text,
  risk varchar(16) not null default 'medium',
  reason text not null default '',
  metadata_json jsonb not null default '{}'::jsonb,
  status varchar(32) not null default 'pending',
  decided_at timestamptz,
  decided_by varchar(36),
  created_at timestamptz not null default now()
);
create index if not exists ix_permission_requests_user_id on public.permission_requests (user_id);

-- audit_events
create table if not exists public.audit_events (
  id text primary key,
  timestamp timestamptz not null default now(),
  user_id text not null references public.users (id) on delete cascade,
  agent_id varchar(36),
  task_id varchar(36),
  step_id varchar(36),
  action varchar(120) not null,
  tool varchar(80),
  target text,
  risk_level varchar(16) not null default 'low',
  permission_decision varchar(16),
  approved_by varchar(36),
  result varchar(40),
  verification_status varchar(32),
  extra jsonb
);
create index if not exists ix_audit_events_timestamp on public.audit_events (timestamp);
create index if not exists ix_audit_events_user_id on public.audit_events (user_id);
create index if not exists ix_audit_events_task_id on public.audit_events (task_id);

-- memories
create table if not exists public.memories (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  kind varchar(32) not null default 'working',
  project_id text references public.projects (id) on delete set null,
  task_id text references public.tasks (id) on delete set null,
  topic varchar(160) not null default '',
  tool varchar(80),
  importance integer not null default 1,
  content text not null default '',
  secret_handle varchar(160),
  created_at timestamptz not null default now(),
  expires_at timestamptz
);
create index if not exists ix_memories_user_id on public.memories (user_id);
create index if not exists ix_memories_kind on public.memories (kind);

-- connections
create table if not exists public.connections (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  provider varchar(40) not null,
  category varchar(40) not null default 'developer',
  status varchar(32) not null default 'not_connected',
  token_handle varchar(160),
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_user_provider unique (user_id, provider)
);
create index if not exists ix_connections_user_id on public.connections (user_id);

-- notifications
create table if not exists public.notifications (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  type varchar(40) not null,
  title varchar(160) not null,
  body text not null default '',
  read boolean not null default false,
  task_id varchar(36),
  created_at timestamptz not null default now()
);
create index if not exists ix_notifications_user_id on public.notifications (user_id);

-- secrets (encrypted vault handles)
create table if not exists public.secrets (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  handle varchar(160) not null unique,
  encrypted_value text not null,
  created_at timestamptz not null default now()
);
create index if not exists ix_secrets_user_id on public.secrets (user_id);

-- user_policies
create table if not exists public.user_policies (
  id text primary key,
  user_id text not null unique references public.users (id) on delete cascade,
  read_project_files varchar(16) not null default 'allow',
  edit_project_files varchar(16) not null default 'ask',
  run_tests varchar(16) not null default 'allow',
  run_terminal varchar(16) not null default 'ask',
  use_browser varchar(16) not null default 'ask',
  delete_files varchar(16) not null default 'ask'
);

-- scheduled_jobs
create table if not exists public.scheduled_jobs (
  id text primary key,
  user_id text not null references public.users (id) on delete cascade,
  device_id text references public.devices (id) on delete set null,
  project_id text references public.projects (id) on delete set null,
  input_text text not null,
  timezone varchar(64) not null default 'UTC',
  interval_seconds integer,
  next_run_at timestamptz not null,
  last_run_at timestamptz,
  expires_at timestamptz,
  enabled boolean not null default true,
  retry_count integer not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists ix_scheduled_jobs_user_id on public.scheduled_jobs (user_id);
create index if not exists ix_scheduled_jobs_next_run_at on public.scheduled_jobs (next_run_at);

-- Lock down: enable RLS; API uses service role / direct Postgres (bypasses RLS).
do $$
declare
  t text;
begin
  foreach t in array array[
    'users','devices','device_capabilities','agent_sessions','allowed_folders',
    'domain_permissions','projects','project_files','tasks','task_steps','tool_calls',
    'permissions','permission_requests','audit_events','memories','connections',
    'notifications','secrets','user_policies','scheduled_jobs'
  ]
  loop
    execute format('alter table public.%I enable row level security', t);
  end loop;
end $$;
