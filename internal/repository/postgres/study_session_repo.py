from datetime import datetime

from internal.domain import ErrNotFound, StudySession
from internal.repository.postgres.db import (
    DBTX,
    normalize_page,
    rows_affected,
    translate_errors,
)


class PostgresStudySessionRepository:
    def __init__(self, db: DBTX) -> None:
        self._db = db

    async def create(self, session: StudySession) -> StudySession:
        query = """
            INSERT INTO study_sessions (
                user_id, subject_id, goal, work_interval, short_break, long_break,
                intervals_count, duration_minutes, status, scheduled_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, created_at, updated_at
        """
        with translate_errors():
            row = await self._db.fetchrow(
                query,
                session.user_id,
                session.subject_id,
                session.goal,
                session.work_interval,
                session.short_break,
                session.long_break,
                session.intervals_count,
                session.duration_minutes,
                session.status,
                session.scheduled_at,
            )
        session.id = row["id"]
        session.created_at = row["created_at"]
        session.updated_at = row["updated_at"]
        return session

    async def get_by_id(self, session_id: int) -> StudySession:
        query = """
            SELECT id, user_id, subject_id, goal, work_interval, short_break, long_break,
                   intervals_count, duration_minutes, status, scheduled_at,
                   started_at, completed_at, created_at, updated_at
            FROM study_sessions
            WHERE id = $1
        """
        with translate_errors():
            row = await self._db.fetchrow(query, session_id)
        if row is None:
            raise ErrNotFound(f"study session {session_id}")
        return StudySession(**dict(row))

    async def list(self, limit: int = 20, offset: int = 0) -> list[StudySession]:
        limit, offset = normalize_page(limit, offset)
        query = """
            SELECT id, user_id, subject_id, goal, work_interval, short_break, long_break,
                   intervals_count, duration_minutes, status, scheduled_at,
                   started_at, completed_at, created_at, updated_at
            FROM study_sessions
            ORDER BY created_at DESC, id DESC
            LIMIT $1 OFFSET $2
        """
        with translate_errors():
            rows = await self._db.fetch(query, limit, offset)
        return [StudySession(**dict(row)) for row in rows]

    async def delete(self, session_id: int) -> None:
        query = "DELETE FROM study_sessions WHERE id = $1"
        with translate_errors():
            status = await self._db.execute(query, session_id)
        if rows_affected(status) == 0:
            raise ErrNotFound(f"study session {session_id}")

    async def has_overlap(self, user_id: int, start: datetime, end: datetime) -> bool:
        """Есть ли у пользователя активная сессия, пересекающая интервал [start, end)."""
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM study_sessions
                WHERE user_id = $1
                  AND status IN ('planned', 'in_progress')
                  AND scheduled_at < $3
                  AND scheduled_at + make_interval(mins => duration_minutes) > $2
            )
        """
        with translate_errors():
            return await self._db.fetchval(query, user_id, start, end)
