# =============================================================================
# shm-next - CatalogService Repository Protocol
# =============================================================================
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.catalog_service import CatalogService


class CatalogServiceRepositoryProtocol(ABC):
    """Протокол репозитория каталожных услуг SHM."""

    @abstractmethod
    async def get(self, service_id: UUID) -> CatalogService | None:
        ...

    @abstractmethod
    async def get_orderable(self) -> list[CatalogService]:
        ...

    @abstractmethod
    async def list(
        self,
        category: str | None = None,
        include_deleted: bool = False,
    ) -> list[CatalogService]:
        ...

    @abstractmethod
    async def save(self, service: CatalogService) -> CatalogService:
        ...
