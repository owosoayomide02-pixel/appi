from enum import Enum


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class StepStatus(str, Enum):
    PENDING = "pending"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RUNNING = "running"
    VERIFYING = "verifying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FORBIDDEN = "forbidden"


class PermissionDecision(str, Enum):
    ALLOW = "ALLOW"
    ASK = "ASK"
    BLOCK = "BLOCK"


class PermissionKind(str, Enum):
    ONE_TIME = "one_time"
    SESSION = "session"
    TIME_LIMITED = "time_limited"
    PERMANENT = "permanent"
    AMOUNT_LIMITED = "amount_limited"
    RESOURCE_LIMITED = "resource_limited"


class PermissionRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED_ONCE = "approved_once"
    APPROVED_TASK = "approved_task"
    APPROVED_SIMILAR = "approved_similar"
    DENIED = "denied"
    EXPIRED = "expired"


class MemoryKind(str, Enum):
    WORKING = "working"
    PROJECT = "project"
    PREFERENCE = "preference"
    SECURE = "secure"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    PAIRING = "pairing"
    REVOKED = "revoked"


class ConnectionStatus(str, Enum):
    NOT_CONNECTED = "not_connected"
    CONNECTED = "connected"
    PERMISSION_REQUIRED = "permission_required"
    UNSUPPORTED = "unsupported"


class NotificationType(str, Enum):
    APPROVAL_REQUESTED = "approval_requested"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    AGENT_DISCONNECTED = "agent_disconnected"
    SECURITY_WARNING = "security_warning"
    TOOL_UNAVAILABLE = "tool_unavailable"
    KILL_SWITCH = "kill_switch"


TERMINAL_STATUSES = {
    TaskStatus.COMPLETED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
    TaskStatus.BLOCKED,
}

ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {
        TaskStatus.PLANNING,
        TaskStatus.CANCELLED,
        TaskStatus.BLOCKED,
    },
    TaskStatus.PLANNING: {
        TaskStatus.WAITING_FOR_APPROVAL,
        TaskStatus.RUNNING,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.BLOCKED,
    },
    TaskStatus.WAITING_FOR_APPROVAL: {
        TaskStatus.RUNNING,
        TaskStatus.PLANNING,
        TaskStatus.CANCELLED,
        TaskStatus.BLOCKED,
        TaskStatus.FAILED,
    },
    TaskStatus.RUNNING: {
        TaskStatus.VERIFYING,
        TaskStatus.WAITING_FOR_APPROVAL,
        TaskStatus.PLANNING,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.BLOCKED,
    },
    TaskStatus.VERIFYING: {
        TaskStatus.COMPLETED,
        TaskStatus.RUNNING,
        TaskStatus.PLANNING,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.BLOCKED,
    },
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: {TaskStatus.PLANNING, TaskStatus.CANCELLED},
    TaskStatus.CANCELLED: set(),
    TaskStatus.BLOCKED: set(),
}
