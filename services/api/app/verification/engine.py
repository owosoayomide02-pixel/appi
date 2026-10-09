from __future__ import annotations

from typing import Any


def verify_file_result(tool: str, payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("success"):
        return {"ok": False, "reason": result.get("error") or "Tool reported failure"}
    data = result.get("data") or {}
    if tool in {"files.create_file", "files.write_file"}:
        if not data.get("exists"):
            return {"ok": False, "reason": "File does not exist after write"}
        expected = payload.get("content")
        if expected is not None and data.get("content") is not None and data.get("content") != expected:
            return {"ok": False, "reason": "File content does not match what was written"}
    if tool == "files.read_file" and data.get("content") is None:
        return {"ok": False, "reason": "Read returned no content"}
    if tool == "files.list_directory" and "entries" not in data:
        return {"ok": False, "reason": "Directory listing missing entries"}
    if tool == "files.search" and "matches" not in data:
        return {"ok": False, "reason": "Search returned no match list"}
    if tool == "files.delete_file" and data.get("exists") is True:
        return {"ok": False, "reason": "File still exists after delete"}
    return {"ok": True, "reason": "File action verified"}


def verify_process_result(tool: str, result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("success"):
        return {"ok": False, "reason": result.get("error") or "Process tool failed"}
    data = result.get("data") or {}
    if tool == "terminal.start_process":
        if not data.get("running") and not data.get("pid"):
            return {"ok": False, "reason": "Process does not appear to be running"}
        health = data.get("health")
        if health is False:
            return {"ok": False, "reason": "Local health check failed"}
    if tool == "terminal.stop_process" and data.get("running") is True:
        return {"ok": False, "reason": "Process still running after stop"}
    if tool == "terminal.run_command" and result.get("exit_code") not in (0, None):
        return {"ok": False, "reason": f"Command exited {result.get('exit_code')}"}
    return {"ok": True, "reason": "Process action verified"}


def verify_browser_result(tool: str, payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("success"):
        return {"ok": False, "reason": result.get("error") or "Browser tool failed"}
    data = result.get("data") or {}
    if data.get("mfa_required") or data.get("captcha_required"):
        return {"ok": False, "reason": "Paused: MFA or CAPTCHA requires the user"}
    expected = payload.get("expect_contains") or payload.get("expected")
    if expected and expected not in (data.get("text") or data.get("url") or ""):
        return {"ok": False, "reason": "Expected page content was not found"}
    if tool == "browser.open_url" and payload.get("url"):
        current = (data.get("url") or "").rstrip("/")
        requested = payload["url"].rstrip("/")
        if current and requested not in current and current not in requested:
            return {"ok": False, "reason": f"Browser URL is {current}, expected {requested}"}
    return {"ok": True, "reason": "Browser action verified"}


def verify_tool(tool: str, payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    if tool.startswith("files."):
        return verify_file_result(tool, payload, result)
    if tool.startswith("terminal.") or tool in {"project.run_tests", "project.run_build"}:
        return verify_process_result(tool, result)
    if tool.startswith("browser."):
        return verify_browser_result(tool, payload, result)
    if tool in {"app.launch", "desktop.launch_app"}:
        if not result.get("success"):
            return {"ok": False, "reason": result.get("error") or "Launch failed"}
        data = result.get("data") or {}
        if not data.get("launched") and not data.get("opened"):
            return {"ok": False, "reason": "Application did not report launched"}
        return {"ok": True, "reason": "Application launch verified"}
    if tool in {"social.draft", "access.prepare", "access.login"}:
        if not result.get("success"):
            return {"ok": False, "reason": result.get("error") or "Handoff failed"}
        data = result.get("data") or {}
        if data.get("published") is True:
            return {"ok": False, "reason": "Appi must not publish for you"}
        if "password" in data and data.get("password"):
            return {"ok": False, "reason": "Password leaked into the tool result"}
        if tool == "social.draft" and not data.get("drafted"):
            return {"ok": False, "reason": "Post was not drafted"}
        return {"ok": True, "reason": "Prepared for you to finish"}
    if tool == "system.info":
        if not result.get("success") or not (result.get("data") or {}).get("platform"):
            return {"ok": False, "reason": "System info missing"}
        return {"ok": True, "reason": "System info verified"}
    if tool.startswith("github."):
        if not result.get("success"):
            return {"ok": False, "reason": result.get("error") or "GitHub request failed"}
        data = result.get("data") or {}
        if tool == "github.user" and not data.get("login"):
            return {"ok": False, "reason": "GitHub user missing login"}
        if tool == "github.repos" and "repos" not in data:
            return {"ok": False, "reason": "GitHub repo list missing"}
        return {"ok": True, "reason": "GitHub action verified"}
    if tool.startswith("email.") or tool.startswith("gmail."):
        if not result.get("success"):
            return {"ok": False, "reason": result.get("error") or "Gmail request failed"}
        data = result.get("data") or {}
        if tool in {"email.read", "email.search"} and "messages" not in data and not data.get("id"):
            return {"ok": False, "reason": "Gmail result missing messages"}
        if tool == "email.draft" and not data.get("draft_id"):
            return {"ok": False, "reason": "Gmail draft missing id"}
        if tool == "email.send" and not data.get("id"):
            return {"ok": False, "reason": "Gmail send missing id"}
        if tool == "gmail.profile" and not data.get("account") and not data.get("email"):
            return {"ok": False, "reason": "Gmail profile missing account"}
        return {"ok": True, "reason": "Gmail action verified"}
    if tool.startswith("calendar."):
        if not result.get("success"):
            return {"ok": False, "reason": result.get("error") or "Calendar request failed"}
        data = result.get("data") or {}
        if tool == "calendar.read" and "events" not in data:
            return {"ok": False, "reason": "Calendar result missing events"}
        if tool in {"calendar.write", "calendar.create"} and not data.get("id"):
            return {"ok": False, "reason": "Calendar event missing id"}
        return {"ok": True, "reason": "Calendar action verified"}
    if not result.get("success"):
        return {"ok": False, "reason": result.get("error") or "Tool failed"}
    return {"ok": True, "reason": "Tool reported success and passed generic verification"}
