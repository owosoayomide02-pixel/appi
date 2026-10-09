# Architecture

Appi is a persistent, voice-accessible AI operator. The cloud brain plans and authorizes; a **background runtime** on each device executes only capabilities it actually implements.

```
USER
  ↓
"Appi..."
  ↓
LISTEN (local wake-word / hotkey)
  ↓
UNDERSTAND
  ↓
PLAN
  ↓
GUARDIAN
  ↓
ACT
  ↓
VERIFY
  ↓
REPORT
```

Process split:

```
APPI UI  +  BACKGROUND RUNTIME  +  VOICE SERVICE  +  CLOUD CONNECTION
```

Closing the dashboard does not stop the local runtime.

```
APPI CLOUD BRAIN
      |
      v
TASK PLANNER / ACTION RESOLVER
      |
      v
GUARDIAN / PERMISSION ENGINE
      |
      v
TOOL ROUTER
      |
      v
UNIVERSAL RUNTIME PROTOCOL
      |
+-----+-----+-----+-----+-----+
|           |           |     |
Windows   Linux       macOS  Android  iOS
Runtime   Runtime     Runtime Runtime  Runtime
```

## Runtimes

| Path | Role |
| --- | --- |
| `apps/web` | Next.js dashboard |
| `apps/device-agent` | Working desktop Python runtime |
| `apps/runtime-core` | Shared background lifecycle, errors, activity, autostart, IPC |
| `apps/runtimes/windows` | Windows entry (delegates to device-agent) |
| `apps/runtimes/linux` | Linux entry (autostart helper; DBus not implemented) |
| `apps/runtimes/macos` | macOS entry (LaunchAgent helper; no Swift/TCC bridge yet) |
| `apps/runtimes/android` | Placeholder + Kotlin folder (not packaged) |
| `apps/runtimes/ios` | Placeholder + App Intents notes |
| `apps/mobile` | Flutter navigation shell (UI only) |
| `services/api` | FastAPI brain, Guardian, planner, audit, memory, scheduler |
| `services/voice` | Wake-word / STT / TTS abstractions |
| `packages/runtime-protocol` | Shared request/response schemas |

## Control flow

1. The user speaks, types, or schedules a goal. Voice does not skip security.
2. The brain retrieves a **small** relevant memory slice (never the whole device).
3. An action resolver prefers official API → OS → browser → UI automation → ask.
4. A `ModelProvider` produces a structured plan. Heuristic mode still works without `AI_API_KEY`.
5. **Guardian** checks: kill switch → connector (for payments) → capability available? → ALLOW / ASK / BLOCK.
6. Honest errors include `CAPABILITY_UNAVAILABLE`, `CONNECTOR_NOT_CONNECTED`, `NETWORK_REQUIRED`, `DEVICE_OFFLINE`.
7. `ALLOW` is dispatched over the Universal Runtime Protocol. `ASK` pauses for the approval UI. `BLOCK` stops the step.
8. The runtime validates paths/commands again locally. Background-safe tools avoid stealing focus.
9. The verifier checks that the world actually changed.
10. Audit events are written with secrets redacted.
11. The task becomes `COMPLETED` only after verification.

Scheduled jobs re-run Guardian at fire time. Proactive alerts default to quiet (`IMPORTANT` and above only, not enabled).

See `docs/background-runtime.md`, `docs/voice.md`, `docs/platform-capabilities.md`, and `docs/connectors.md`.


## Task state machine

`CREATED → PLANNING → WAITING_FOR_APPROVAL | RUNNING → VERIFYING → COMPLETED`

Also: `FAILED`, `CANCELLED`, `BLOCKED`.

`COMPLETED` is unreachable without `verified=True`.

## Model providers

Unchanged: `generate`, `plan`, `classify_action`, `summarize`, `tool_decision`.

`AI_PROVIDER` + `AI_API_KEY` remain optional (`heuristic` by default). `OPENAI_API_KEY` is accepted as a fallback for `AI_API_KEY`.

## Universal Runtime Protocol

Request:

```json
{
  "task_id": "task_123",
  "step_id": "step_6",
  "tool": "filesystem.read",
  "permission_token": "...",
  "input": {},
  "timeout": 30
}
```

Existing V0.1 tool names (`files.read_file`, `terminal.run_command`, …) still work and map onto the capability registry.

Response:

```json
{
  "success": true,
  "platform": "windows",
  "result": {},
  "verification": {},
  "error": null
}
```

Runtimes send a heartbeat about every 15 seconds with platform, runtime version, and the capability map.

## Connectors

Services are not treated as device UI automation. Preferred order:

Official API / OAuth → approved OS integration → browser automation → manual handoff.

Catalog entries exist for developer, cloud, communication, social, productivity, payments, finance, and shopping providers. None are marked **Connected** without real credentials.

## Memory

Memory stays in Appi Cloud (task, project, preferences, connection metadata, policies). Secrets remain encrypted handles. Device storage is never uploaded wholesale.
