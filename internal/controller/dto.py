from datetime import datetime
from pydantic import BaseModel, Field

from internal.domain import Subject, Task


class SubjectCreateRequest(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=255)
    color: str = "#7012CE"
    category: str | None = None
    time_studied_minutes: int = Field(default=0, ge=0)


class SubjectUpdateRequest(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=255)
    color: str
    category: str | None = None
    time_studied_minutes: int = Field(default=0, ge=0)


class SubjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    color: str
    category: str | None
    time_studied_minutes: int
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_domain(cls, item: Subject) -> "SubjectResponse":
        return cls(**item.model_dump())


class TaskCreateRequest(BaseModel):
    subject_id: int
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    priority: str = "medium"
    due_date: datetime | None = None


class TaskPatchRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    priority: str | None = None
    is_completed: bool | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    id: int
    subject_id: int
    title: str
    description: str | None
    priority: str
    is_completed: bool
    due_date: datetime | None
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_domain(cls, item: Task) -> "TaskResponse":
        return cls(**item.model_dump())