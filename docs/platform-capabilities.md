# Platform capabilities

Never mark a row **Implemented** unless it was tested. This matrix is for Device Intelligence V1 on the developer Windows machine.

Legend: **Implemented** · **Planned** · **OS Restricted** · **Unavailable**

| Capability | Windows | macOS | Linux | Android | iOS |
| --- | --- | --- | --- | --- | --- |
| filesystem.read/write/delete | Implemented | Planned | Planned | Unavailable | OS Restricted |
| files.search | Implemented | Planned | Planned | Unavailable | OS Restricted |
| terminal / process | Implemented | Planned | Planned | Unavailable | OS Restricted |
| browser (Playwright) | Implemented | Planned | Planned | Unavailable | OS Restricted |
| app.launch / desktop.launch_app | Implemented | Planned | Planned | Planned | OS Restricted |
| system.info | Implemented | Planned | Planned | Planned | Planned |
| clipboard read/write | Implemented | Planned | Planned | Planned | Planned |
| system.volume / wifi / bluetooth | Planned | Planned | Planned | Planned | OS Restricted |
| system.shutdown / restart | Planned | Planned | Planned | Planned | OS Restricted |
| desktop.inspect_ui / interact | Planned | Planned | Planned | Unavailable | OS Restricted |
| notification.send | Planned | Planned | Planned | Planned | Planned |
| background runtime / heartbeat | Implemented | Planned | Planned | Planned | OS Restricted |
| wake word | Implemented | Planned | Planned | Planned | Planned |
| STT / TTS | Implemented | Planned | Planned | Planned | Planned |
| contacts / calendar | Planned (Contacts) / Implemented (cloud Calendar) | Planned (Contacts) / Implemented (cloud Calendar) | Planned (Contacts) / Implemented (cloud Calendar) | Planned (Contacts) / Implemented (cloud Calendar) | Planned (Contacts) / Implemented (cloud Calendar) |
| email (Gmail, cloud API) | Implemented (cloud) | Implemented (cloud) | Implemented (cloud) | Implemented (cloud) | Implemented (cloud) |
| calling / SMS | Unavailable | Unavailable | Unavailable | Planned | OS Restricted |
| camera / microphone.record | Planned | Planned | Planned | Planned | Planned |
| location / maps | Planned | Planned | Planned | Planned | Planned |
| social publish (auto-post) | Planned | Planned | Planned | Planned | OS Restricted |
| social.draft (write + copy + open; you tap Post) | Implemented | Planned | Planned | Planned | Planned |
| payment.execute / transfer | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable |
| cloud.manage | Planned | Planned | Planned | Planned | Planned |
| App Intents / Shortcuts | Unavailable | Planned | Unavailable | Unavailable | Planned |
| Android assistant | Unavailable | Unavailable | Unavailable | Planned | Unavailable |
| AccessibilityService | Unavailable | Unavailable | Unavailable | Planned (explicit, never bypass MFA) | OS Restricted |

Gmail and Google Calendar are **cloud connectors**, not device mailbox/calendar APIs. After a verified profile they run on the API for any OS. Contacts stay Planned.

Desktop rows marked Planned on macOS/Linux mean the shared Python agent exists but was not tested on those OSes in this milestone.

iOS cannot grant unrestricted control of other apps. Those actions return `CAPABILITY_RESTRICTED_BY_OS` when a runtime exists.
