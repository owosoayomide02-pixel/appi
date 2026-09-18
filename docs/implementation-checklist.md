# Appi V0.1 Implementation Checklist

Status key: `[x]` done · `[ ]` remaining · `[~]` partial

The existing repository was a default Flutter Hello World starter. It is preserved at `apps/mobile/` for a future mobile-device agent. V0.1 is Windows-first and uses the Next.js + FastAPI + Python device-agent stack specified in the product brief.

---

## Milestone 1 — Foundation

- [x] Monorepo layout (`apps/`, `services/`, `packages/`, `docs/`, `scripts/`)
- [x] Next.js dashboard shell (sidebar, conversation, branding)
- [x] FastAPI server
- [x] PostgreSQL schema + SQLAlchemy models (SQLite fallback when Docker/Postgres is unavailable)
- [x] Authentication (register / sign-in, hashed passwords, JWT cookies)
- [x] Task creation and task state machine
- [x] First-time onboarding flow
- [x] docker-compose.yml for PostgreSQL
- [x] `.env.example`

## Milestone 2 — Windows Device Agent

- [x] Device identity generation
- [x] Secure pairing (one-time code + device token)
- [x] File tools (sandboxed to approved folders)
- [x] Structured terminal execution
- [x] Local events over WebSocket
- [x] Device status and capability registry

## Milestone 3 — Planner and Tools

- [x] ModelProvider abstraction (`generate`, `plan`, `classify_action`, `summarize`, `tool_decision`)
- [x] Configurable providers via environment variables
- [x] Structured planner (goal + steps + risk + dependencies)
- [x] Tool registry and tool protocol
- [x] Task execution loop (plan → authorize → act → verify)

## Milestone 4 — Permissions

- [x] ALLOW / ASK / BLOCK engine
- [x] Structured permission records (one-time, session, time-limited, permanent)
- [x] Approval UI (once / for this task / deny)
- [x] Temporary permission grant and revoke
- [x] Global kill switch below the AI layer

## Milestone 5 — Coding Agent

- [x] Project folder selection
- [x] Framework / package detection
- [x] Code search and file inspection
- [x] Approved file edits
- [x] Tests / build / dev-server tools
- [x] Before/after diff viewer

## Milestone 6 — Browser Agent

- [x] Playwright-backed browser tools
- [x] Domain permission policy
- [x] Navigation, read, click, type, select, scroll, screenshot
- [x] Form submission requires approval for credentials/payments/PII
- [x] CAPTCHA / MFA pause (no bypass)

## Milestone 7 — Memory

- [x] Working, project, preference, and secure memory
- [x] Retrieval by user / project / topic / tool / recency / importance
- [x] Memory management UI
- [x] Secure handles instead of raw secrets in model context

## Milestone 8 — Verification

- [x] File existence / content checks
- [x] Process / health-check verification
- [x] Browser expected-state verification hooks
- [x] Code lint/test/build verification hooks
- [x] Tasks cannot become COMPLETED without verification

## Milestone 9 — Security Hardening

- [x] Secrets vault abstraction
- [x] Secret redaction in logs, audit, model context, API errors
- [x] Prompt-injection boundaries (user / model / tool / untrusted)
- [x] Path traversal prevention
- [x] Terminal allow/deny restrictions
- [x] Rate limiting, authn/z, payload validation
- [x] Security-focused tests

## Milestone 10 — Appi V0.1 Release

- [x] README setup instructions
- [x] `docs/architecture.md`
- [x] `docs/security.md`
- [x] `docs/tool-system.md`
- [x] `docs/roadmap.md`
- [x] End-to-end coding-task path: understand → plan → inspect → act → verify → report

## Universal Runtime

- [x] Universal runtime protocol (compatible with existing tool protocol)
- [x] Capability registry (support ≠ permission)
- [x] Guardian capability checks before ALLOW/ASK/BLOCK
- [x] Device platform, runtime version, heartbeat, revoke
- [x] `apps/runtimes/{shared,windows,linux,macos,android,ios}`
- [x] Working desktop runtime on the current OS
- [x] Android/iOS placeholders return `CAPABILITY_UNAVAILABLE`
- [x] Devices UI and categorized Connections catalog
- [x] Heuristic planner and SQLite local mode preserved

## Device Intelligence V1

- [x] `apps/runtime-core` background lifecycle, errors, activity detector, autostart, IPC
- [x] `python -m app.main serve` reconnect loop (dashboard may close)
- [x] Windows Startup-folder autostart helper
- [x] `services/voice` pipeline abstractions and microphone states
- [x] Windows `app.launch`, `system.info`, clipboard, `files.search`
- [x] User-activity / execution-mode hooks (`serve` asks when busy)
- [x] Action resolver + scheduler table (Guardian still runs at fire time)
- [x] `CONNECTOR_NOT_CONNECTED` for transfers with no payment connector
- [x] Flutter navigation shell (UI only)
- [x] Live wake-word acceptance test (Windows SAPI / Ctrl+Shift+A fallback)
- [x] Android foreground service template (Kotlin; not compiled on this machine)
- [x] macOS LaunchAgent + Linux systemd templates
- [x] iOS App Intents
- [x] GitHub OAuth / verified PAT
- [x] Gmail OAuth / verified token
- [x] Google Calendar OAuth / verified token (Contacts still Planned)

## Website + Operator

- [x] Public product site (`/`, `/product`, `/security`, `/download`)
- [x] Operator dashboard moved to `/app`; marketing lives at `/`
- [x] Task detail route `/tasks/[id]` with live plan, report, and diffs
- [x] Notification bell reads and marks notifications
- [x] Responsive sidebar drawer for small screens
- [x] Empty states for tasks, history, memory, projects, permissions, activity
- [x] Readable validation errors instead of raw API JSON
- [x] Custom 404

---

## Explicitly out of scope for V0.1

Do not implement before permission, audit, device-agent, and verification are solid:

- Payments, banking, purchases
- Calls, SMS, social posting
- Unrestricted device / full-drive control
- Account creation on third-party sites
- CAPTCHA/MFA bypass
- Fake OAuth “connected” states
