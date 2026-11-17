from datetime import datetime, timedelta, timezone

import pytest

from internal.domain import ErrConflict, ErrInvalidInput, ErrNotFound, Subject, Task
from internal.service.task_service import TaskService

NOW = datetime(2030, 1, 1, 10, 0, tzinfo=timezone.utc)


class FakeSubjectRepository:
    def __init__(self, items=None):
        self.items = items or {}

    async def get_by_id(self, subject_id):
        if subject_id not in self.items:
            raise ErrNotFound(f"subject {subject_id}")
        return self.items[subject_id]


class FakeTaskRepository:
    def __init__(self):
        self.items = {}
        self.next_id = 1

    async def create(self, task):
        task.id = self.next_id
        self.next_id += 1
        self.items[task.id] = task
        return task

    async def get_by_id(self, task_id):
        if task_id not in self.items:
            raise ErrNotFound(f"task {task_id}")
        return self.items[task_id]

    async def list(self, limit=20, offset=0):
        return list(self.items.values())[offset:offset + limit]

    async def update(self, task):
        if task.id not in self.items:
            raise ErrNotFound(f"task {task.id}")
        self.items[task.id] = task
        return task

    async def delete(self, task_id):
        if task_id not in self.items:
            raise ErrNotFound(f"task {task_id}")
        del self.items[task_id]


@pytest.fixture
def service():
    subjects = FakeSubjectRepository({
        7: Subject(id=7, user_id=1, name="Математика")
    })
    tasks = FakeTaskRepository()
    return TaskService(tasks, subjects, now=lambda: NOW), tasks


@pytest.mark.asyncio
async def test_create_rejects_task_for_missing_subject(service):
    task_service, tasks = service
    task = Task(subject_id=999, title="Подготовить конспект")

    with pytest.raises(ErrNotFound):
        await task_service.create(task)

    assert tasks.items == {}


@pytest.mark.asyncio
async def test_create_rejects_due_date_in_the_past(service):
    task_service, tasks = service
    task = Task(
        subject_id=7,
        title="Подготовить конспект",
        due_date=NOW - timedelta(minutes=1),
    )

    with pytest.raises(ErrInvalidInput):
        await task_service.create(task)

    assert tasks.items == {}


@pytest.mark.asyncio
async def test_create_and_complete_task_successfully(service):
    task_service, _ = service
    created = await task_service.create(
        Task(subject_id=7, title="  Решить упражнения  ", priority="high")
    )
    assert created.title == "Решить упражнения"
    assert created.is_completed is False

    completed = await task_service.patch(created.id, {"is_completed": True})
    assert completed.is_completed is True


@pytest.mark.asyncio
async def test_completed_task_cannot_be_completed_twice(service):
    task_service, _ = service
    created = await task_service.create(
        Task(subject_id=7, title="Прочитать главу")
    )
    await task_service.patch(created.id, {"is_completed": True})

    with pytest.raises(ErrConflict):
        await task_service.patch(created.id, {"is_completed": True})
