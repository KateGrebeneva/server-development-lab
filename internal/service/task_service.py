from collections.abc import Callable
from datetime import datetime, timezone

from internal.domain import ErrConflict, ErrInvalidInput, Task
from internal.repository.repository import SubjectRepository, TaskRepository


class TaskService:
    """Сценарии работы с задачами и правила перехода их состояния."""

    ALLOWED_PRIORITIES = {"low", "medium", "high"}

    def __init__(
        self,
        tasks: TaskRepository,
        subjects: SubjectRepository,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._tasks = tasks
        self._subjects = subjects
        self._now = now or (lambda: datetime.now(timezone.utc))

    async def create(self, task: Task) -> Task:
        task.title = task.title.strip()
        if not task.title:
            raise ErrInvalidInput("task title must not be empty")
        if task.priority not in self.ALLOWED_PRIORITIES:
            raise ErrInvalidInput("priority must be low, medium or high")
        self._validate_due_date(task.due_date)
        # Бизнес-правило: задача может относиться только к существующему предмету.
        await self._subjects.get_by_id(task.subject_id)
        return await self._tasks.create(task)

    async def get(self, task_id: int) -> Task:
        return await self._tasks.get_by_id(task_id)

    async def list(self, limit: int = 20, offset: int = 0) -> list[Task]:
        return await self._tasks.list(max(1, min(limit, 100)), max(0, offset))

    async def patch(self, task_id: int, changes: dict) -> Task:
        task = await self.get(task_id)

        if "title" in changes:
            if changes["title"] is None:
                raise ErrInvalidInput("task title must not be null")
            title = changes["title"].strip()
            if not title:
                raise ErrInvalidInput("task title must not be empty")
            task.title = title

        if "priority" in changes:
            if changes["priority"] not in self.ALLOWED_PRIORITIES:
                raise ErrInvalidInput("priority must be low, medium or high")
            task.priority = changes["priority"]

        if "description" in changes:
            task.description = changes["description"]

        if "due_date" in changes:
            due_date = changes["due_date"]
            self._validate_due_date(due_date)
            task.due_date = due_date

        if "is_completed" in changes:
            if task.is_completed:
                raise ErrConflict("completed task cannot change its state again")
            if changes["is_completed"] is not True:
                raise ErrConflict("task state can only be changed to completed")
            task.is_completed = True

        await self._tasks.update(task)
        return await self._tasks.get_by_id(task_id)

    def _validate_due_date(self, due_date: datetime | None) -> None:
        if due_date is None:
            return
        if due_date.tzinfo is None or due_date.utcoffset() is None:
            raise ErrInvalidInput("due_date must include a timezone")
        if due_date <= self._now():
            raise ErrInvalidInput("due_date must be in the future")

    async def delete(self, task_id: int) -> None:
        await self._tasks.delete(task_id)
