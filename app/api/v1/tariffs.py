"""
Роутер для управления тарифами.
"""
from __future__ import annotations

from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from app.api.dependencies import get_tariff_service, provide_uow_dependency
from app.api.dto.requests import TariffCreateRequest, TariffUpdateRequest
from app.api.dto.responses import TariffListResponse, TariffResponse
from app.core.application.tariffs.tariff_service import TariffService
from app.infrastructure.db.unit_of_work import UnitOfWork


class TariffController(Controller):
    """Контроллер для управления тарифами."""

    path = "/v1/tariffs"
    tags = ["Tariffs"]

    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "tariff_service": Provide(get_tariff_service),
    }

    @get("/", summary="Список тарифов")
    async def list_tariffs(
        self,
        tariff_service: TariffService,
        active_only: bool = True,
    ) -> TariffListResponse:
        """Получить список тарифов."""
        tariffs = await tariff_service.list_tariffs(active_only=active_only)
        return TariffListResponse(
            items=[TariffResponse.model_validate(t, from_attributes=True) for t in tariffs],
            total=len(tariffs),
        )

    @get("/{tariff_id:uuid}", summary="Получить тариф по ID")
    async def get_tariff(
        self, tariff_id: UUID, tariff_service: TariffService
    ) -> TariffResponse:
        """Получить тариф по ID."""
        tariff = await tariff_service.get_tariff(tariff_id)
        if not tariff:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tariff not found")
        return TariffResponse.model_validate(tariff, from_attributes=True)

    @get("/name/{name:str}", summary="Поиск тарифа по имени")
    async def get_by_name(
        self, name: str, tariff_service: TariffService
    ) -> TariffResponse:
        """Найти тариф по имени."""
        tariff = await tariff_service.get_by_name(name)
        if not tariff:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tariff not found")
        return TariffResponse.model_validate(tariff, from_attributes=True)

    @post("/", summary="Создать новый тариф", status_code=HTTP_201_CREATED)
    async def create_tariff(
        self, data: TariffCreateRequest, uow: UnitOfWork, tariff_service: TariffService
    ) -> TariffResponse:
        """Создать новый тариф."""
        async with uow:
            tariff = await tariff_service.create_tariff(data=data)
            await uow.commit()
            return TariffResponse.model_validate(tariff, from_attributes=True)

    @patch("/{tariff_id:uuid}", summary="Обновить тариф")
    async def update_tariff(
        self,
        tariff_id: UUID,
        data: TariffUpdateRequest,
        uow: UnitOfWork,
        tariff_service: TariffService,
    ) -> TariffResponse:
        """Обновить тариф."""
        async with uow:
            tariff = await tariff_service.update_tariff(tariff_id=tariff_id, data=data)
            await uow.commit()
            return TariffResponse.model_validate(tariff, from_attributes=True)

    @delete("/{tariff_id:uuid}", summary="Деактивировать тариф", status_code=HTTP_204_NO_CONTENT)
    async def deactivate_tariff(
        self, tariff_id: UUID, uow: UnitOfWork, tariff_service: TariffService
    ) -> None:
        """Деактивировать тариф (мягкое удаление)."""
        async with uow:
            await tariff_service.deactivate_tariff(tariff_id)
            await uow.commit()
