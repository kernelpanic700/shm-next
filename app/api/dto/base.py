# =============================================================================
# shm-next — Base DTOs
# =============================================================================
"""
Базовые Pydantic-схемы для DTO.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Успешный ответ API."""
    success: bool = True
    message: str | None = None
    data: Any | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Ошибка API."""
    success: bool = False
    error: str
    details: dict | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "Validation failed",
                "details": {"field": "error message"},
                "timestamp": "2023-01-01T00:00:00Z",
            }
        }
    )


class Pagination(BaseModel):
    """Параметры пагинации."""
    page: int = Field(1, ge=1, description="Номер страницы (начиная с 1)")
    size: int = Field(20, ge=1, le=100, description="Размер страницы")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "size": 20,
            }
        }
    )


class PageResponse(BaseModel, Generic[T]):
    """Страничный ответ с данными и метаданными пагинации."""
    items: list[T]
    total: int = Field(ge=0, description="Общее количество элементов")
    page: int = Field(ge=1, description="Текущая страница")
    size: int = Field(ge=1, description="Размер страницы")
    pages: int = Field(ge=0, description="Общее количество страниц")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0,
            }
        }
    )


class IDResponse(BaseModel):
    """Ответ с идентификатором созданного объекта."""
    id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class TimestampMixin(BaseModel):
    """Миксин для полей времени создания и обновления."""
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
