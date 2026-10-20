from dataclasses import dataclass
from time import monotonic

import asyncpg

from internal.config.settings import Config


@dataclass(frozen=True)
class HealthInfo:
    status: str
    app_name: str
    version: str
    environment: str
    uptime: float


class HealthService:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._started_at = monotonic()

    async def get_health(self, pool: asyncpg.Pool) -> HealthInfo:
        # Проверяем доступность именно базы, а не только работу HTTP-сервера.
        async with pool.acquire() as connection:
            await connection.fetchval("SELECT 1")

        return HealthInfo(
            status="pass",
            app_name=self._config.app_name,
            version=self._config.app_version,
            environment=self._config.app_env,
            uptime=round(monotonic() - self._started_at, 3),
        )
