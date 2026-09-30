"""SQLAlchemy implementation of the TaskRepository port."""

from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from tasks.entities import CategorySummary, Task, TaskCategory, TaskNotFoundError
from tasks.models import TaskModel


def _to_entity(row: TaskModel) -> Task:
    return Task(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        description=row.description,
        is_completed=row.is_completed,
        category=row.category,
        created_date=row.created_date,
        updated_date=row.updated_date,
    )


class SqlAlchemyTaskRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(
        self,
        user_id: int,
        *,
        completed: Optional[bool],
        category: Optional[TaskCategory],
        limit: int,
        offset: int,
    ) -> list[Task]:
        query = self._db.query(TaskModel).filter(TaskModel.user_id == user_id)
        if completed is not None:
            query = query.filter(TaskModel.is_completed == completed)
        if category is not None:
            query = query.filter(TaskModel.category == category)
        rows = (
            query.order_by(TaskModel.is_completed, TaskModel.created_date.desc(), TaskModel.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [_to_entity(row) for row in rows]

    def get_for_user(self, user_id: int, task_id: int) -> Optional[Task]:
        row = self._find(user_id, task_id)
        return _to_entity(row) if row else None

    def add(self, task: Task) -> Task:
        row = TaskModel(
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            is_completed=task.is_completed,
            category=task.category,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _to_entity(row)

    def save(self, task: Task) -> Task:
        row = self._find(task.user_id, task.id)
        if row is None:
            raise TaskNotFoundError(task.id)
        row.title = task.title
        row.description = task.description
        row.is_completed = task.is_completed
        row.category = task.category
        self._db.commit()
        self._db.refresh(row)
        return _to_entity(row)

    def delete(self, task: Task) -> None:
        row = self._find(task.user_id, task.id)
        if row is not None:
            self._db.delete(row)
            self._db.commit()

    def summarize_by_category(self, user_id: int) -> list[CategorySummary]:
        completed_count = func.sum(case((TaskModel.is_completed.is_(True), 1), else_=0))
        rows = (
            self._db.query(TaskModel.category, func.count(TaskModel.id), completed_count)
            .filter(TaskModel.user_id == user_id, TaskModel.category.isnot(None))
            .group_by(TaskModel.category)
            .all()
        )
        return [
            CategorySummary(category=category, total=total, completed=int(done or 0))
            for category, total, done in rows
        ]

    def _find(self, user_id: int, task_id: Optional[int]) -> Optional[TaskModel]:
        return self._db.query(TaskModel).filter_by(user_id=user_id, id=task_id).one_or_none()
