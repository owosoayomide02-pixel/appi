# Linux runtime

Same Python device-agent as Windows for files, shell, and Playwright. Voice wake-word is **not** included (`serve --no-voice`).

On a Linux machine:

```bash
bash scripts/setup-linux.sh
```

That installs Python deps, writes a systemd **user** unit with real paths, and enables it. Pair from the dashboard afterward:

```bash
cd apps/device-agent
python3 -m app.main pair --code 123456
```

This was not executed on a Linux host in this milestone. Desktop environment adapters (AT-SPI, DBus extras, verified tray) are not implemented.
