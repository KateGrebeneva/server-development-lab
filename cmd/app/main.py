from fastapi import FastAPI

from internal.config.settings import load_config
from internal.controller.health_controller import create_health_router
from internal.service.health_service import HealthService

config = load_config()
health_service = HealthService(config)

app = FastAPI(title=config.app_name, version=config.app_version)
app.include_router(create_health_router(health_service), prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cmd.app.main:app", host="0.0.0.0", port=config.http_port, reload=True)
