# Tool system

Every Appi action goes through a registered tool. The model cannot invoke arbitrary system functions.

## Interface

```
Tool
- name
- description
- input_schema
- risk_level
- required_permissions
- execute()   # device agent
- verify()    # API verification engine
```

Unknown tool names are rejected. Tool names must match `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`.

## File tools

`list_directory`, `read_file`, `write_file`, `create_file`, `rename_file`, `move_file`, `copy_file`, `delete_file` (elevated).

## Terminal tools

`run_command`, `start_process`, `stop_process`, `get_process_status`.

## Browser tools

`open_browser`, `open_url`, `click`, `type`, `read_page`, `screenshot`, `select`, `scroll`, `upload_file`, `download_file`.

## Project tools

`detect_framework`, `inspect_package_json`, `inspect_git_status`, `run_tests`, `run_build`, `detect_errors`.

## Universal Runtime Protocol

Every runtime action uses the shared request/response schemas in `packages/runtime-protocol/` and `services/api/app/tools/protocol.py`.

Legacy V0.1 names (`files.read_file`, `terminal.run_command`, `browser.open_url`) still execute. They map onto capabilities such as `filesystem.read` and `terminal.execute`.

Cloud tools (not sent to the device): `github.user`, `github.repos`, `gmail.profile`, `email.read`, `email.search`, `email.draft`, `email.send`, `calendar.read`, `calendar.write`. Guardian still runs. Missing connectors return `CONNECTOR_NOT_CONNECTED`.

Unknown or unimplemented tools return `CAPABILITY_UNAVAILABLE` — never a fake success.

## Capability registry

Support and permission are separate. A Windows runtime may report `filesystem.write: true` while Guardian still ASK before writing.

Implemented on desktop in this milestone: filesystem read/write/delete, terminal/process, Playwright browser tools.

Not implemented on any platform: desktop UI, clipboard, notifications, contacts, calendar, messaging, calling, location, camera, microphone, payments, social, cloud, database.

## Verification

A tool returning without an exception is not success.

- Files: existence and content
- Processes: still running / health check / exit code
- Browser: expected URL or text; MFA/CAPTCHA fail closed
- Code: lint/test/build hooks via project tools

## Protocol schemas

See `packages/tool-protocol/`.
