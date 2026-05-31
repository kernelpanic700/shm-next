# =============================================================================
# shm-next - Default external actions
# =============================================================================
from __future__ import annotations

from string import Template
from typing import Any
from uuid import UUID

from app.infrastructure.db.unit_of_work import UnitOfWork
from app.infrastructure.external.action_registry import ActionRegistry
from app.infrastructure.security.secret_crypto import decrypt_secret


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render_template(body: str, context: dict[str, Any]) -> str:
    flattened = {
        "abonent_id": context.get("abonent_id") or "",
        "service_id": context.get("service_id") or "",
        "service_type": context.get("service_type") or "",
        "catalog_service_id": context.get("catalog_service_id") or "",
        "reason": context.get("reason") or "",
        "status": context.get("status") or "",
        "changes": context.get("changes") or "",
        "event_type": (context.get("event") or {}).get("type") if isinstance(context.get("event"), dict) else "",
    }
    rendered = Template(body).safe_substitute(flattened)
    return rendered.format_map(_SafeDict(flattened))


def _split_host(value: str) -> tuple[str | None, str]:
    if "@" not in value:
        return None, value
    user, host = value.split("@", 1)
    return user or None, host


async def _pick_server(uow: UnitOfWork, settings: dict[str, Any]):
    server_id = settings.get("server_id")
    if server_id:
        return await uow.servers.get(UUID(str(server_id)))

    group_id = settings.get("server_group_id")
    if not group_id:
        return None
    servers = await uow.servers.list_by_group(UUID(str(group_id)))
    return servers[0] if servers else None


def _rule_settings(payload: dict[str, Any]) -> dict[str, Any]:
    rule = payload.get("rule")
    if isinstance(rule, dict):
        nested_settings = rule.get("settings")
        if isinstance(nested_settings, dict):
            return nested_settings
        return rule

    settings = payload.get("settings")
    return settings if isinstance(settings, dict) else {}


async def execute_ssh(uow: UnitOfWork, **payload: Any) -> dict[str, Any]:
    """Execute SHM-style SSH action from spool payload."""
    try:
        import asyncssh
    except ImportError as exc:
        raise RuntimeError("asyncssh is required to execute SSH automation actions") from exc

    settings = _rule_settings(payload)
    server = await _pick_server(uow, settings)
    if server is None:
        raise ValueError("SSH action requires server_id or server_group_id with active servers")

    cmd = settings.get("command") or server.default_cmd
    template_id = settings.get("template_id")
    if template_id:
        template = await uow.command_templates.get(UUID(str(template_id)))
        if template is None:
            raise ValueError(f"Command template {template_id} not found")
        cmd = template.body

    if not cmd:
        raise ValueError("SSH action requires command or template")

    key = await uow.ssh_keys.get(server.key_id) if server.key_id else None
    if key is None:
        raise ValueError(f"Server {server.id} has no active SSH key")

    username, host = _split_host(server.host)
    rendered_cmd = _render_template(cmd, payload)
    private_key = decrypt_secret(key.private_key)
    passphrase = decrypt_secret(key.passphrase)
    client_keys = [asyncssh.import_private_key(private_key, passphrase=passphrase)]

    connect_kwargs: dict[str, Any] = {
        "host": host,
        "port": server.port,
        "username": username,
        "client_keys": client_keys,
        "known_hosts": None,
    }
    timeout = int((server.settings or {}).get("timeout") or settings.get("timeout") or 10)

    async with asyncssh.connect(**connect_kwargs) as conn:
        result = await conn.run(rendered_cmd, check=False, timeout=timeout)
        output = {
            "server_id": str(server.id),
            "command": rendered_cmd,
            "exit_status": result.exit_status,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.exit_status == 0,
        }
        if result.exit_status != 0:
            raise RuntimeError(f"SSH command failed with exit status {result.exit_status}: {result.stderr}")
        return output


def create_default_action_registry(uow: UnitOfWork) -> ActionRegistry:
    registry = ActionRegistry()
    registry.register("ssh.exec", lambda **payload: execute_ssh(uow, **payload))
    registry.register("local.noop", lambda **payload: {"status": "noop", "payload": payload})
    return registry
