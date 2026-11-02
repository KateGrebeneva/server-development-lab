from datetime import datetime

from pydantic import BaseModel, Field

class User(BaseModel):
    id: int | None = None
    email: str
    password_hash: str = Field(exclude=True, repr=False)
    name: str
    role: str = "student"
    avatar_url: str | None = None
    theme: str = "light"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Subject(BaseModel):
    id: int | None = None
    user_id: int
    name: str
    color: str = "#7012CE"
    category: str | None = None
    time_studied_minutes: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Task(BaseModel):
    id: int | None = None
    subject_id: int
    title: str
    description: str | None = None
    priority: str = "medium"
    is_completed: bool = False
    due_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StudySession(BaseModel):
    id: int | None = None
    user_id: int
    subject_id: int | None = None
    goal: str
    work_interval: int = 25
    short_break: int = 5
    long_break: int = 15
    intervals_count: int = 4
    duration_minutes: int
    status: str = "planned"
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
