from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from internal.service.health_service import HealthService


def create_health_router(health_service: HealthService) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health(request: Request):
        pool = getattr(request.app.state, "db_pool", None)
        if pool is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "db": "down"},
            )

        try:
            info = await health_service.get_health(pool)
            return {
                "status": info.status,
                "db": "up",
                "app_name": info.app_name,
                "version": info.version,
                "environment": info.environment,
                "uptime": info.uptime,
            }
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "db": "down"},
            )

    return router
