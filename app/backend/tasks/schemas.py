"""HTTP DTOs for the tasks API. Shape/length validation happens here, domain rules in entities."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from tasks.entities import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, TaskCategory


class TaskCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=TITLE_MAX_LENGTH, description="Title of the task")
    description: Optional[str] = Field(None, max_length=DESCRIPTION_MAX_LENGTH, description="Optional details")
    category: Optional[TaskCategory] = Field(None, description="Optional category")
    is_completed: bool = Field(False, description="Completion status of the task")


class TaskUpdateSchema(BaseModel):
    """Partial update: only fields present in the request body are changed; null clears optional fields."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=1, max_length=TITLE_MAX_LENGTH)
    description: Optional[str] = Field(None, max_length=DESCRIPTION_MAX_LENGTH)
    category: Optional[TaskCategory] = None
    is_completed: Optional[bool] = None


class TaskResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique identifier of the object")
    title: str
    description: Optional[str]
    category: Optional[TaskCategory]
    is_completed: bool
    created_date: datetime = Field(..., description="Creation date and time of the object")
    updated_date: datetime = Field(..., description="Updating date and time of the object")


class CategorySummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: TaskCategory
    total: int
    completed: int
