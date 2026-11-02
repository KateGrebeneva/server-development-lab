from internal.domain import ErrNotFound, Subject
from internal.repository.postgres.db import (
    DBTX,
    normalize_page,
    rows_affected,
    translate_errors,
)


class PostgresSubjectRepository:
    def __init__(self, db: DBTX) -> None:
        self._db = db

    async def create(self, subject: Subject) -> Subject:
        query = """
            INSERT INTO subjects (user_id, name, color, category, time_studied_minutes)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, created_at, updated_at
        """
        with translate_errors():
            row = await self._db.fetchrow(
                query,
                subject.user_id,
                subject.name,
                subject.color,
                subject.category,
                subject.time_studied_minutes,
            )
        subject.id = row["id"]
        subject.created_at = row["created_at"]
        subject.updated_at = row["updated_at"]
        return subject

    async def get_by_id(self, subject_id: int) -> Subject:
        query = """
            SELECT id, user_id, name, color, category, time_studied_minutes,
                   created_at, updated_at
            FROM subjects
            WHERE id = $1
        """
        with translate_errors():
            row = await self._db.fetchrow(query, subject_id)
        if row is None:
            raise ErrNotFound(f"subject {subject_id}")
        return Subject(**dict(row))

    async def list(self, limit: int = 20, offset: int = 0) -> list[Subject]:
        limit, offset = normalize_page(limit, offset)
        query = """
            SELECT id, user_id, name, color, category, time_studied_minutes,
                   created_at, updated_at
            FROM subjects
            ORDER BY created_at DESC, id DESC
            LIMIT $1 OFFSET $2
        """
        with translate_errors():
            rows = await self._db.fetch(query, limit, offset)
        return [Subject(**dict(row)) for row in rows]

    async def update(self, subject: Subject) -> Subject:
        query = """
            UPDATE subjects
            SET name = $1, color = $2, category = $3, time_studied_minutes = $4,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $5
        """
        with translate_errors():
            status = await self._db.execute(
                query,
                subject.name,
                subject.color,
                subject.category,
                subject.time_studied_minutes,
                subject.id,
            )
        if rows_affected(status) == 0:
            raise ErrNotFound(f"subject {subject.id}")
        return subject

    async def delete(self, subject_id: int) -> None:
        query = "DELETE FROM subjects WHERE id = $1"
        with translate_errors():
            status = await self._db.execute(query, subject_id)
        if rows_affected(status) == 0:
            raise ErrNotFound(f"subject {subject_id}")
