"""What the task use cases need from storage. Implementations live in tasks/adapters.py."""

from typing import Optional, Protocol

from tasks.entities import CategorySummary, Task, TaskCategory


class TaskRepository(Protocol):
    def list_for_user(
        self,
        user_id: int,
        *,
        completed: Optional[bool],
        category: Optional[TaskCategory],
        limit: int,
        offset: int,
    ) -> list[Task]:
        """Tasks of one user: incomplete first, then newest first."""
        ...

    def get_for_user(self, user_id: int, task_id: int) -> Optional[Task]: ...

    def add(self, task: Task) -> Task:
        """Persist a new task and return it with id and timestamps set."""
        ...

    def save(self, task: Task) -> Task:
        """Persist changes to an existing task and return the stored state."""
        ...

    def delete(self, task: Task) -> None: ...

    def summarize_by_category(self, user_id: int) -> list[CategorySummary]:
        """Counts for categories that have at least one task (uncategorised tasks excluded)."""
        ...
