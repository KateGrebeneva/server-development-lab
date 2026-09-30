from fastapi import APIRouter

from internal.service.health_service import HealthService


def create_health_router(health_service: HealthService) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict:
        info = health_service.get_health()
        return {
            "status": info.status,
            "app_name": info.app_name,
            "version": info.version,
            "environment": info.environment,
            "uptime": info.uptime,
        }

    return router
