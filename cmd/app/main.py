import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from internal.config.settings import load_config
from internal.controller.health_controller import create_health_router
from internal.database.postgres import create_pool_with_retries
from internal.service.health_service import HealthService

logging.basicConfig(level=logging.INFO)
config = load_config()
health_service = HealthService(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Приложение начнёт обслуживать запросы после подключения к БД.
    app.state.db_pool = await create_pool_with_retries(config)
    try:
        yield
    finally:
        await app.state.db_pool.close()


app = FastAPI(title=config.app_name, version=config.app_version, lifespan=lifespan)
app.include_router(create_health_router(health_service), prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cmd.app.main:app", host="0.0.0.0", port=config.http_port, reload=True)
