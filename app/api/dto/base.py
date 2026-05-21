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