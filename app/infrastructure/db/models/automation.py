# =============================================================================
# shm-next - Automation Models
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class SSHKeyModel(Base):
    """SSH key used by server transports."""

    __tablename__ = "ssh_keys"

    id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_key: Mapped[str] = mapped_column(Text, nullable=False)
    passphrase: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="1")


class ServerGroupModel(Base):
    """Group of servers that share transport settings."""

    __tablename__ = "server_groups"

    id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    transport: Mapped[str] = mapped_column(String(32), nullable=False, server_default="ssh")
    strategy: Mapped[str] = mapped_column(String(32), nullable=False, server_default="round_robin")
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="1")


class ServerModel(Base):
    """Managed server target."""

    __tablename__ = "servers"

    id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("server_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, server_default="22")
    key_id: Mapped[Any | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ssh_keys.id"), nullable=True)
    proxy_jump: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_cmd: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="1")


class CommandTemplateModel(Base):
    """Script/command template rendered before external execution."""

    __tablename__ = "command_templates"

    id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    transport: Mapped[str] = mapped_column(String(32), nullable=False, server_default="ssh")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="1")
