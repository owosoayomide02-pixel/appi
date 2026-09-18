from app.state.machine import InvalidStateTransition, mark_completed, transition
from app.models.enums import TaskStatus
import pytest


def test_created_to_planning():
    assert transition(TaskStatus.CREATED, TaskStatus.PLANNING) == TaskStatus.PLANNING


def test_cannot_skip_to_completed():
    with pytest.raises(InvalidStateTransition):
        transition(TaskStatus.CREATED, TaskStatus.COMPLETED)


def test_cannot_complete_without_verification():
    with pytest.raises(InvalidStateTransition):
        mark_completed(TaskStatus.VERIFYING, verified=False)


def test_complete_after_verify():
    assert mark_completed(TaskStatus.VERIFYING, verified=True) == TaskStatus.COMPLETED


def test_running_can_return_to_planning():
    assert transition(TaskStatus.RUNNING, TaskStatus.PLANNING) == TaskStatus.PLANNING
