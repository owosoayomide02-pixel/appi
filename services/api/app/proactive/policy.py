"""Optional proactive events. Default is quiet."""

from __future__ import annotations

from enum import Enum


class Priority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"


DEFAULT_MIN_PRIORITY = Priority.IMPORTANT
