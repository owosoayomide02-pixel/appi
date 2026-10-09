from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import sys
import webbrowser
from pathlib import Path
from typing import Any

import httpx
import websockets

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    REPO_ROOT = Path(sys._MEIPASS)
else:
    REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "apps" / "runtime-core"))
sys.path.insert(0, str(REPO_ROOT / "services" / "voice"))

from appi_runtime_core.activity import last_input_idle_seconds, should_ask_before_foreground
from appi_runtime_core.autostart import disable_autostart, enable_autostart
from appi_runtime_core.errors import CAPABILITY_UNAVAILABLE, CAPABILITY_RESTRICTED_BY_OS
from appi_runtime_core.execution_mode import ExecutionMode, mode_for_tool
from appi_runtime_core.ipc import LocalIpc

from app.browser import playwright_tools
from app.config import settings
from app.desktop import apps as desktop_apps
from app.desktop import clipboard as desktop_clipboard
from app.desktop import system as desktop_system
from app.desktop.tray import start_tray
from app.files import ops as file_ops
from app.identity import default_name, load_identity, save_identity
from app.runtime_profile import RUNTIME_VERSION, desktop_capabilities, detect_platform, os_label
from app.terminal import runner as terminal_runner
from app.tools import project as project_tools
from app.voice_prefs import load_voice_prefs, save_voice_prefs

KILLED = False
PAUSED = False
MUTED = False
VOICE_ENABLED = False
STOP = False
ASK_WHEN_BUSY = False
VOICE_PIPELINE = None
EVENT_LOOP: asyncio.AbstractEventLoop | None = None


async def _stop_local_work() -> None:
    await terminal_runner.stop_all()
    await playwright_tools.close()


def _unavailable(tool: str, platform: str, code: str = CAPABILITY_UNAVAILABLE) -> dict[str, Any]:
    return {
        "success": False,
        "error": f"{code}: {tool}",
        "error_code": code,
        "platform": platform,
        "verification_required": True,
    }


