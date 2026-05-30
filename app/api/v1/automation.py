# =============================================================================
# shm-next - API v1: Automation
# =============================================================================
from __future__ import annotations

from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from app.api.dependencies import provide_uow_dependency
from app.api.dto.requests import (
    CommandTemplateCreateRequest,
    CommandTemplateUpdateRequest,
    ServerCreateRequest,
    ServerGroupCreateRequest,
    ServerGroupUpdateRequest,
    ServerUpdateRequest,
    SSHKeyCreateRequest,
    SSHKeyUpdateRequest,
)
from app.api.dto.responses import (
    AutomationListResponse,
    CommandTemplateResponse,
    ServerGroupResponse,
    ServerResponse,
    SSHKeyResponse,
)
from app.infrastructure.db.models import CommandTemplateModel, ServerGroupModel, ServerModel, SSHKeyModel
from app.infrastructure.db.unit_of_work import UnitOfWork


def _list_response(items: list, response_model: type) -> AutomationListResponse:
    return AutomationListResponse(
        items=[response_model.model_validate(item, from_attributes=True).model_dump() for item in items],
        total=len(items),
    )


class AutomationController(Controller):
    """SHM-style automation settings: SSH keys, server groups, servers and script templates."""

    path = "/automation"
    tags = ["Automation"]
    dependencies = {"uow": Provide(provide_uow_dependency)}

    @get("/ssh-keys", summary="SSH keys")
    async def list_ssh_keys(self, uow: UnitOfWork) -> AutomationListResponse:
        return _list_response(await uow.ssh_keys.list_active(), SSHKeyResponse)

    @post("/ssh-keys", summary="Create SSH key", status_code=HTTP_201_CREATED)
    async def create_ssh_key(self, data: SSHKeyCreateRequest, uow: UnitOfWork) -> SSHKeyResponse:
        model = SSHKeyModel(**data.model_dump())
        saved = await uow.ssh_keys.save(model)
        await uow.commit()
        return SSHKeyResponse.model_validate(saved, from_attributes=True)

    @patch("/ssh-keys/{key_id:uuid}", summary="Update SSH key")
    async def update_ssh_key(self, key_id: UUID, data: SSHKeyUpdateRequest, uow: UnitOfWork) -> SSHKeyResponse:
        model = await uow.ssh_keys.get(key_id)
        if model is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="SSH key not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(model, field, value)
        model.version += 1
        saved = await uow.ssh_keys.save(model)
        await uow.commit()
        return SSHKeyResponse.model_validate(saved, from_attributes=True)

    @delete("/ssh-keys/{key_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_ssh_key(self, key_id: UUID, uow: UnitOfWork) -> None:
        if not await uow.ssh_keys.soft_delete(key_id):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="SSH key not found")
        await uow.commit()

    @get("/server-groups", summary="Server groups")
    async def list_server_groups(self, uow: UnitOfWork) -> AutomationListResponse:
        return _list_response(await uow.server_groups.list_active(), ServerGroupResponse)

    @post("/server-groups", summary="Create server group", status_code=HTTP_201_CREATED)
    async def create_server_group(self, data: ServerGroupCreateRequest, uow: UnitOfWork) -> ServerGroupResponse:
        model = ServerGroupModel(**data.model_dump())
        saved = await uow.server_groups.save(model)
        await uow.commit()
        return ServerGroupResponse.model_validate(saved, from_attributes=True)

    @patch("/server-groups/{group_id:uuid}", summary="Update server group")
    async def update_server_group(
        self,
        group_id: UUID,
        data: ServerGroupUpdateRequest,
        uow: UnitOfWork,
    ) -> ServerGroupResponse:
        model = await uow.server_groups.get(group_id)
        if model is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Server group not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(model, field, value)
        model.version += 1
        saved = await uow.server_groups.save(model)
        await uow.commit()
        return ServerGroupResponse.model_validate(saved, from_attributes=True)

    @delete("/server-groups/{group_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_server_group(self, group_id: UUID, uow: UnitOfWork) -> None:
        if not await uow.server_groups.soft_delete(group_id):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Server group not found")
        await uow.commit()

    @get("/servers", summary="Servers")
    async def list_servers(self, uow: UnitOfWork) -> AutomationListResponse:
        return _list_response(await uow.servers.list_active(), ServerResponse)

    @post("/servers", summary="Create server", status_code=HTTP_201_CREATED)
    async def create_server(self, data: ServerCreateRequest, uow: UnitOfWork) -> ServerResponse:
        model = ServerModel(**data.model_dump())
        saved = await uow.servers.save(model)
        await uow.commit()
        return ServerResponse.model_validate(saved, from_attributes=True)

    @patch("/servers/{server_id:uuid}", summary="Update server")
    async def update_server(self, server_id: UUID, data: ServerUpdateRequest, uow: UnitOfWork) -> ServerResponse:
        model = await uow.servers.get(server_id)
        if model is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Server not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(model, field, value)
        model.version += 1
        saved = await uow.servers.save(model)
        await uow.commit()
        return ServerResponse.model_validate(saved, from_attributes=True)

    @delete("/servers/{server_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_server(self, server_id: UUID, uow: UnitOfWork) -> None:
        if not await uow.servers.soft_delete(server_id):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Server not found")
        await uow.commit()

    @get("/templates", summary="Command templates")
    async def list_templates(self, uow: UnitOfWork) -> AutomationListResponse:
        return _list_response(await uow.command_templates.list_active(), CommandTemplateResponse)

    @post("/templates", summary="Create command template", status_code=HTTP_201_CREATED)
    async def create_template(self, data: CommandTemplateCreateRequest, uow: UnitOfWork) -> CommandTemplateResponse:
        model = CommandTemplateModel(**data.model_dump())
        saved = await uow.command_templates.save(model)
        await uow.commit()
        return CommandTemplateResponse.model_validate(saved, from_attributes=True)

    @patch("/templates/{template_id:uuid}", summary="Update command template")
    async def update_template(
        self,
        template_id: UUID,
        data: CommandTemplateUpdateRequest,
        uow: UnitOfWork,
    ) -> CommandTemplateResponse:
        model = await uow.command_templates.get(template_id)
        if model is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Template not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(model, field, value)
        model.version += 1
        saved = await uow.command_templates.save(model)
        await uow.commit()
        return CommandTemplateResponse.model_validate(saved, from_attributes=True)

    @delete("/templates/{template_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_template(self, template_id: UUID, uow: UnitOfWork) -> None:
        if not await uow.command_templates.soft_delete(template_id):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Template not found")
        await uow.commit()
