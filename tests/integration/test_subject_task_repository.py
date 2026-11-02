import pytest

from internal.domain import (
    ErrConflict,
    ErrInvalidInput,
    ErrNotFound,
    Subject,
    Task,
)
from internal.repository.postgres import PostgresTaskRepository
from tests.integration.conftest import uniq


@pytest.fixture
def task_repo(pool):
    return PostgresTaskRepository(pool)


async def test_subject_create_and_get(subject_repo, subject):
    assert subject.id is not None and subject.created_at is not None
    got = await subject_repo.get_by_id(subject.id)
    assert got.name == subject.name
    assert got.color == "#7012CE"


async def test_subject_update(subject_repo, subject):
    subject.name = "Математика"
    subject.color = "#22C55E"
    await subject_repo.update(subject)

    got = await subject_repo.get_by_id(subject.id)
    assert got.name == "Математика"
    assert got.color == "#22C55E"
    assert got.updated_at >= got.created_at


async def test_subject_update_missing_not_found(subject_repo, user):
    missing = Subject(id=999_999_999, user_id=user.id, name="nope")
    with pytest.raises(ErrNotFound):
        await subject_repo.update(missing)


async def test_subject_foreign_key_violation_is_conflict(subject_repo):
    with pytest.raises(ErrConflict):
        await subject_repo.create(Subject(user_id=999_999_999, name=uniq("orphan")))


async def test_subject_invalid_color_is_invalid_input(subject_repo, user):
    with pytest.raises(ErrInvalidInput):
        await subject_repo.create(Subject(user_id=user.id, name="bad", color="red"))


async def test_subject_list_respects_limit(subject_repo, user):
    for _ in range(3):
        await subject_repo.create(Subject(user_id=user.id, name=uniq("s")))
    assert len(await subject_repo.list(limit=2)) <= 2


async def test_task_create_update_delete(task_repo, subject):
    task = await task_repo.create(Task(subject_id=subject.id, title="Решить задачи"))
    assert task.id is not None and task.created_at is not None

    task.is_completed = True
    task.priority = "high"
    await task_repo.update(task)
    got = await task_repo.get_by_id(task.id)
    assert got.is_completed is True
    assert got.priority == "high"

    await task_repo.delete(task.id)
    with pytest.raises(ErrNotFound):
        await task_repo.get_by_id(task.id)


async def test_task_foreign_key_violation_is_conflict(task_repo):
    with pytest.raises(ErrConflict):
        await task_repo.create(Task(subject_id=999_999_999, title="orphan"))


async def test_task_list_is_ordered_newest_first(task_repo, subject):
    first = await task_repo.create(Task(subject_id=subject.id, title="first"))
    second = await task_repo.create(Task(subject_id=subject.id, title="second"))
    ids = [t.id for t in await task_repo.list(limit=100)]
    assert ids.index(second.id) < ids.index(first.id)


async def test_delete_subject_cascades_to_tasks(subject_repo, task_repo, subject):
    task = await task_repo.create(Task(subject_id=subject.id, title="cascade"))
    await subject_repo.delete(subject.id)
    with pytest.raises(ErrNotFound):
        await task_repo.get_by_id(task.id)
