# =============================================================================
# shm-next — Error DTOs
# =============================================================================
"""
Схемы ошибок API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Детали ошибки."""
    type: str
    message: str
    field: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    """Стандартный ответ об ошибке."""
    success: bool = False
    error: str
    details: list[ErrorDetail] | None = None
    timestamp: datetime
    request_id: str | None = None
