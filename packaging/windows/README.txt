APPI for Windows — Desktop app
Created by MELIX STUDIOS

Double-click Appi.exe to open the Appi window (no Command Prompt).
It connects to your account on the live site.

Website
  Product site:  https://appi-project01.netlify.app
  Operator:      https://appi-project01.netlify.app/app
  Devices page:  https://appi-project01.netlify.app/device

Install
1. Unzip this folder anywhere.
2. Open the Appi folder (the one that contains Appi.exe).
3. Double-click Appi.exe (do not Run as administrator).
4. If prompted, paste a pairing code from Devices.
5. The Appi window opens the operator. Close it to keep Appi in the tray.

Optional CLI pair (if you skip the dialog):

   .\Appi.exe pair --code 123456

Optional autostart at login:

   .\Appi.exe autostart on

Requires Microsoft Edge WebView2 (preinstalled on modern Windows).
A local .env next to Appi.exe points at the production API.
Do not put API keys in this folder.

Voice: say Appi, wait for the greeting, then speak your command.
Ctrl+Shift+A if the wake word misses.
