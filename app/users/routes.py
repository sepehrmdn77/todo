from fastapi import APIRouter, Path, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from users.schemas import *  # better not to use *
from users.models import UsersModel, TokenModel
from sqlalchemy.orm import Session  # for creating session
from core.database import get_db
from typing import List
import secrets


router = APIRouter(tags=["users"], prefix="/users")

def generate_token(lenght=32):
    """Generates a secure random token as a string"""
    return secrets.token_hex(32)


@router.post("/login")
async def user_login(request: UserLoginSchema, db: Session = Depends(get_db)):
    user_obj = db.query(UsersModel).filter_by(username=request.username.lower()).first()
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    if not user_obj.verify_password(request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="incorrect password")
    token_obj = TokenModel(user_id = user_obj.id, token=generate_token())
    db.add(token_obj)
    db.commit()
    db.refresh(token_obj)
    return JSONResponse(content={"detail":"logged in successfully", "token": token_obj.token})


@router.post("/register")
async def user_register(request: UserRegisterSchema, db: Session = Depends(get_db)):
    if db.query(UsersModel).filter_by(username=request.username.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="username already exists"
        )
    user_obj = UsersModel(username=request.username.lower())
    user_obj.set_password(request.password)
    db.add(user_obj)
    db.commit()

    return JSONResponse(content={"detail":"User registered successfully"})

