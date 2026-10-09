from app.models.enums import ALLOWED_TRANSITIONS, TaskStatus


class InvalidStateTransition(ValueError):
    pass


def can_transition(current: TaskStatus | str, target: TaskStatus | str) -> bool:
    current_status = TaskStatus(current)
    target_status = TaskStatus(target)
    return target_status in ALLOWED_TRANSITIONS[current_status]


def transition(current: TaskStatus | str, target: TaskStatus | str) -> TaskStatus:
    current_status = TaskStatus(current)
    target_status = TaskStatus(target)
    if target_status == TaskStatus.COMPLETED:
        raise InvalidStateTransition("COMPLETED is only allowed through mark_completed()")
    if not can_transition(current_status, target_status):
        raise InvalidStateTransition(f"Cannot transition {current_status.value} -> {target_status.value}")
    return target_status


def mark_completed(current: TaskStatus | str, *, verified: bool) -> TaskStatus:
    current_status = TaskStatus(current)
    if not verified:
        raise InvalidStateTransition("A task cannot be COMPLETED until verification succeeds")
    if not can_transition(current_status, TaskStatus.COMPLETED):
        raise InvalidStateTransition(f"Cannot complete from {current_status.value}")
    return TaskStatus.COMPLETED
