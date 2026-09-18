# iOS runtime (placeholder)

iPhone app sources: `apps/runtimes/ios/AppiIOS/`.

On a Mac with Xcode:

```bash
bash scripts/setup-ios.sh
```

That builds a **simulator** `.app`. A signed `.ipa` for a physical iPhone needs an Apple Developer account. This Windows laptop cannot compile iOS.

The app tells the user honestly: it is not Siri, and it cannot control other iPhone apps (`CAPABILITY_RESTRICTED_BY_OS`).

Future work must use approved Apple APIs only:

- App Intents
- Shortcuts integrations
- files the user exposes to Appi
- contacts, calendar, microphone, camera, location, notifications
- deep links

Do not assume unrestricted access to other iOS apps. Everything unimplemented returns `CAPABILITY_UNAVAILABLE`.
