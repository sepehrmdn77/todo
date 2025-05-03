from fastapi import APIRouter, Path, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from users.schemas import * # better not to use *
from users.models import UsersModel
from sqlalchemy.orm import Session # for creating session
from core.database import get_db
from typing import List

router = APIRouter(tags=["users"], prefix="/users" )

@router.post("/login")
async def user_login(request:UserLoginSchema ,db:Session = Depends(get_db)):
    return {}

@router.post("/register")
async def user_register(request:UserRegisterSchema ,db:Session = Depends(get_db)):
    if db.query(UsersModel).filter_by(username=request.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already exists")
    user_obj = UsersModel(username=request.username)
    user_obj.set_password(request.password)
    db.add(user_obj)
    db.commit()

    return JSONResponse(content="User registered successfully")