async def dispatch(tool: str, payload: dict[str, Any], allowed_roots: list[str]) -> dict[str, Any]:
    platform = detect_platform()
    if KILLED:
        return {
            "success": False,
            "error": "Kill switch is active",
            "error_code": "KILL_SWITCH",
            "platform": platform,
            "verification_required": True,
        }
    if PAUSED:
        return {
            "success": False,
            "error": "Agent is paused",
            "error_code": "USER_APPROVAL_REQUIRED",
            "platform": platform,
            "verification_required": True,
        }
    mode = mode_for_tool(tool)
    if ASK_WHEN_BUSY and mode == ExecutionMode.FOREGROUND_REQUIRED and should_ask_before_foreground() and not payload.get("user_confirmed_foreground"):
        snap = last_input_idle_seconds()
        return {
            "success": False,
            "error": "I need to use the foreground to complete this task. Continue now?",
            "error_code": "USER_APPROVAL_REQUIRED",
            "platform": platform,
            "execution_mode": mode.value,
            "user_busy": snap.busy,
            "idle_seconds": snap.idle_seconds,
            "verification_required": True,
        }
    if tool.startswith("files.") or tool.startswith("filesystem."):
        mapped = {
            "filesystem.read": "files.read_file",
            "filesystem.write": "files.write_file",
            "filesystem.delete": "files.delete_file",
            "files.search": "files.search",
        }.get(tool, tool)
        result = file_ops.execute(mapped, payload, allowed_roots)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool.startswith("terminal.") or tool.startswith("process.") or tool in {"project.run_tests", "project.run_build"}:
        mapped = {
            "terminal.execute": "terminal.run_command",
            "process.start": "terminal.start_process",
            "process.stop": "terminal.stop_process",
        }.get(tool, tool)
        result = await terminal_runner.execute(mapped, payload, allowed_roots)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool.startswith("browser."):
        mapped = {
            "browser.navigate": "browser.open_url",
            "browser.read": "browser.read_page",
            "browser.upload": "browser.upload_file",
            "browser.download": "browser.download_file",
            "browser.search": "browser.open_url",
        }.get(tool, tool)
        if mapped == "browser.open_url" and not payload.get("url") and payload.get("query"):
            payload = {**payload, "url": desktop_apps.search_url(str(payload["query"]))}
        result = await playwright_tools.execute(mapped, payload)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool.startswith("project."):
        result = project_tools.execute(tool, payload, allowed_roots)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool in {"app.launch", "desktop.launch_app", "app.focus"}:
        if tool == "app.focus":
            return _unavailable(tool, platform, CAPABILITY_RESTRICTED_BY_OS if platform != "windows" else CAPABILITY_UNAVAILABLE)
        result = desktop_apps.launch(payload)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool == "social.draft":
        from app.desktop.handoff import draft_post

        result = draft_post(payload)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool == "access.prepare":
        from app.desktop.handoff import prepare_access

        result = prepare_access(payload)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool in {"access.login", "browser.login_vault"}:
        result = await playwright_tools.login_with_vault(payload)
        result["platform"] = platform
        result["execution_mode"] = mode.value
        return result
    if tool == "social.publish":
        return _unavailable(tool, platform)
    if tool == "system.info":
        result = desktop_system.info()
        result["platform"] = platform
        result["execution_mode"] = ExecutionMode.BACKGROUND_SAFE.value
        return result
    if tool == "clipboard.read":
        result = desktop_clipboard.read()
        result["platform"] = platform
        return result
    if tool == "clipboard.write":
        result = desktop_clipboard.write(str(payload.get("text") or payload.get("content") or ""))
        result["platform"] = platform
        return result
    if tool in {
        "system.lock",
        "system.shutdown",
        "system.restart",
        "system.sleep",
        "system.volume",
        "system.brightness",
        "system.wifi",
        "system.bluetooth",
        "app.close",
        "app.install",
        "app.uninstall",
        "notification.send",
    }:
        return _unavailable(tool, platform)
    return _unavailable(tool, platform)


def _heartbeat_payload(device_id: str) -> dict[str, Any]:
    platform = detect_platform()
    snap = last_input_idle_seconds()
    prefs = load_voice_prefs()
    inventory: dict[str, Any] = {"voices": [], "recognizers": []}
    try:
        from appi_voice.windows_sapi import speech_inventory

        inventory = speech_inventory()
    except Exception:
        pass
    return {
        "type": "heartbeat",
        "device_id": device_id,
        "platform": platform,
        "runtime_version": RUNTIME_VERSION,
        "capabilities": desktop_capabilities(platform),
        "voice": {
            "enabled": VOICE_ENABLED,
            "muted": MUTED,
            "tts_voice": prefs.get("tts_voice") or "",
            "tts_gender": prefs.get("tts_gender") or "",
            "culture": prefs.get("culture") or "",
            "min_confidence": prefs.get("min_confidence") or 0.45,
            "voices": inventory.get("voices") or [],
            "recognizers": inventory.get("recognizers") or [],
        },
        "idle_seconds": snap.idle_seconds,
        "paused": PAUSED,
        "killed": KILLED,
    }


