import os
import uuid
from collections.abc import AsyncIterator

import asyncpg
import pytest

from internal.domain import ErrNotFound, Subject, User
from internal.repository.postgres import (
    PostgresSubjectRepository,
    PostgresUserRepository,
)


def uniq(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@pytest.fixture
async def pool() -> AsyncIterator[asyncpg.Pool]:
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("TEST_DATABASE_URL is not set")
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    try:
        yield pool
    finally:
        await pool.close()


@pytest.fixture
def user_repo(pool: asyncpg.Pool) -> PostgresUserRepository:
    return PostgresUserRepository(pool)


@pytest.fixture
def subject_repo(pool: asyncpg.Pool) -> PostgresSubjectRepository:
    return PostgresSubjectRepository(pool)


@pytest.fixture
async def user(user_repo: PostgresUserRepository) -> AsyncIterator[User]:
    """Тестовый пользователь; удаляется после теста вместе с зависимыми записями."""
    created = await user_repo.create(
        User(email=f"{uniq('user')}@example.com", password_hash="hash", name="Test")
    )
    yield created
    try:
        await user_repo.delete(created.id)
    except ErrNotFound:
        pass


@pytest.fixture
async def subject(subject_repo: PostgresSubjectRepository, user: User) -> Subject:
    return await subject_repo.create(Subject(user_id=user.id, name=uniq("subject")))
