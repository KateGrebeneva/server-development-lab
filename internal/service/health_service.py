from dataclasses import dataclass
from time import monotonic

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

    def get_health(self) -> HealthInfo:
        return HealthInfo(
            status="pass",
            app_name=self._config.app_name,
            version=self._config.app_version,
            environment=self._config.app_env,
            uptime=round(monotonic() - self._started_at, 3),
        )
