class DomainError(Exception):
    """Базовая ошибка предметной области."""


class ErrNotFound(DomainError):
    """Запись не найдена (HTTP 404)."""


class ErrAlreadyExists(DomainError):
    """Нарушение уникальности (HTTP 409)."""


class ErrConflict(DomainError):
    """Нарушение связей или занятый ресурс (HTTP 409)."""


class ErrInvalidInput(DomainError):
    """Нарушение CHECK, неверный формат значения (HTTP 400)."""
