from internal.domain import ErrInvalidInput, Subject
from internal.repository.repository import SubjectRepository


class SubjectService:
    """Бизнес-операции над учебными предметами."""

    def __init__(self, subjects: SubjectRepository) -> None:
        self._subjects = subjects

    async def create(self, subject: Subject) -> Subject:
        subject.name = subject.name.strip()
        if not subject.name:
            raise ErrInvalidInput("subject name must not be empty")
        if subject.time_studied_minutes < 0:
            raise ErrInvalidInput("time_studied_minutes must be >= 0")
        return await self._subjects.create(subject)

    async def get(self, subject_id: int) -> Subject:
        return await self._subjects.get_by_id(subject_id)

    async def list(self, limit: int = 20, offset: int = 0) -> list[Subject]:
        return await self._subjects.list(max(1, min(limit, 100)), max(0, offset))

    async def update(self, subject_id: int, subject: Subject) -> Subject:
        subject.name = subject.name.strip()
        if not subject.name:
            raise ErrInvalidInput("subject name must not be empty")
        if subject.time_studied_minutes < 0:
            raise ErrInvalidInput("time_studied_minutes must be >= 0")
        subject.id = subject_id
        await self._subjects.update(subject)
        return await self._subjects.get_by_id(subject_id)

    async def delete(self, subject_id: int) -> None:
        await self._subjects.delete(subject_id)
