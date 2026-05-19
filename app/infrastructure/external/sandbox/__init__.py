# =============================================================================
# shm-next — Plugin Sandbox
# =============================================================================
"""
Изолированная среда выполнения плагинов.

Использует subprocess с ограничениями:
- rlimit (CPU, memory, file size)
- seccomp (ограничение системных вызовов)
- Таймаут выполнения
- Изоляция файловой системы
"""

from app.infrastructure.external.sandbox.exceptions import SandboxError
from app.infrastructure.external.sandbox.executor import SandboxExecutor

__all__ = ["SandboxError", "SandboxExecutor"]
