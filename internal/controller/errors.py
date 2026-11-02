from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from internal.domain import (
    DomainError,
    ErrAlreadyExists,
    ErrConflict,
    ErrInvalidInput,
    ErrNotFound,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    ErrNotFound: 404,
    ErrAlreadyExists: 409,
    ErrConflict: 409,
    ErrInvalidInput: 400,
}


class ErrorResponse(BaseModel):
    error: str
    detail: str

NOT_FOUND = {404: {"model": ErrorResponse, "description": "ErrNotFound — запись не найдена"}}
ALREADY_EXISTS = {409: {"model": ErrorResponse, "description": "ErrAlreadyExists — нарушение уникальности"}}
CONFLICT = {409: {"model": ErrorResponse, "description": "ErrConflict — нарушение связи или занятое время"}}
INVALID_INPUT = {400: {"model": ErrorResponse, "description": "ErrInvalidInput — нарушение CHECK, неверное значение"}}


def status_for(error: DomainError) -> int:
    for error_type, status in STATUS_BY_ERROR.items():
        if isinstance(error, error_type):
            return status
    return 500


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status_for(exc),
            content={"error": type(exc).__name__, "detail": str(exc)},
        )