async def pair(code: str) -> None:
    platform = detect_platform()
    url = settings.api_base_url.rstrip("/") + "/api/v1/devices/pair/complete"
    body = {
        "pairing_code": code,
        "name": default_name() or socket.gethostname(),
        "os": os_label(platform),
        "platform": platform,
        "runtime_version": RUNTIME_VERSION,
        "capabilities": desktop_capabilities(platform),
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError:
        print(f"Could not reach the Appi API at {settings.api_base_url}.")
        print("Make sure .env next to Appi.exe has DEVICE_AGENT_API_URL=https://appi-6kfe.onrender.com")
        raise RuntimeError(f"Could not reach the Appi API at {settings.api_base_url}") from None
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail") or ""
        except Exception:
            detail = exc.response.text[:200]
        print(f"Pairing failed ({exc.response.status_code}): {detail or exc}")
        print("Open https://appi-project01.netlify.app/device , create a fresh code, and try again.")
        raise RuntimeError(detail or f"Pairing failed ({exc.response.status_code})") from None
    save_identity(
        {
            "device_id": data["device_id"],
            "device_token": data["device_token"],
            "user_id": data.get("user_id"),
            "display_name": data.get("display_name") or "",
        }
    )
    print(f"Paired as {data['device_id']} ({platform} runtime {RUNTIME_VERSION})")
    print(f"Next: run Appi.exe, then open {settings.dashboard_url}")


async def _submit_voice_command(text: str) -> dict[str, Any]:
    identity = load_identity()
    if not identity:
        return {"ok": False, "error": "DEVICE_OFFLINE"}
    api = settings.api_base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{api}/api/v1/runtime/voice-command",
            params={"token": identity["device_token"]},
            json={"text": text, "source": "voice"},
        )
        if response.status_code >= 400:
            return {"ok": False, "error": response.text[:400]}
        data = response.json()
        task_id = data.get("id")
        for _ in range(40):
            await asyncio.sleep(1.5)
            poll = await client.get(f"{api}/api/v1/runtime/task/{task_id}", params={"token": identity["device_token"]})
            if poll.status_code >= 400:
                continue
            body = poll.json()
            status = body.get("status")
            if status in {"COMPLETED", "FAILED", "CANCELLED", "BLOCKED", "WAITING_FOR_APPROVAL"}:
                return body
        return data


async def _pull_server_voice_prefs() -> None:
    identity = load_identity()
    if not identity:
        return
    api = settings.api_base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{api}/api/v1/runtime/voice-prefs",
                params={"token": identity["device_token"]},
            )
        if response.status_code >= 400:
            return
        payload = response.json()
        if not isinstance(payload, dict):
            return
        if payload.get("tts_voice") or payload.get("culture") or payload.get("tts_gender"):
            prefs = save_voice_prefs(payload)
            if VOICE_PIPELINE is not None:
                VOICE_PIPELINE.apply_prefs(prefs)
    except Exception:
        return


async def _user_display_name() -> str:
    identity = load_identity() or {}
    name = str(identity.get("display_name") or "").strip()
    if name:
        return name
    api = settings.api_base_url.rstrip("/")
    token = identity.get("device_token")
    if not token:
        return ""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(f"{api}/api/v1/runtime/whoami", params={"token": token})
        if response.status_code >= 400:
            return ""
        name = str(response.json().get("display_name") or "").strip()
        if name:
            identity["display_name"] = name
            save_identity(identity)
        return name
    except Exception:
        return ""


