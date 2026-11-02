import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from internal.domain import ErrConflict, ErrNotFound, StudySession
from internal.repository.postgres import PostgresStudySessionRepository
from internal.service.study_session_service import StudySessionService

START = datetime(2030, 1, 15, 10, 0, tzinfo=timezone.utc)


def make_session(user_id: int, start: datetime, minutes: int = 60) -> StudySession:
    return StudySession(
        user_id=user_id, goal="Подготовка", duration_minutes=minutes, scheduled_at=start
    )


async def test_schedule_creates_session(pool, user):
    service = StudySessionService(pool)
    session = await service.schedule(make_session(user.id, START))
    assert session.id is not None

    got = await PostgresStudySessionRepository(pool).get_by_id(session.id)
    assert got.scheduled_at == START


async def test_overlapping_session_is_rejected(pool, user):
    service = StudySessionService(pool)
    await service.schedule(make_session(user.id, START, minutes=60))

    # 10:30–11:30 пересекается с 10:00–11:00
    with pytest.raises(ErrConflict):
        await service.schedule(make_session(user.id, START + timedelta(minutes=30)))

    # 11:00–12:00 начинается ровно в момент окончания — пересечения нет
    await service.schedule(make_session(user.id, START + timedelta(minutes=60)))

    sessions = await PostgresStudySessionRepository(pool).list(limit=100)
    assert sum(1 for s in sessions if s.user_id == user.id) == 2


async def test_concurrent_overlapping_requests_only_one_succeeds(pool, user):
    service = StudySessionService(pool)
    results = await asyncio.gather(
        *(service.schedule(make_session(user.id, START)) for _ in range(5)),
        return_exceptions=True,
    )
    created = [r for r in results if isinstance(r, StudySession)]
    conflicts = [r for r in results if isinstance(r, ErrConflict)]
    assert len(created) == 1
    assert len(conflicts) == 4


async def test_schedule_for_missing_user_not_found(pool):
    with pytest.raises(ErrNotFound):
        await StudySessionService(pool).schedule(make_session(999_999_999, START))
