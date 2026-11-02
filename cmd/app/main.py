import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from internal.config.settings import load_config
from internal.controller.crud_controller import create_crud_router
from internal.controller.errors import register_error_handlers
from internal.controller.health_controller import create_health_router
from internal.database.postgres import create_pool_with_retries
from internal.repository.postgres import (
    PostgresStudySessionRepository,
    PostgresSubjectRepository,
    PostgresTaskRepository,
    PostgresUserRepository,
)
from internal.service.health_service import HealthService
from internal.service.study_session_service import StudySessionService

logging.basicConfig(level=logging.INFO)
config = load_config()
health_service = HealthService(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Приложение начнёт обслуживать запросы после подключения к БД.
    pool = await create_pool_with_retries(config)
    app.state.db_pool = pool

    # Репозитории получают пул соединений из ЛР 5 и передаются в слой сервисов.
    app.state.user_repo = PostgresUserRepository(pool)
    app.state.subject_repo = PostgresSubjectRepository(pool)
    app.state.task_repo = PostgresTaskRepository(pool)
    app.state.study_session_repo = PostgresStudySessionRepository(pool)
    app.state.study_session_service = StudySessionService(pool)
    try:
        yield
    finally:
        await app.state.db_pool.close()


app = FastAPI(title=config.app_name, version=config.app_version, lifespan=lifespan)
app.include_router(create_health_router(health_service), prefix="/api/v1")
app.include_router(create_crud_router(), prefix="/api/v1")
register_error_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cmd.app.main:app", host="0.0.0.0", port=config.http_port, reload=True)
