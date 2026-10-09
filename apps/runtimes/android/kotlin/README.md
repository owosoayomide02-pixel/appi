# Android foreground service

Kotlin sources for a **notification-backed foreground service** live in `app/src/main`.

Build (requires Android Studio / Android SDK):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-android.ps1
```

The APK is a placeholder. It is not the user's selected Android assistant.

Rules that remain:

- AccessibilityService is not included
- No bypass of security dialogs or MFA
- Microphone / contacts / calendar stay behind explicit user grants later