async def _voice_loop() -> None:
    global VOICE_PIPELINE
    from appi_voice.assistant import follow_up, greeting, local_reply, sanitize_heard
    from appi_voice.pipeline import VoicePipeline
    from appi_voice.states import MicState
    from app.desktop.apps import write_voice_commands

    try:
        os.environ["APPI_VOICE_COMMANDS"] = str(write_voice_commands())
    except Exception:
        pass

    pipeline = VoicePipeline()
    pipeline.apply_prefs(load_voice_prefs())
    VOICE_PIPELINE = pipeline
    await _pull_server_voice_prefs()
    name = await _user_display_name()
    pipeline.config.ack_text = greeting(name)
    pipeline.config.done_text = "Done."
    voice_label = pipeline.config.tts_voice or pipeline.config.tts_gender or "Windows default"
    culture_label = pipeline.config.culture or "Windows default"
    print(f"Voice ready. Wake word: {pipeline.config.wake_word}. Fallback hotkey: Ctrl+Shift+A")
    print(f"Assistant greeting uses: {name or 'there'}")
    print(f"Speaking voice: {voice_label}. Recognition language: {culture_label}")
    print(f"Microphone state: {pipeline.status.mic_state.value}")
    print("Say Appi, wait for the greeting, then a short command such as open Chrome.")
    try:
        from appi_voice.quantum_core import set_viz_state, start_quantum_core

        if start_quantum_core():
            print("Quantum Core visualizer online (cyan / iris).")
        else:
            print("Quantum Core skipped (pip install PyQt6 pyaudio numpy).")

            def set_viz_state(_s: str = "idle") -> None:
                return None
    except Exception as exc:
        print(f"Quantum Core unavailable: {exc}")

        def set_viz_state(_s: str = "idle") -> None:
            return None
    while not STOP:
        if MUTED or KILLED or PAUSED or pipeline.status.mic_state == MicState.OFF:
            set_viz_state("idle")
            await asyncio.sleep(0.4)
            continue
        pipeline.config.ack_text = greeting(name or await _user_display_name())
        set_viz_state("listening")
        woke = await asyncio.to_thread(pipeline.wait_for_wake, 8.0)
        if not woke:
            continue
        set_viz_state("speaking")
        await asyncio.to_thread(pipeline.acknowledge)
        set_viz_state("listening")
        command = sanitize_heard(await asyncio.to_thread(pipeline.capture_command, 10.0))
        heard = pipeline.last_recognition or {}
        if not command:
            conf = heard.get("confidence")
            raw = sanitize_heard(str(heard.get("text") or ""))
            if raw:
                print(f"Ignored low-confidence speech ({conf}): {raw}")
            else:
                print("No command heard after greeting.")
            set_viz_state("speaking")
            await asyncio.to_thread(pipeline.respond, "Sorry, say that again.")
            set_viz_state("idle")
            continue
        print(f"Voice command ({heard.get('confidence', '?')} {heard.get('source', '')}): {command}")
        local = local_reply(command, name)
        if local:
            set_viz_state("speaking")
            await asyncio.to_thread(pipeline.respond, local)
            set_viz_state("idle")
            continue
        set_viz_state("thinking")
        result = await _submit_voice_command(command)
        status = result.get("status")
        set_viz_state("speaking")
        if status == "WAITING_FOR_APPROVAL":
            await asyncio.to_thread(pipeline.respond, "I need your approval on the dashboard.")
        elif status == "COMPLETED":
            summary = result.get("result_summary") or pipeline.config.done_text
            await asyncio.to_thread(pipeline.respond, f"{summary} {follow_up(name)}")
        elif result.get("error_message") or result.get("error"):
            await asyncio.to_thread(pipeline.respond, f"I could not complete that. {follow_up(name)}")
        else:
            await asyncio.to_thread(pipeline.respond, "Working on it.")
        set_viz_state("idle")


