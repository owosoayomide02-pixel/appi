# macOS runtime

Files, shell, and Playwright can run through the shared Python agent. Voice wake-word is **not** included (`serve --no-voice`). Native TCC adapters are not implemented.

On a Mac:

```bash
bash scripts/setup-macos.sh
```

That installs Python deps and loads `~/Library/LaunchAgents/dev.appi.runtime.plist` with this machine’s Python path. Pair from the dashboard afterward:

```bash
cd apps/device-agent
python3 -m app.main pair --code 123456
```

A future Swift bridge is required for:

- native TCC permission adapters (microphone, accessibility, automation, screen recording, files)
- App Intents / Shortcuts
- contacts, calendar, camera, location
