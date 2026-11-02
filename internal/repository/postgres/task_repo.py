from internal.domain import ErrNotFound, Task
from internal.repository.postgres.db import (
    DBTX,
    normalize_page,
    rows_affected,
    translate_errors,
)


class PostgresTaskRepository:
    def __init__(self, db: DBTX) -> None:
        self._db = db

    async def create(self, task: Task) -> Task:
        query = """
            INSERT INTO tasks (subject_id, title, description, priority, is_completed, due_date)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, created_at, updated_at
        """
        with translate_errors():
            row = await self._db.fetchrow(
                query,
                task.subject_id,
                task.title,
                task.description,
                task.priority,
                task.is_completed,
                task.due_date,
            )
        task.id = row["id"]
        task.created_at = row["created_at"]
        task.updated_at = row["updated_at"]
        return task

    async def get_by_id(self, task_id: int) -> Task:
        query = """
            SELECT id, subject_id, title, description, priority, is_completed,
                   due_date, created_at, updated_at
            FROM tasks
            WHERE id = $1
        """
        with translate_errors():
            row = await self._db.fetchrow(query, task_id)
        if row is None:
            raise ErrNotFound(f"task {task_id}")
        return Task(**dict(row))

    async def list(self, limit: int = 20, offset: int = 0) -> list[Task]:
        limit, offset = normalize_page(limit, offset)
        query = """
            SELECT id, subject_id, title, description, priority, is_completed,
                   due_date, created_at, updated_at
            FROM tasks
            ORDER BY created_at DESC, id DESC
            LIMIT $1 OFFSET $2
        """
        with translate_errors():
            rows = await self._db.fetch(query, limit, offset)
        return [Task(**dict(row)) for row in rows]

    async def update(self, task: Task) -> Task:
        query = """
            UPDATE tasks
            SET title = $1, description = $2, priority = $3, is_completed = $4,
                due_date = $5, updated_at = CURRENT_TIMESTAMP
            WHERE id = $6
        """
        with translate_errors():
            status = await self._db.execute(
                query,
                task.title,
                task.description,
                task.priority,
                task.is_completed,
                task.due_date,
                task.id,
            )
        if rows_affected(status) == 0:
            raise ErrNotFound(f"task {task.id}")
        return task

    async def delete(self, task_id: int) -> None:
        query = "DELETE FROM tasks WHERE id = $1"
        with translate_errors():
            status = await self._db.execute(query, task_id)
        if rows_affected(status) == 0:
            raise ErrNotFound(f"task {task_id}")
