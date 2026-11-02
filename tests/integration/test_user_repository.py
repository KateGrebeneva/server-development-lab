import pytest

from internal.domain import (
    ErrAlreadyExists,
    ErrInvalidInput,
    ErrNotFound,
    User,
)
from tests.integration.conftest import uniq


async def test_create_and_get_by_id(user_repo):
    user = User(email=f"{uniq('user')}@example.com", password_hash="hash", name="Катя")
    await user_repo.create(user)
    try:
        # id и created_at заполняет СУБД
        assert user.id is not None
        assert user.created_at is not None

        got = await user_repo.get_by_id(user.id)
        assert got.email == user.email
        assert got.name == "Катя"
        assert got.role == "student"
    finally:
        await user_repo.delete(user.id)


async def test_get_by_id_not_found(user_repo):
    with pytest.raises(ErrNotFound):
        await user_repo.get_by_id(999_999_999)


async def test_create_duplicate_email(user_repo, user):
    duplicate = User(email=user.email, password_hash="hash", name="Copy")
    with pytest.raises(ErrAlreadyExists):
        await user_repo.create(duplicate)


async def test_get_by_email(user_repo, user):
    got = await user_repo.get_by_email(user.email)
    assert got.id == user.id


async def test_get_by_email_sql_injection(user_repo, user):
    # При склейке строк этот ввод вернул бы первого пользователя таблицы.
    with pytest.raises(ErrNotFound):
        await user_repo.get_by_email("' OR '1'='1")


async def test_list_respects_limit(user_repo):
    created = []
    for _ in range(3):
        u = User(email=f"{uniq('list')}@example.com", password_hash="hash", name="L")
        created.append(await user_repo.create(u))
    try:
        page = await user_repo.list(limit=2, offset=0)
        assert len(page) <= 2

        # limit больше 100 заменяется значением по умолчанию (20)
        assert len(await user_repo.list(limit=10_000)) <= 20
    finally:
        for u in created:
            await user_repo.delete(u.id)


async def test_delete_then_get_not_found(user_repo):
    user = await user_repo.create(
        User(email=f"{uniq('del')}@example.com", password_hash="hash", name="D")
    )
    await user_repo.delete(user.id)
    with pytest.raises(ErrNotFound):
        await user_repo.get_by_id(user.id)


async def test_delete_missing_not_found(user_repo):
    with pytest.raises(ErrNotFound):
        await user_repo.delete(999_999_999)


async def test_check_violation_is_invalid_input(user_repo):
    user = User(
        email=f"{uniq('role')}@example.com", password_hash="hash", name="R", role="hacker"
    )
    with pytest.raises(ErrInvalidInput) as exc_info:
        await user_repo.create(user)
    # в текст ошибки не попадают данные строки (хеш пароля)
    assert str(exc_info.value) == "users_role_check"


async def test_password_hash_not_serialized(user):
    data = user.model_dump()
    assert "password_hash" not in data
    assert "hash" not in user.model_dump_json()
