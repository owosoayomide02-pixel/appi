APPI for Windows
Created by MELIX STUDIOS

This folder is the Windows assistant (Appi.exe).
It pairs to the APPI website / operator running on this PC.

Website
  Product site:  http://localhost:3000
  Operator:      http://localhost:3000/app
  Devices page:  http://localhost:3000/device

Install
1. Unzip this folder anywhere, for example Desktop\Appi.
2. Make sure the APPI brain + website are running
   (from the APPI source folder: scripts\preview-windows.ps1
    or scripts\dev.ps1 -All).
3. Double-click Appi.exe. Do not Run as administrator.
4. Open http://localhost:3000/device and create a pairing code.
5. Pair once:

   Appi.exe pair --code 123456

6. Then start it normally:

   Appi.exe

Optional autostart at login:

   Appi.exe autostart on

Voice: say Appi, wait for the greeting, then speak your command.
Ctrl+Shift+A if the wake word misses.

This package does not include API keys.
Secrets live in the APPI source folder as .env (never ship real keys inside the exe).
Pair Appi.exe to your APPI account after the website is up.
