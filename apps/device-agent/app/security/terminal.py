BLOCKED_EXECUTABLES = {
    "format",
    "format.com",
    "diskpart",
    "diskpart.exe",
    "reg",
    "reg.exe",
    "shutdown",
    "shutdown.exe",
    "bcdedit",
    "bcdedit.exe",
    "cipher",
    "cipher.exe",
    "vssadmin",
    "vssadmin.exe",
    "takeown",
    "takeown.exe",
}


class TerminalDenied(ValueError):
    pass


def validate_command(executable: str, args: list[str] | None = None) -> None:
    if not executable or not str(executable).strip():
        raise TerminalDenied("Executable is required")
    if any(ch in executable for ch in ["|", "&", ";", "`", "\n"]):
        raise TerminalDenied("Shell metacharacters are not allowed in the executable")
    name = executable.replace("\\", "/").split("/")[-1].lower()
    if name in BLOCKED_EXECUTABLES:
        raise TerminalDenied(f"Executable is blocked: {name}")
    blob = " ".join(args or []).lower()
    for pattern in ("rm -rf /", "del /f /s /q", "format ", "invoke-expression", "frombase64string"):
        if pattern in blob:
            raise TerminalDenied("Destructive command is blocked")
