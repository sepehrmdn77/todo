from fastapi import APIRouter, Path, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from tasks.schemas import *  # better not to use *
from tasks.models import TaskModel
from users.models import UsersModel
from sqlalchemy.orm import Session  # for creating session
from core.database import get_db
from typing import List
from auth.jwt_auth import get_authenticated_user


router = APIRouter(tags=["tasks"], prefix="/todo")


@router.get("/tasks", response_model=List[TaskResponseSchema])
async def retrieve_tasks_list(
    limit: int = Query(10, gt=0, le=50, description="Tasks count filter"),
    offset: int = Query(
        0, gt=0, description="User for paginating based on passed items"
    ),
    completed: bool = Query(None, description="Filter tasks by complition status"),
    db: Session = Depends(get_db),
    user: UsersModel = Depends(get_authenticated_user),
):
    query = db.query(TaskModel).filter_by(user_id=user.id)
    if completed is not None:
        query = query.filter_by(is_completed=completed)

    return query.limit(limit).offset(offset).all()


@router.get("/tasks/{task_id}", response_model=TaskResponseSchema)
async def retrieve_task_detail(
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    user: UsersModel = Depends(get_authenticated_user),
):
    task_obj = db.query(TaskModel).filter_by(user_id=user.id, id=task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found!")
    return task_obj


@router.post("/tasks", response_model=TaskResponseSchema)
async def create_task(
    request: TaskCreateSchema,
    db: Session = Depends(get_db),
    user: UsersModel = Depends(get_authenticated_user),
):
    data = request.model_dump()
    data.update({"user_id": user.id})
    task_obj = TaskModel(**data)
    db.add(task_obj)
    db.commit()
    db.refresh(task_obj)
    return task_obj


@router.put("/tasks/{task_id}", response_model=TaskResponseSchema)
async def update_task(
    request: TaskUpdateSchema,
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    user: UsersModel = Depends(get_authenticated_user),
):
    task_obj = db.query(TaskModel).filter_by(user_id=user.id, id=task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found!")
    if request.title:
        task_obj.title = request.title
    if request.description:
        task_obj.description = request.description
    if request.is_completed:
        task_obj.is_completed = request.is_completed
    db.commit()
    db.refresh(task_obj)
    return task_obj


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    user: UsersModel = Depends(get_authenticated_user),
):
    task_obj = db.query(TaskModel).filter_by(user_id=user.id, id=task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found!")
    db.delete(task_obj)
    db.commit()
    # return JSONResponse(status_code=200,content="Task deleted.")
