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
    "ntdsutil",
    "mbkac",
}

BLOCKED_ARG_PATTERNS = (
    "rm -rf /",
    "rm -rf \\",
    "del /f /s /q",
    "format ",
    "mkfs",
    ":(){:|:&};:",
    "invoke-expression",
    "iex(",
    "downloadstring",
    "frombase64string",
    "set-executionpolicy unrestricted",
)


class TerminalDenied(ValueError):
    pass


def normalize_executable(executable: str) -> str:
    name = executable.strip().strip('"').replace("\\", "/").split("/")[-1]
    return name.lower()


def validate_command(executable: str, args: list[str] | None = None) -> None:
    if not executable or not executable.strip():
        raise TerminalDenied("Executable is required")
    if any(ch in executable for ch in ["|", "&", ";", "`", "\n"]):
        raise TerminalDenied("Shell metacharacters are not allowed in the executable")
    exe = normalize_executable(executable)
    if exe in BLOCKED_EXECUTABLES:
        raise TerminalDenied(f"Executable is blocked: {exe}")
    joined = " ".join(args or []).lower()
    for pattern in BLOCKED_ARG_PATTERNS:
        if pattern in joined:
            raise TerminalDenied("Command arguments match a blocked destructive pattern")
    if exe in {"cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
        lowered_args = [a.lower() for a in (args or [])]
        if any(flag in lowered_args for flag in ("/c", "-c", "-command", "-enc", "-encodedcommand")):
            blob = " ".join(lowered_args)
            for pattern in BLOCKED_ARG_PATTERNS:
                if pattern in blob:
                    raise TerminalDenied("Destructive shell command is blocked")
