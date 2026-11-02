from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from typing import Any, Protocol, TypeVar

import asyncpg

from internal.domain import (
    DomainError,
    ErrAlreadyExists,
    ErrConflict,
    ErrInvalidInput,
)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

T = TypeVar("T")


class DBTX(Protocol):
    async def execute(self, query: str, *args: Any) -> str: ...

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]: ...

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None: ...

    async def fetchval(self, query: str, *args: Any) -> Any: ...


class RepositoryError(Exception):
    """Прочие ошибки БД (сеть, таймаут). Исходная ошибка сохраняется в __cause__."""


def map_error(exc: Exception) -> Exception:
    if isinstance(exc, DomainError):
        return exc
    if isinstance(exc, asyncpg.UniqueViolationError):  # SQLSTATE 23505
        return ErrAlreadyExists(exc.constraint_name or str(exc))
    if isinstance(exc, asyncpg.ForeignKeyViolationError):  # SQLSTATE 23503
        return ErrConflict(exc.constraint_name or str(exc))
    if isinstance(
        exc,
        (
            asyncpg.CheckViolationError,  # SQLSTATE 23514
            asyncpg.NotNullViolationError,  # SQLSTATE 23502
            asyncpg.InvalidTextRepresentationError,  # SQLSTATE 22P02
            asyncpg.DataError,  # класс 22 и неверный тип параметра на стороне драйвера
        ),
    ):
        constraint = getattr(exc, "constraint_name", None)
        message = getattr(exc, "message", None) or str(exc).splitlines()[0]
        return ErrInvalidInput(constraint or message)
    return RepositoryError(f"database error: {exc}")


@contextmanager
def translate_errors() -> Iterator[None]:
    """Оборачивает обращение к БД: наружу выходят только доменные ошибки."""
    try:
        yield
    except Exception as exc:
        mapped = map_error(exc)
        if mapped is exc:
            raise
        raise mapped from exc


def rows_affected(status: str) -> int:
    """Число затронутых строк из статуса команды, например 'DELETE 1' -> 1."""
    return int(status.rsplit(" ", 1)[-1])


def normalize_page(limit: int, offset: int) -> tuple[int, int]:
    """Ограничивает limit сверху, чтобы клиент не мог запросить всю таблицу."""
    if limit <= 0 or limit > MAX_LIMIT:
        limit = DEFAULT_LIMIT
    if offset < 0:
        offset = 0
    return limit, offset


async def with_tx(pool: asyncpg.Pool, fn: Callable[[asyncpg.Connection], Awaitable[T]]) -> T:
    """Выполняет fn в транзакции: COMMIT при успехе, ROLLBACK при исключении."""
    async with pool.acquire() as connection:
        async with connection.transaction():
            return await fn(connection)
