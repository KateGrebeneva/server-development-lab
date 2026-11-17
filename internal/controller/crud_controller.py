import hashlib
import os
from datetime import datetime

from fastapi import APIRouter, Query, Request, Response, status
from pydantic import BaseModel, Field

from internal.controller.errors import ALREADY_EXISTS, CONFLICT, INVALID_INPUT, NOT_FOUND
from internal.domain import StudySession, Subject, Task, User
from internal.controller.dto import (
    SubjectCreateRequest, SubjectUpdateRequest, SubjectResponse,
    TaskCreateRequest, TaskPatchRequest, TaskResponse,
)

class UserCreate(BaseModel):
    email: str = Field(examples=["katya@example.com"])
    password: str = Field(examples=["secret123"])
    name: str = Field(examples=["Катя"])
    role: str = Field("student", description="student, parent, teacher или admin")
    theme: str = Field("light", description="light, dark или system")


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

    # ---------- предметы: полный CRUD через SubjectService ----------
    @router.post("/subjects", status_code=201, tags=["subjects"],
                 summary="Создать предмет", response_model=SubjectResponse,
                 responses={**CONFLICT, **INVALID_INPUT})
    async def create_subject(body: SubjectCreateRequest, request: Request,
                             response: Response) -> SubjectResponse:
        subject = await request.app.state.subject_service.create(
            Subject(**body.model_dump())
        )
        response.headers["Location"] = f"/api/v1/subjects/{subject.id}"
        return SubjectResponse.from_domain(subject)

    @router.get("/subjects", tags=["subjects"], summary="Список предметов",
                response_model=list[SubjectResponse])
    async def list_subjects(request: Request,
                            limit: int = Query(20, ge=1, le=100),
                            offset: int = Query(0, ge=0)) -> list[SubjectResponse]:
        items = await request.app.state.subject_service.list(limit, offset)
        return [SubjectResponse.from_domain(item) for item in items]

    @router.get("/subjects/{subject_id}", tags=["subjects"],
                summary="Получить предмет", response_model=SubjectResponse,
                responses=NOT_FOUND)
    async def get_subject(subject_id: int, request: Request) -> SubjectResponse:
        item = await request.app.state.subject_service.get(subject_id)
        return SubjectResponse.from_domain(item)

    @router.put("/subjects/{subject_id}", tags=["subjects"],
                summary="Полностью обновить предмет",
                response_model=SubjectResponse,
                responses={**NOT_FOUND, **INVALID_INPUT})
    async def update_subject(subject_id: int, body: SubjectUpdateRequest,
                             request: Request) -> SubjectResponse:
        item = await request.app.state.subject_service.update(
            subject_id, Subject(**body.model_dump())
        )
        return SubjectResponse.from_domain(item)

    @router.delete("/subjects/{subject_id}", status_code=204, tags=["subjects"],
                   summary="Удалить предмет", responses=NOT_FOUND)
    async def delete_subject(subject_id: int, request: Request) -> Response:
        await request.app.state.subject_service.delete(subject_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # ---------- задачи: создание, чтение и изменение состояния ----------
    @router.post("/tasks", status_code=201, tags=["tasks"],
                 summary="Создать учебную задачу", response_model=TaskResponse,
                 responses={**NOT_FOUND, **CONFLICT, **INVALID_INPUT})
    async def create_task(body: TaskCreateRequest, request: Request,
                          response: Response) -> TaskResponse:
        item = await request.app.state.task_service.create(Task(**body.model_dump()))
        response.headers["Location"] = f"/api/v1/tasks/{item.id}"
        return TaskResponse.from_domain(item)

    @router.get("/tasks", tags=["tasks"], summary="Список задач",
                response_model=list[TaskResponse])
    async def list_tasks(request: Request,
                         limit: int = Query(20, ge=1, le=100),
                         offset: int = Query(0, ge=0)) -> list[TaskResponse]:
        items = await request.app.state.task_service.list(limit, offset)
        return [TaskResponse.from_domain(item) for item in items]

    @router.get("/tasks/{task_id}", tags=["tasks"], summary="Получить задачу",
                response_model=TaskResponse, responses=NOT_FOUND)
    async def get_task(task_id: int, request: Request) -> TaskResponse:
        item = await request.app.state.task_service.get(task_id)
        return TaskResponse.from_domain(item)

    @router.patch("/tasks/{task_id}", tags=["tasks"],
                  summary="Изменить задачу или отметить выполненной",
                  response_model=TaskResponse,
                  responses={**NOT_FOUND, **CONFLICT, **INVALID_INPUT})
    async def patch_task(task_id: int, body: TaskPatchRequest,
                         request: Request) -> TaskResponse:
        changes = body.model_dump(exclude_unset=True)
        item = await request.app.state.task_service.patch(task_id, changes)
        return TaskResponse.from_domain(item)

    @router.delete("/tasks/{task_id}", status_code=204, tags=["tasks"],
                   summary="Удалить задачу", responses=NOT_FOUND)
    async def delete_task(task_id: int, request: Request) -> Response:
        await request.app.state.task_service.delete(task_id)
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
