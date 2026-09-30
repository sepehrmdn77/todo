"""Frontend view of tasks. Mirrors the backend contract; no flet imports here."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional

TITLE_MAX_LENGTH = 150
DESCRIPTION_MAX_LENGTH = 500
CATEGORIES: tuple[str, ...] = ("university", "finnish", "painting")
CATEGORY_LABELS: dict[str, str] = {"university": "University", "finnish": "Finnish", "painting": "Painting"}


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    is_completed: bool

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "Task":
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            description=data.get("description"),
            category=data.get("category"),
            is_completed=bool(data["is_completed"]),
        )


@dataclass(frozen=True)
class CategorySummary:
    category: str
    total: int
    completed: int

    @property
    def progress(self) -> float:
        return self.completed / self.total if self.total else 0.0

    @property
    def label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category.title())

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "CategorySummary":
        return cls(category=str(data["category"]), total=int(data["total"]), completed=int(data["completed"]))


@dataclass(frozen=True)
class TaskDraft:
    """What the task form collects; validated before it is sent."""

    title: str
    description: str
    category: Optional[str]

    def validate(self) -> dict[str, str]:
        errors: dict[str, str] = {}
        title = self.title.strip()
        if not title:
            errors["title"] = "Give your task a title."
        elif len(title) > TITLE_MAX_LENGTH:
            errors["title"] = f"Keep the title under {TITLE_MAX_LENGTH} characters."
        if len(self.description.strip()) > DESCRIPTION_MAX_LENGTH:
            errors["description"] = f"Keep the description under {DESCRIPTION_MAX_LENGTH} characters."
        if self.category is not None and self.category not in CATEGORIES:
            errors["category"] = "Choose a category from the list."
        return errors

    def to_payload(self) -> dict[str, Any]:
        return {
            "title": self.title.strip(),
            "description": self.description.strip() or None,
            "category": self.category,
        }
