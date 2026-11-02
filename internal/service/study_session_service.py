from datetime import timedelta

import asyncpg

from internal.domain import ErrConflict, ErrInvalidInput, StudySession
from internal.repository.postgres import (
    PostgresStudySessionRepository,
    PostgresUserRepository,
    with_tx,
)

class StudySessionService:
    """Планирование учебных сессий без пересечения по времени."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def schedule(self, session: StudySession) -> StudySession:
        if session.scheduled_at is None:
            raise ErrInvalidInput("scheduled_at is required")
        start = session.scheduled_at
        end = start + timedelta(minutes=session.duration_minutes)

        async def operation(tx: asyncpg.Connection) -> StudySession:
            users = PostgresUserRepository(tx)
            sessions = PostgresStudySessionRepository(tx)

            await users.lock(session.user_id)
            if await sessions.has_overlap(session.user_id, start, end):
                raise ErrConflict("study session overlaps with another session")
            return await sessions.create(session)

        return await with_tx(self._pool, operation)
