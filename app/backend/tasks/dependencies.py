"""Composition root for the tasks module: wires the SQLAlchemy adapter into the service."""

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from tasks.adapters import SqlAlchemyTaskRepository
from tasks.services import TaskService


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(SqlAlchemyTaskRepository(db))
