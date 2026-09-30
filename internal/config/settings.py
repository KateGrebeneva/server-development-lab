import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    app_name: str
    app_env: str
    http_port: int
    app_version: str


def load_config() -> Config:
    load_dotenv()
    return Config(
        app_name=os.getenv("APP_NAME", "Studly API"),
        app_env=os.getenv("APP_ENV", "development"),
        http_port=int(os.getenv("HTTP_PORT", "8080")),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
    )