async def _session() -> None:
    global KILLED
    identity = load_identity()
    if not identity:
        print("Device is not paired. Run: python -m app.main pair --code 123456")
        sys.exit(1)
    api = settings.api_base_url.rstrip("/")
    ws_url = api.replace("http://", "ws://").replace("https://", "wss://") + f"/api/v1/ws/device?token={identity['device_token']}"
    print(f"Connecting to {api} as {identity['device_id']} ({detect_platform()})")
    async with websockets.connect(ws_url, ping_interval=20) as ws:
        print("Device runtime online")
        await _pull_server_voice_prefs()
        await ws.send(json.dumps(_heartbeat_payload(identity["device_id"])))

        async def heartbeats() -> None:
            while True:
                await asyncio.sleep(15)
                try:
                    await ws.send(json.dumps(_heartbeat_payload(identity["device_id"])))
                except Exception:
                    return

        beat = asyncio.create_task(heartbeats())
        try:
            while True:
                raw = await ws.recv()
                message = json.loads(raw)
                if message.get("type") == "kill_switch":
                    KILLED = bool(message.get("active"))
                    terminal_runner.set_killed(KILLED)
                    playwright_tools.set_killed(KILLED)
                    if KILLED:
                        await terminal_runner.stop_all()
                        await playwright_tools.close()
                        print("Kill switch received — all local operations stopped")
                    continue
                if message.get("type") == "voice.prefs":
                    prefs = save_voice_prefs(
                        {
                            "tts_voice": message.get("tts_voice") or "",
                            "tts_gender": message.get("tts_gender") or "",
                            "culture": message.get("culture") or "",
                            "min_confidence": message.get("min_confidence"),
                        }
                    )
                    if VOICE_PIPELINE is not None:
                        VOICE_PIPELINE.apply_prefs(prefs)
                    print(f"Voice preference updated: {prefs.get('tts_voice') or 'default'} / {prefs.get('culture') or 'default'}")
                    continue
                if message.get("type") != "tool.request":
                    continue
                request = message.get("payload") or {}
                tool = request.get("tool")
                result = await dispatch(tool, request.get("input") or {}, request.get("allowed_roots") or [])
                await ws.send(
                    json.dumps(
                        {
                            "type": "tool.result",
                            "task_id": request.get("task_id"),
                            "step_id": request.get("step_id"),
                            "tool": tool,
                            "payload": result,
                        }
                    )
                )
        finally:
            beat.cancel()


async def run_agent(*, reconnect: bool = False, voice: bool = False, ask_when_busy: bool = False) -> None:
    global VOICE_ENABLED, STOP, ASK_WHEN_BUSY, EVENT_LOOP
    VOICE_ENABLED = voice
    ASK_WHEN_BUSY = ask_when_busy
    EVENT_LOOP = asyncio.get_running_loop()
    voice_task = asyncio.create_task(_voice_loop()) if voice else None

    async def ipc_handler(message: dict[str, Any]) -> dict[str, Any]:
        global MUTED, PAUSED, STOP
        cmd = message.get("cmd")
        if cmd == "status":
            return {"ok": True, "killed": KILLED, "paused": PAUSED, "muted": MUTED, "voice": VOICE_ENABLED}
        if cmd == "mute":
            MUTED = True
            return {"ok": True, "muted": True}
        if cmd == "unmute":
            MUTED = False
            return {"ok": True, "muted": False}
        if cmd == "pause":
            PAUSED = True
            return {"ok": True, "paused": True}
        if cmd == "resume":
            PAUSED = False
            return {"ok": True, "paused": False}
        if cmd == "stop_tasks":
            await terminal_runner.stop_all()
            await playwright_tools.close()
            return {"ok": True}
        if cmd == "exit":
            STOP = True
            return {"ok": True}
        if cmd == "open":
            try:
                from app.desktop.app_window import request_show

                shown = request_show()
            except Exception:
                shown = False
            if not shown and not os.environ.get("APPI_DESKTOP"):
                webbrowser.open(settings.dashboard_url)
                shown = True
            return {"ok": True, "shown": shown}
        return {"ok": False, "error": "unknown"}

    ipc = LocalIpc(ipc_handler)
    try:
        await ipc.start()
        print(f"Local IPC on 127.0.0.1:47821")
    except OSError:
        print("Local IPC port busy — runtime continues without IPC")
        ipc = None

    try:
        refused_hint = False
        delay = 5
        while not STOP:
            try:
                await _session()
                delay = 5
            except Exception as exc:
                text = str(exc)
                refused = "1225" in text or "refused" in text.lower() or "10061" in text
                if refused:
                    if not refused_hint:
                        print(f"The Appi API is not running on {settings.api_base_url}.")
                        if not os.environ.get("APPI_DESKTOP"):
                            print("Keep this window. Start the brain from the repo root:")
                            print("  .\\scripts\\dev.ps1 -Api")
                            print("  # or: .\\scripts\\preview-windows.ps1")
                        refused_hint = True
                    else:
                        print(f"Still waiting for the API on {settings.api_base_url} …")
                    delay = min(30, delay + 5)
                else:
                    print(f"Runtime disconnected: {exc}")
                    refused_hint = False
                    delay = 5
                if not reconnect:
                    raise
                await asyncio.sleep(delay)
                print("Reconnecting…")
    finally:
        STOP = True
        if voice_task:
            voice_task.cancel()
        if ipc:
            await ipc.stop()


