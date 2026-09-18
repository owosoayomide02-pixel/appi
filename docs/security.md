# Security

Appi is designed to become powerful **without** unrestricted device or account control. Every capability is explicit, reviewable, revocable, and gated.

## Guardian

Every action follows:

```
AI proposes action
      → kill switch?
      → financial connector connected? (payments/transfers)
      → capability available on this runtime?
            NO  → CAPABILITY_UNAVAILABLE / CONNECTOR_NOT_CONNECTED / CAPABILITY_RESTRICTED_BY_OS
            YES → ALLOW / ASK / BLOCK
      → runtime executes
      → verifier
      → audit
```

The model cannot bypass Guardian. Voice cannot bypass Guardian. Kill switch is checked first.

| Class | Default |
| --- | --- |
| Low risk (read, search, tests, inspect, `social.draft`, `system.info`) | ALLOW |
| Medium risk (writes, installs, processes, `app.launch`, `payment.prepare`) | ASK |
| High risk (delete, publish, send, `payment.execute`, calls) | ALWAYS ASK |
| No financial connector | CONNECTOR_NOT_CONNECTED |
| Unimplemented / missing runtime support | CAPABILITY_UNAVAILABLE |
| OS will not expose the API | CAPABILITY_RESTRICTED_BY_OS |
| Forbidden (bypass security, exfiltrate secrets, hidden actions, denied-again) | BLOCK |

Voice is not strong authentication. Transfers still need PIN / biometric / device / passkey after a real connector exists.

Capabilities ≠ permissions. `filesystem.delete` may be supported and still always ASK.

Financial actions are split: `payment.prepare` vs `payment.execute`. Amount limits, service limits, and biometric-required flags are modeled. **No payment connector is live.** Card numbers and banking passwords are never stored or sent to the model.

Social actions are split: draft / approve / publish / send / schedule / delete. Publishing and sending are higher risk than drafting. **No social publisher is live.**

## Kill switch

`STOP APPI` is below the AI layer. It cancels tasks, blocks new tool execution, revokes temporary permissions, disconnects runtimes, stops browser automation and tracked processes, and writes an audit event.

## Filesystem

Approved folders only. Drive roots, Windows, Program Files, and AppData are blocked at grant time. Path traversal is rejected on the API and the runtime.

## Terminal

Structured `{ executable, args, cwd, timeout }`. No `os.system`.

## Browser

Playwright on desktop runtimes only. Unknown domains ASK. No CAPTCHA/MFA bypass.

## Device runtimes

Android and iOS placeholders do not access OS APIs. They return `CAPABILITY_UNAVAILABLE`. Desktop UI automation, contacts, calendar, calls, camera, microphone recording, and payments are not implemented as live connectors.

Pairing stores a token hash only. Devices can be revoked from the dashboard.

Wake-word audio stays on-device. Raw microphone audio is not stored. Cloud STT is not used to detect “Appi”.

## Secrets and injection

Unchanged: bcrypt passwords, encrypted vault handles, redaction, untrusted-content wrappers.
