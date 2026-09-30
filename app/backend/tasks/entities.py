"""Task domain model and rules. Pure Python: no ORM, HTTP or framework imports."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional

TITLE_MAX_LENGTH = 150
DESCRIPTION_MAX_LENGTH = 500
UPDATABLE_FIELDS = frozenset({"title", "description", "is_completed", "category"})


class TaskCategory(str, Enum):
    UNIVERSITY = "university"
    FINNISH = "finnish"
    GENERAL = "general"


class InvalidTaskError(ValueError):
    """Task data breaks a domain rule. The message is safe to show to users."""


class TaskNotFoundError(Exception):
    """The task does not exist or belongs to another user."""

    def __init__(self, task_id: int) -> None:
        super().__init__(f"Task {task_id} not found")
        self.task_id = task_id


def normalize_title(title: Any) -> str:
    if not isinstance(title, str):
        raise InvalidTaskError("Title is required")
    cleaned = title.strip()
    if not cleaned:
        raise InvalidTaskError("Title must not be blank")
    if len(cleaned) > TITLE_MAX_LENGTH:
        raise InvalidTaskError(f"Title must be at most {TITLE_MAX_LENGTH} characters")
    return cleaned


def normalize_description(description: Any) -> Optional[str]:
    if description is None:
        return None
    if not isinstance(description, str):
        raise InvalidTaskError("Description must be text")
    cleaned = description.strip()
    if len(cleaned) > DESCRIPTION_MAX_LENGTH:
        raise InvalidTaskError(f"Description must be at most {DESCRIPTION_MAX_LENGTH} characters")
    return cleaned or None


def to_category(value: Any) -> Optional[TaskCategory]:
    if value is None or isinstance(value, TaskCategory):
        return value
    try:
        return TaskCategory(value)
    except ValueError:
        raise InvalidTaskError(f"Unknown category: {value}") from None


def require_completion_flag(value: Any) -> bool:
    if not isinstance(value, bool):
        raise InvalidTaskError("Completion status must be true or false")
    return value


@dataclass
class Task:
    user_id: int
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    category: Optional[TaskCategory] = None
    id: Optional[int] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.title = normalize_title(self.title)
        self.description = normalize_description(self.description)
        self.is_completed = require_completion_flag(self.is_completed)
        self.category = to_category(self.category)

    def apply_changes(self, changes: Mapping[str, Any]) -> None:
        """Apply a partial update. Only keys present in `changes` are modified."""
        unknown = set(changes) - UPDATABLE_FIELDS
        if unknown:
            raise InvalidTaskError(f"Unknown task fields: {', '.join(sorted(unknown))}")
        if "title" in changes:
            self.title = normalize_title(changes["title"])
        if "description" in changes:
            self.description = normalize_description(changes["description"])
        if "is_completed" in changes:
            self.is_completed = require_completion_flag(changes["is_completed"])
        if "category" in changes:
            self.category = to_category(changes["category"])


@dataclass(frozen=True)
class CategorySummary:
    category: TaskCategory
    total: int
    completed: int
