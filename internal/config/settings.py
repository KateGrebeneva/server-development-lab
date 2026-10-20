import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    app_name: str
    app_env: str
    http_port: int
    app_version: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_max_conns: int


def load_config() -> Config:
    load_dotenv()

    required = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Не заданы обязательные переменные окружения: " + ", ".join(missing)
        )

    try:
        http_port = int(os.getenv("HTTP_PORT", "8080"))
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_max_conns = int(os.getenv("DB_MAX_CONNS", "10"))
    except ValueError as exc:
        raise RuntimeError("HTTP_PORT, DB_PORT и DB_MAX_CONNS должны быть числами") from exc

    if not 1 <= db_max_conns <= 100:
        raise RuntimeError("DB_MAX_CONNS должен быть в диапазоне от 1 до 100")

    return Config(
        app_name=os.getenv("APP_NAME", "Studly API"),
        app_env=os.getenv("APP_ENV", "development"),
        http_port=http_port,
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        db_host=os.environ["DB_HOST"],
        db_port=db_port,
        db_user=os.environ["DB_USER"],
        db_password=os.environ["DB_PASSWORD"],
        db_name=os.environ["DB_NAME"],
        db_max_conns=db_max_conns,
    )
