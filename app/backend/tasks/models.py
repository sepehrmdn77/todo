from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from core.database import Base
from tasks.entities import TITLE_MAX_LENGTH, TaskCategory


def _enum_values(enum_cls: type[TaskCategory]) -> list[str]:
    """Store enum *values* ("finnish"), not member names ("FINNISH")."""
    return [member.value for member in enum_cls]


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(TITLE_MAX_LENGTH), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    category = Column(
        SqlEnum(TaskCategory, name="task_category", values_callable=_enum_values),
        nullable=True,
    )
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("UsersModel", back_populates="tasks", uselist=False)
