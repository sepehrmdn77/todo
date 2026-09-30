"""Task use cases. Depends only on entities and the TaskRepository port."""

from typing import Any, Mapping, Optional

from tasks.entities import CategorySummary, Task, TaskCategory, TaskNotFoundError
from tasks.ports import TaskRepository

DEFAULT_PAGE_SIZE = 50


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(
        self,
        user_id: int,
        *,
        completed: Optional[bool] = None,
        category: Optional[TaskCategory] = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> list[Task]:
        return self._repository.list_for_user(
            user_id, completed=completed, category=category, limit=limit, offset=offset
        )

    def get_task(self, user_id: int, task_id: int) -> Task:
        task = self._repository.get_for_user(user_id, task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def create_task(
        self,
        user_id: int,
        *,
        title: str,
        description: Optional[str] = None,
        category: Optional[TaskCategory] = None,
        is_completed: bool = False,
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            is_completed=is_completed,
        )
        return self._repository.add(task)

    def update_task(self, user_id: int, task_id: int, changes: Mapping[str, Any]) -> Task:
        task = self.get_task(user_id, task_id)
        task.apply_changes(changes)
        return self._repository.save(task)

    def delete_task(self, user_id: int, task_id: int) -> None:
        self._repository.delete(self.get_task(user_id, task_id))

    def summarize_categories(self, user_id: int) -> list[CategorySummary]:
        """One summary per category (zero-filled), in TaskCategory declaration order."""
        found = {s.category: s for s in self._repository.summarize_by_category(user_id)}
        return [found.get(c, CategorySummary(category=c, total=0, completed=0)) for c in TaskCategory]
