# Windows runtime

Entry: `python main.py pair --code …` then `python main.py run`.

Delegates to `apps/device-agent`, which implements:

- filesystem read/write/delete (approved folders)
- structured terminal / process start-stop
- Playwright browser

Not implemented (returns `CAPABILITY_UNAVAILABLE`):

- desktop UI automation
- clipboard
- OS notifications
- contacts, calendar, calls, payments, social, camera, microphone
