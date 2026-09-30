from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Response, status

from auth.jwt_auth import get_authenticated_user
from tasks.dependencies import get_task_service
from tasks.entities import Task, TaskCategory
from tasks.schemas import (
    CategorySummarySchema,
    TaskCreateSchema,
    TaskResponseSchema,
    TaskUpdateSchema,
)
from tasks.services import DEFAULT_PAGE_SIZE, TaskService
from users.models import UsersModel

router = APIRouter(tags=["tasks"], prefix="/todo")

MAX_PAGE_SIZE = 100


@router.get("/tasks", response_model=list[TaskResponseSchema])
def list_tasks(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    category: Optional[TaskCategory] = Query(None, description="Filter by category"),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> list[Task]:
    return service.list_tasks(user.id, completed=completed, category=category, limit=limit, offset=offset)


# Declared before /tasks/{task_id} so "summary" is not parsed as an id.
@router.get("/tasks/summary", response_model=list[CategorySummarySchema])
def summarize_tasks(
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
):
    return service.summarize_categories(user.id)


@router.get("/tasks/{task_id}", response_model=TaskResponseSchema)
def retrieve_task(
    task_id: int = Path(..., gt=0),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Task:
    return service.get_task(user.id, task_id)


@router.post("/tasks", response_model=TaskResponseSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    request: TaskCreateSchema,
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Task:
    return service.create_task(user.id, **request.model_dump())


@router.patch("/tasks/{task_id}", response_model=TaskResponseSchema)
def update_task(
    request: TaskUpdateSchema,
    task_id: int = Path(..., gt=0),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Task:
    return service.update_task(user.id, task_id, request.model_dump(exclude_unset=True))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int = Path(..., gt=0),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Response:
    service.delete_task(user.id, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
