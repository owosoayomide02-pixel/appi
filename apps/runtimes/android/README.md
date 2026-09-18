# Android runtime (placeholder)

This milestone defines the capability surface only.

The Kotlin app in `kotlin/` can be packaged as a **debug APK** on a machine with Android Studio (JDK + SDK):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-android.ps1
```

The APK is a placeholder: launcher screen + foreground notification. It does **not** open files, Chrome, the terminal, or act as the phone assistant. Unsupported tools still return `CAPABILITY_UNAVAILABLE`.

This Windows laptop did not have the Android SDK, so the APK is not produced here until Android Studio is installed.

Future implementation must use explicit Android permissions and approved platform APIs:

- file access (Storage Access Framework / granted URIs)
- notifications
- contacts / calendar
- microphone / camera / location
- intents and deep links
- approved external app actions

Do not bypass the Android permission system.

The existing Flutter starter remains in `apps/mobile` (UI shell only).
