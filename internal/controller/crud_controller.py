import hashlib
import os
from datetime import datetime

from fastapi import APIRouter, Query, Request, Response, status
from pydantic import BaseModel, Field

from internal.controller.errors import ALREADY_EXISTS, CONFLICT, INVALID_INPUT, NOT_FOUND
from internal.domain import StudySession, Subject, Task, User

class UserCreate(BaseModel):
    email: str = Field(examples=["katya@example.com"])
    password: str = Field(examples=["secret123"])
    name: str = Field(examples=["Катя"])
    role: str = Field("student", description="student, parent, teacher или admin")
    theme: str = Field("light", description="light, dark или system")


class SubjectInput(BaseModel):
    user_id: int = Field(examples=[1])
    name: str = Field(examples=["Математика"])
    color: str = Field("#7012CE", description="HEX-цвет, например #7012CE")
    category: str | None = None
    time_studied_minutes: int = 0


class TaskInput(BaseModel):
    subject_id: int = Field(examples=[1])
    title: str = Field(examples=["Решить задачи 1–10"])
    description: str | None = None
    priority: str = Field("medium", description="low, medium или high")
    is_completed: bool = False
    due_date: datetime | None = None


class StudySessionCreate(BaseModel):
    user_id: int = Field(examples=[1])
    subject_id: int | None = None
    goal: str = Field(examples=["Подготовка к контрольной"])
    duration_minutes: int = Field(examples=[60])
    scheduled_at: datetime = Field(examples=["2030-01-15T10:00:00+03:00"])


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def create_crud_router() -> APIRouter:
    router = APIRouter()

    # ---------- пользователи ----------
    @router.post("/users", status_code=201, tags=["users"], summary="Создать пользователя",
                 responses={**ALREADY_EXISTS, **INVALID_INPUT})
    async def create_user(body: UserCreate, request: Request) -> User:
        user = User(
            email=body.email,
            password_hash=hash_password(body.password),
            name=body.name,
            role=body.role,
            theme=body.theme,
        )
        return await request.app.state.user_repo.create(user)

    @router.get("/users", tags=["users"], summary="Список пользователей")
    async def list_users(request: Request, limit: int = Query(20, description="не больше 100"),
                         offset: int = 0) -> list[User]:
        return await request.app.state.user_repo.list(limit, offset)

    @router.get("/users/by-email", tags=["users"], summary="Найти пользователя по email",
                responses=NOT_FOUND)
    async def get_user_by_email(email: str, request: Request) -> User:
        return await request.app.state.user_repo.get_by_email(email)

    @router.get("/users/{user_id}", tags=["users"], summary="Получить пользователя",
                responses=NOT_FOUND)
    async def get_user(user_id: int, request: Request) -> User:
        return await request.app.state.user_repo.get_by_id(user_id)

    @router.delete("/users/{user_id}", status_code=204, tags=["users"],
                   summary="Удалить пользователя", responses=NOT_FOUND)
    async def delete_user(user_id: int, request: Request) -> Response:
        await request.app.state.user_repo.delete(user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # ---------- предметы ----------
    @router.post("/subjects", status_code=201, tags=["subjects"], summary="Создать предмет",
                 responses={**CONFLICT, **INVALID_INPUT})
    async def create_subject(body: SubjectInput, request: Request) -> Subject:
        return await request.app.state.subject_repo.create(Subject(**body.model_dump()))

    @router.get("/subjects", tags=["subjects"], summary="Список предметов")
    async def list_subjects(request: Request, limit: int = Query(20, description="не больше 100"),
                            offset: int = 0) -> list[Subject]:
        return await request.app.state.subject_repo.list(limit, offset)

    @router.get("/subjects/{subject_id}", tags=["subjects"], summary="Получить предмет",
                responses=NOT_FOUND)
    async def get_subject(subject_id: int, request: Request) -> Subject:
        return await request.app.state.subject_repo.get_by_id(subject_id)

    @router.put("/subjects/{subject_id}", tags=["subjects"], summary="Обновить предмет",
                responses={**NOT_FOUND, **INVALID_INPUT})
    async def update_subject(subject_id: int, body: SubjectInput, request: Request) -> Subject:
        repo = request.app.state.subject_repo
        await repo.update(Subject(id=subject_id, **body.model_dump()))
        return await repo.get_by_id(subject_id)

    @router.delete("/subjects/{subject_id}", status_code=204, tags=["subjects"],
                   summary="Удалить предмет", responses=NOT_FOUND)
    async def delete_subject(subject_id: int, request: Request) -> Response:
        await request.app.state.subject_repo.delete(subject_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # ---------- задачи ----------
    @router.post("/tasks", status_code=201, tags=["tasks"], summary="Создать задачу",
                 responses={**CONFLICT, **INVALID_INPUT})
    async def create_task(body: TaskInput, request: Request) -> Task:
        return await request.app.state.task_repo.create(Task(**body.model_dump()))

    @router.get("/tasks", tags=["tasks"], summary="Список задач")
    async def list_tasks(request: Request, limit: int = Query(20, description="не больше 100"),
                         offset: int = 0) -> list[Task]:
        return await request.app.state.task_repo.list(limit, offset)

    @router.get("/tasks/{task_id}", tags=["tasks"], summary="Получить задачу",
                responses=NOT_FOUND)
    async def get_task(task_id: int, request: Request) -> Task:
        return await request.app.state.task_repo.get_by_id(task_id)

    @router.put("/tasks/{task_id}", tags=["tasks"], summary="Обновить задачу",
                responses={**NOT_FOUND, **INVALID_INPUT})
    async def update_task(task_id: int, body: TaskInput, request: Request) -> Task:
        repo = request.app.state.task_repo
        await repo.update(Task(id=task_id, **body.model_dump()))
        return await repo.get_by_id(task_id)

    @router.delete("/tasks/{task_id}", status_code=204, tags=["tasks"],
                   summary="Удалить задачу", responses=NOT_FOUND)
    async def delete_task(task_id: int, request: Request) -> Response:
        await request.app.state.task_repo.delete(task_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # ---------- учебные сессии ----------
    @router.post("/study-sessions", status_code=201, tags=["study-sessions"],
                 summary="Запланировать учебную сессию (транзакция)",
                 description="В одной транзакции блокирует пользователя (FOR UPDATE), "
                             "проверяет пересечение по времени и создаёт сессию.",
                 responses={**NOT_FOUND, **CONFLICT, **INVALID_INPUT})
    async def schedule_session(body: StudySessionCreate, request: Request) -> StudySession:
        session = StudySession(**body.model_dump())
        return await request.app.state.study_session_service.schedule(session)

    @router.get("/study-sessions", tags=["study-sessions"], summary="Список учебных сессий")
    async def list_sessions(request: Request, limit: int = Query(20, description="не больше 100"),
                            offset: int = 0) -> list[StudySession]:
        return await request.app.state.study_session_repo.list(limit, offset)

    @router.get("/study-sessions/{session_id}", tags=["study-sessions"],
                summary="Получить учебную сессию", responses=NOT_FOUND)
    async def get_session(session_id: int, request: Request) -> StudySession:
        return await request.app.state.study_session_repo.get_by_id(session_id)

    @router.delete("/study-sessions/{session_id}", status_code=204, tags=["study-sessions"],
                   summary="Удалить учебную сессию", responses=NOT_FOUND)
    async def delete_session(session_id: int, request: Request) -> Response:
        await request.app.state.study_session_repo.delete(session_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
