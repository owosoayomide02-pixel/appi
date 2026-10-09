# Roadmap

See `docs/implementation-checklist.md` for V0.1 status.

## Done in V0.1

Milestones 1–10 at prototype depth:

- Monorepo, dashboard, FastAPI, auth, tasks
- Windows device agent (pair, files, terminal, events)
- Planner + tool registry + execution loop
- ALLOW / ASK / BLOCK, approval UI, kill switch
- Coding workspace, diffs
- Playwright browser tools and domain policy
- Four memory kinds + retrieval
- Verification before COMPLETED
- Secret vault, redaction, injection boundaries, tests

## Universal Runtime (this milestone)

- Shared capability registry and Guardian (capability check before ALLOW/ASK/BLOCK)
- Universal Runtime Protocol + heartbeat
- Cross-platform runtime layout (`apps/runtimes/*`)
- Working desktop runtime on the developer OS (Windows: files, terminal, Playwright)
- Android/iOS placeholders that return `CAPABILITY_UNAVAILABLE`
- Devices UI (capabilities, heartbeat, revoke)
- Connection catalog by category (never faked as connected)

## Device Intelligence V1

- Background desktop runtime (`serve`, autostart, IPC) on Windows
- Voice pipeline abstractions (wake-word not live-tested)
- Windows app launch, system.info, clipboard, files.search
- Connector stubs + `CONNECTOR_NOT_CONNECTED` for transfers
- Scheduler table (Guardian at execution time)

## Next milestone

- Google Contacts OAuth (separate from Gmail and Calendar scopes)
- macOS/Linux background verification on real machines
- Deeper iOS App Intents beyond "Open Appi"

## Explicitly later

- Contacts, calls, messaging, social posting
- Account creation, live payments, shopping, banking
- Unrestricted desktop UI control
- External spend above ₦0
