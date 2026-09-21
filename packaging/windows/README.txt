APPI for Windows
Created by MELIX STUDIOS

This folder is the Windows assistant (Appi.exe).
It pairs to your Appi account on the live site.

Website
  Product site:  https://appi-project01.netlify.app
  Operator:      https://appi-project01.netlify.app/app
  Devices page:  https://appi-project01.netlify.app/device

Install
1. Unzip this folder anywhere, for example Desktop\Appi.
2. Open the Appi folder (the one that contains Appi.exe).
3. Do not Run as administrator.
4. Open https://appi-project01.netlify.app/device , sign in, create a pairing code.
5. In PowerShell in this folder, pair once:

   .\Appi.exe pair --code 123456

6. Then start it normally:

   .\Appi.exe

Optional autostart at login:

   .\Appi.exe autostart on

Voice: say Appi, wait for the greeting, then speak your command.
Ctrl+Shift+A if the wake word misses.

A local .env next to Appi.exe points at the production API.
Do not put API keys in this folder.
