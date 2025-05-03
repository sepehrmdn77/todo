from fastapi import APIRouter, Path, Depends, HTTPException
from fastapi.responses import JSONResponse
from tasks.schemas import * # better not to use *
from tasks.models import TaskModel
from sqlalchemy.orm import Session # for creating session
from core.database import get_db
from typing import List

router = APIRouter(tags=["tasks"], prefix="/todo" )


@router.get("/tasks", response_model=List[TaskResponseSchema])
async def retrieve_tasks_list(db:Session = Depends(get_db)):
    result = db.query(TaskModel).all()
    return result

@router.get("/tasks/{task_id}", response_model=TaskResponseSchema)
async def retrieve_task_detail(task_id:int = Path(...,gt=0),db:Session = Depends(get_db)):
    task_obj = db.query(TaskModel).filter_by(id=task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404,detail="Task not found!")
    return task_obj

@router.post("/tasks", response_model=TaskResponseSchema)
async def create_task(request:TaskCreateSchema ,db:Session = Depends(get_db)):
    task_obj = TaskModel(**request.model_dump())
    db.add(task_obj)
    db.commit()
    db.refresh(task_obj)
    return task_obj

@router.put("/tasks/{task_id}", response_model=TaskResponseSchema)
async def update_task(task_id:int = Path(...,gt=0),db:Session = Depends(get_db)):
    return {}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id:int = Path(...,gt=0),db:Session = Depends(get_db)):
    return {}