def main() -> None:
    if getattr(sys, "frozen", False) and len(sys.argv) == 1:
        sys.argv.append("serve")
    parser = argparse.ArgumentParser(description="Appi desktop device runtime")
    sub = parser.add_subparsers(dest="cmd")
    pair_p = sub.add_parser("pair")
    pair_p.add_argument("--code", required=True)
    sub.add_parser("run")
    serve_p = sub.add_parser("serve", help="Background runtime with voice. Dashboard may be closed.")
    serve_p.add_argument("--voice", action="store_true", help="Deprecated: voice is on by default")
    serve_p.add_argument("--no-voice", action="store_true", help="Disable the wake-word assistant")
    serve_p.add_argument("--no-tray", action="store_true")
    auto = sub.add_parser("autostart")
    auto.add_argument("action", choices=["on", "off"])
    sub.add_parser("open", help="Start Appi like a desktop app (API + dashboard + assistant, no consoles)")
    sub.add_parser("install", help="Install Appi for this Windows user (no Administrator)")
    sub.add_parser("uninstall", help="Remove the per-user Appi install")
    vault_p = sub.add_parser("vault", help="Save or clear the local login email/password (never sent to the model)")
    vault_p.add_argument("action", choices=["set", "status", "clear"])
    vault_p.add_argument("--email", default="")
    vault_p.add_argument("--password", default="")
    voice = sub.add_parser("voice-check", help="Probe local TTS, mic, and Appi grammar; optionally speak the greeting")
    voice.add_argument("--speak", action="store_true", help="Speak the assistant greeting using Windows SAPI")
    sub.add_parser("voice-voices", help="List installed Windows TTS voices and recognizers")
    voice_set = sub.add_parser("voice-set", help="Save TTS voice and recognition language preference")
    voice_set.add_argument("--voice", default="", help="Installed SAPI voice name, e.g. Microsoft Zira Desktop")
    voice_set.add_argument("--gender", default="", help="Female or Male if you do not pick a named voice")
    voice_set.add_argument("--culture", default="", help="Recognition language, e.g. en-GB or en-US")
    args = parser.parse_args()
    if args.cmd == "pair":
        try:
            asyncio.run(pair(args.code))
        except RuntimeError:
            raise SystemExit(1) from None
        return
    if args.cmd == "open":
        from app.launcher import main as open_appi

        open_appi()
        return
    if args.cmd == "install":
        from app.install_windows import install, running_as_admin

        if running_as_admin():
            print("Do not run Appi as Administrator. Install it for your normal Windows account.")
        info = install()
        print(f"Installed for this user: {info.get('exe')}")
        if info.get("desktop"):
            print(f"Desktop shortcut: {info['desktop']}")
        if info.get("start_menu") or info.get("shortcut"):
            print(f"Start Menu: {info.get('start_menu') or info.get('shortcut')}")
        if info.get("autostart"):
            print(f"Starts at login: {info['autostart']}")
        print("Double-click Appi on the Desktop or search Appi in the Start Menu. No Command Prompt needed.")
        print(
            f"Pair from {settings.device_page_url} (six-digit code), "
            f"then open the operator at {settings.dashboard_url}."
        )
        return
    if args.cmd == "uninstall":
        from app.install_windows import uninstall

        uninstall()
        print("Appi per-user install removed.")
        return
    if args.cmd == "vault":
        from app import secrets_vault
        from getpass import getpass

        if args.action == "status":
            print(json.dumps(secrets_vault.status(), indent=2))
            return
        if args.action == "clear":
            secrets_vault.clear_login()
            print("Local login vault cleared.")
            return
        email = args.email or input("Email: ").strip()
        password = args.password or getpass("Password (stored only on this Windows account): ")
        print(json.dumps(secrets_vault.save_login(email, password), indent=2))
        print("Appi can use this to fill logins. It is never sent to the chat model. Banks and MFA stay with you.")
        return
    if args.cmd == "autostart":
        if args.action == "on":
            path = enable_autostart(REPO_ROOT)
            print(f"Autostart enabled: {path}")
        else:
            disable_autostart()
            print("Autostart removed")
        return
    if args.cmd == "voice-voices":
        from appi_voice.windows_sapi import speech_inventory

        print(json.dumps({"prefs": load_voice_prefs(), **speech_inventory()}, indent=2))
        return
    if args.cmd == "voice-set":
        prefs = save_voice_prefs({"tts_voice": args.voice, "tts_gender": args.gender, "culture": args.culture})
        print(json.dumps(prefs, indent=2))
        print("Restart serve for the new speaking voice and recognition language.")
        return
    if args.cmd == "voice-check":
        from appi_voice.pipeline import VoicePipeline

        pipeline = VoicePipeline()
        pipeline.apply_prefs(load_voice_prefs())
        report = pipeline.diagnose(speak_ack=bool(args.speak))
        print(json.dumps(report, indent=2))
        if not report["tts"].get("ok"):
            sys.exit(2)
        if not report["wake"].get("ok"):
            print("Wake-word grammar did not load. Ctrl+Shift+A remains the local fallback.")
            sys.exit(3)
        print("Voice check passed. Run: python -m app.main serve")
        print("Say Appi — Appi should greet you by name, then wait for a command.")
        return
    if args.cmd == "serve":
        def toggle_mute() -> None:
            global MUTED
            MUTED = not MUTED
            print(f"Microphone {'muted' if MUTED else 'listening'}")

        def toggle_pause() -> None:
            global PAUSED
            PAUSED = not PAUSED
            print(f"Agent {'paused' if PAUSED else 'resumed'}")

        def stop_tasks() -> None:
            if EVENT_LOOP is None:
                return
            asyncio.run_coroutine_threadsafe(_stop_local_work(), EVENT_LOOP)

        def exit_app() -> None:
            global STOP
            STOP = True
            try:
                from app.desktop.app_window import request_quit

                request_quit()
            except Exception:
                pass

        def open_app() -> None:
            try:
                from app.desktop.app_window import request_show

                if request_show():
                    return
            except Exception:
                pass
            if not os.environ.get("APPI_DESKTOP"):
                webbrowser.open(settings.dashboard_url)

        if not args.no_tray:
            start_tray(
                on_open=open_app,
                on_mute=toggle_mute,
                on_pause=toggle_pause,
                on_stop=stop_tasks,
                on_exit=exit_app,
            )
        print("Background assistant is running. Closing the dashboard will not stop this process.")
        try:
            from app.vault_prompt import prompt_if_empty
            from app.secrets_vault import status as vault_status

            if os.environ.get("APPI_SKIP_VAULT_PROMPT"):
                info = vault_status()
            else:
                info = prompt_if_empty()
            if info.get("saved"):
                print(f"Login vault ready for {info.get('email')} (password stays on this PC).")
            else:
                print("No login vault yet. Run: python -m app.main vault set")
                print(f"Vault status: {vault_status()}")
        except Exception as exc:
            print(f"Login vault prompt skipped: {exc}")
        if getattr(sys, "frozen", False):
            from app.install_windows import install, is_installed_copy, running_as_admin

            if running_as_admin():
                print("Warning: running as Administrator is not required and is not recommended.")
            if not is_installed_copy():
                try:
                    info = install()
                    print(f"Also installed for this user (no admin): {info.get('exe')}")
                except Exception as exc:
                    print(f"Per-user install skipped: {exc}")
        asyncio.run(run_agent(reconnect=True, voice=not args.no_voice, ask_when_busy=True))
        return
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
