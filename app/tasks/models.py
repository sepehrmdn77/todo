from sqlalchemy import Column, Integer, String, Boolean, Text, func, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
# from app.users.models import UsersModel


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer,ForeignKey("users.id")) # for connecting to users table

    title = Column(String(150), nullable=False)
    description = Column(Text(500), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    user = relationship("UsersModel", back_populates="tasks", uselist=False)