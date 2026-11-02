from internal.domain import ErrNotFound, User
from internal.repository.postgres.db import (
    DBTX,
    normalize_page,
    rows_affected,
    translate_errors,
)

class PostgresUserRepository:
    def __init__(self, db: DBTX) -> None:
        self._db = db

    async def create(self, user: User) -> User:
        query = """
            INSERT INTO users (email, password_hash, name, role, avatar_url, theme)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, created_at, updated_at
        """
        with translate_errors():
            row = await self._db.fetchrow(
                query,
                user.email,
                user.password_hash,
                user.name,
                user.role,
                user.avatar_url,
                user.theme,
            )
        user.id = row["id"]
        user.created_at = row["created_at"]
        user.updated_at = row["updated_at"]
        return user

    async def get_by_id(self, user_id: int) -> User:
        query = """
            SELECT id, email, password_hash, name, role, avatar_url, theme,
                   created_at, updated_at
            FROM users
            WHERE id = $1
        """
        with translate_errors():
            row = await self._db.fetchrow(query, user_id)
        if row is None:
            raise ErrNotFound(f"user {user_id}")
        return User(**dict(row))

    async def get_by_email(self, email: str) -> User:
        query = """
            SELECT id, email, password_hash, name, role, avatar_url, theme,
                   created_at, updated_at
            FROM users
            WHERE email = $1
        """
        with translate_errors():
            row = await self._db.fetchrow(query, email)
        if row is None:
            raise ErrNotFound("user with this email")
        return User(**dict(row))

    async def list(self, limit: int = 20, offset: int = 0) -> list[User]:
        limit, offset = normalize_page(limit, offset)
        query = """
            SELECT id, email, password_hash, name, role, avatar_url, theme,
                   created_at, updated_at
            FROM users
            ORDER BY created_at DESC, id DESC
            LIMIT $1 OFFSET $2
        """
        with translate_errors():
            rows = await self._db.fetch(query, limit, offset)
        return [User(**dict(row)) for row in rows]

    async def delete(self, user_id: int) -> None:
        query = "DELETE FROM users WHERE id = $1"
        with translate_errors():
            status = await self._db.execute(query, user_id)
        if rows_affected(status) == 0:
            raise ErrNotFound(f"user {user_id}")

    async def lock(self, user_id: int) -> None:
        """Блокирует строку пользователя до конца текущей транзакции."""
        query = "SELECT id FROM users WHERE id = $1 FOR UPDATE"
        with translate_errors():
            found = await self._db.fetchval(query, user_id)
        if found is None:
            raise ErrNotFound(f"user {user_id}")
