import asyncio
import logging

import asyncpg

from internal.config.settings import Config

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 10


async def create_pool_with_retries(config: Config) -> asyncpg.Pool:
    """Создаёт ограниченный пул и повторяет попытки, если PostgreSQL ещё не готов."""
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            pool = await asyncpg.create_pool(
                host=config.db_host,
                port=config.db_port,
                user=config.db_user,
                password=config.db_password,
                database=config.db_name,
                min_size=1,
                max_size=config.db_max_conns,
                command_timeout=5,
            )
            # Проверяем не только создание пула, но и реальное соединение с БД.
            async with pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            logger.info("Подключение к PostgreSQL установлено: %s:%s",
                        config.db_host, config.db_port)
            return pool
        except Exception as exc:
            last_error = exc
            wait_seconds = min(attempt * 2, 10)
            logger.warning(
                "Попытка подключения %s/%s не удалась: %s. Повтор через %s сек.",
                attempt, MAX_ATTEMPTS, exc, wait_seconds
            )
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(wait_seconds)

    raise RuntimeError(
        f"Не удалось подключиться к PostgreSQL после {MAX_ATTEMPTS} попыток"
    ) from last_error
