# APPI

**Tell it what you need done.**  
Think. Act. Verify.

Appi is a persistent, voice-accessible AI operator: a dashboard, a FastAPI cloud brain, and a background device runtime. It plans, asks before sensitive actions, executes only real capabilities, verifies results, and keeps an audit trail.

It is **not** a chatbot that pretends work happened. Unsupported abilities return honest errors such as `CAPABILITY_UNAVAILABLE` or `CONNECTOR_NOT_CONNECTED`.

Voice is an input method. It does not bypass Guardian.

## Architecture

```
USER → "Appi..." → listen → understand → plan → Guardian → act → verify → report

APPI UI  +  BACKGROUND RUNTIME  +  VOICE SERVICE  +  CLOUD BRAIN
```

See `docs/architecture.md`, `docs/background-runtime.md`, `docs/voice.md`, `docs/platform-capabilities.md`, `docs/connectors.md`, and `docs/security.md`.

## Repository

| Path | Role |
| --- | --- |
| `apps/web` | Next.js website + operator dashboard |
| `apps/device-agent` | Working desktop runtime |
| `apps/runtime-core` | Shared background-runtime logic |
| `apps/runtimes/` | Per-OS entries + Android/iOS placeholders |
| `apps/mobile` | Flutter shell (UI only) |
| `services/api` | FastAPI brain, Guardian, auth, planner, audit |
| `services/voice` | Wake-word / STT / TTS abstractions |
| `packages/` | Shared types, tool protocol, runtime protocol |

## Prerequisites

- Python 3.11+ (3.14 is fine)
- Node.js 20+
- Optional: Docker, for PostgreSQL (`docker compose up -d`)
- Optional: `AI_API_KEY` or `OPENAI_API_KEY`. Without a key, Appi uses the heuristic planner.

Local development uses SQLite. Docker is **not** required.

## Setup

```powershell
cd APPI-0.1.0\APPI-0.1.0
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

That creates `.env` at the repo root, writes `apps\web\.env.local`, installs Python packages into `.venv`, and runs `npm install` for the website.

Manual equivalent:

```powershell
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .\services\api\[dev]
.\.venv\Scripts\python.exe -m pip install -e .\apps\device-agent\[dev]
cd apps\web
npm install
cd ..\..
```

## Environment files

| File | Role |
| --- | --- |
| `.env.example` | Template (safe to commit). Local defaults documented. |
| `.env` | **Your secrets.** Repo root only. Gitignored. Loaded by the API and device agent. |
| `apps/web/.env.local` | Public Next.js vars (`NEXT_PUBLIC_APP_URL`, `NEXT_PUBLIC_API_URL`). Gitignored. Created by `setup.ps1`. |

Never put real API keys in the Windows `.exe` package. The exe pairs to whatever account/brain is already running.

Edit `.env` if you want a model provider:

```
AI_PROVIDER=openai
AI_API_KEY=sk-...
```

## Website

| URL | Role |
| --- | --- |
| http://localhost:3000 | Product website |
| http://localhost:3000/app | Operator dashboard |
| http://localhost:3000/device | Pair this PC |
| http://localhost:3000/login | Sign in |

The Windows desktop window opens `/app` directly.

## Run (Windows app)

Appi is meant to start like a normal program: Desktop or Start Menu, no PowerShell or CMD.

One-time from this folder (do **not** Run as administrator):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preview-windows.ps1
```

Then **double-click Appi** on the Desktop. Close the window and Appi stays in the tray; say **Appi** or press **Ctrl+Shift+A**.

Pair once from http://localhost:3000/device (six-digit code):

```powershell
cd apps\device-agent
..\..\.venv\Scripts\python.exe -m app.main pair --code 482917
```

Voice is on by default. Pick the speaking voice in Settings. Connectors are optional for this preview.

Developer consoles (only if you are debugging):

```powershell
.\scripts\dev.ps1 -Api
.\scripts\dev.ps1 -Web
.\scripts\dev.ps1 -Agent
# or everything:
.\scripts\dev.ps1 -All
```

## Installers

| Platform | Command | Output |
| --- | --- | --- |
| Windows `.exe` | `powershell -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1` | `dist\windows\Appi\Appi.exe` + `Appi-windows.zip` |
| Android `.apk` | `powershell -ExecutionPolicy Bypass -File .\scripts\build-android.ps1` | Needs Android Studio |
| Linux | On Linux: `bash scripts/setup-linux.sh` | systemd user service (`serve --no-voice`) |
| macOS | On a Mac: `bash scripts/setup-macos.sh` | LaunchAgent (`serve --no-voice`) |
| iPhone | On a Mac with Xcode: `bash scripts/setup-ios.sh` | Simulator `.app` placeholder (not a signed IPA) |

Prefer the Desktop **Appi** shortcut from `preview-windows.ps1` / `python -m app.main install`. That starts the full app (brain + dashboard + assistant) without a console.

`Appi.exe` in `dist\windows\Appi\` is only the assistant. It does not start the dashboard by itself. Do not Run as administrator. Pair with `Appi.exe pair --code 123456` if you use that exe. Open http://localhost:3000/app after pairing.

`python -m app.main run` still works as a foreground session.

Use the pairing code from the Devices page (six digits, no brackets).

The Devices page should show the runtime online, a heartbeat, and an honest capability list.

GitHub, Gmail, and Google Calendar stay optional cloud connectors. This laptop preview does not require them.

## Tests

```powershell
cd services\api
..\..\.venv\Scripts\python.exe -m pytest
cd ..\..\apps\device-agent
..\..\.venv\Scripts\python.exe -m pytest
cd ..\web
npm run lint
npx tsc --noEmit
```

## Environment notes

Copy `.env.example` via `scripts\setup.ps1`. `AI_PROVIDER` and `AI_API_KEY` are optional. Never commit real secrets.
