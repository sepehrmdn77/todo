from dataclasses import replace
from typing import Optional

from tasks.entities import CategorySummary, Task, TaskCategory


class InMemoryTaskRepository:
    """TaskRepository test double; returns copies so callers can't mutate stored state."""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1

    def list_for_user(self, user_id, *, completed, category, limit, offset) -> list[Task]:
        matching = [
            task
            for task in self._tasks.values()
            if task.user_id == user_id
            and (completed is None or task.is_completed == completed)
            and (category is None or task.category == category)
        ]
        return [replace(task) for task in matching[offset: offset + limit]]

    def get_for_user(self, user_id: int, task_id: int) -> Optional[Task]:
        task = self._tasks.get(task_id)
        return replace(task) if task and task.user_id == user_id else None

    def add(self, task: Task) -> Task:
        stored = replace(task, id=self._next_id)
        self._tasks[stored.id] = stored
        self._next_id += 1
        return replace(stored)

    def save(self, task: Task) -> Task:
        self._tasks[task.id] = replace(task)
        return replace(task)

    def delete(self, task: Task) -> None:
        self._tasks.pop(task.id, None)

    def summarize_by_category(self, user_id: int) -> list[CategorySummary]:
        summaries = []
        for category in TaskCategory:
            tasks = [t for t in self._tasks.values() if t.user_id == user_id and t.category == category]
            if tasks:
                done = sum(1 for t in tasks if t.is_completed)
                summaries.append(CategorySummary(category=category, total=len(tasks), completed=done))
        return summaries
