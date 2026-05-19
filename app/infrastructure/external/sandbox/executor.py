# =============================================================================
# shm-next — Sandbox Executor
# =============================================================================
"""
Исполнитель кода в изолированном subprocess.

Ограничения:
- CPU time (RLIMIT_CPU)
- Virtual memory (RLIMIT_AS)
- File size (RLIMIT_FSIZE)
- Process count (RLIMIT_NPROC)
- seccomp-bpf фильтр системных вызовов
- Таймаут wall-clock
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import tempfile
import textwrap
from typing import Any

import structlog

logger = structlog.get_logger("sandbox")


class SandboxLimits:
    """
    Ограничения ресурсов для sandbox.

    Значения по умолчанию консервативны для защиты хост-системы.
    """

    def __init__(
        self,
        cpu_time: float = 5.0,        # seconds
        memory: int = 256 * 1024 * 1024,  # 256 MB
        file_size: int = 10 * 1024 * 1024,  # 10 MB
        max_processes: int = 4,
        wall_timeout: float = 30.0,    # seconds
    ) -> None:
        self.cpu_time = cpu_time
        self.memory = memory
        self.file_size = file_size
        self.max_processes = max_processes
        self.wall_timeout = wall_timeout


class SandboxError(Exception):
    """Ошибка выполнения в sandbox."""
    pass


class SandboxTimeoutError(SandboxError):
    """Превышено время выполнения."""
    pass


class SandboxResourceError(SandboxError):
    """Превышен лимит ресурсов."""
    pass


class SandboxSecurityError(SandboxError):
    """Обнаружена попытка нарушения безопасности."""
    pass


class SandboxExecutor:
    """
    Исполнитель Python-кода в изолированном subprocess.

    Архитектура:
    1. Код плагина записывается во временный файл
    2. Запускается subprocess с ограничениями через preexec_fn
    3. Результат возвращается через stdout в JSON-формате
    4. subprocess уничтожается после выполнения или таймаута
    """

    # Разрешённые системные вызовы для seccomp
    ALLOWED_SYSCALLS = [
        "read", "write", "open", "close", "stat", "fstat",
        "lstat", "poll", "lseek", "mmap", "mprotect", "munmap",
        "brk", "rt_sigaction", "rt_sigprocmask", "ioctl",
        "pread64", "pwrite64", "access", "pipe", "select",
        "dup", "dup2", "getpid", "getppid", "getuid", "getgid",
        "geteuid", "getegid", "exit_group", "futex", "set_robust_list",
        "getrandom", "execve", "unlink", "mkdir", "rmdir",
        "readlink", "clock_gettime", "getcwd", "chdir",
    ]

    def __init__(
        self,
        limits: SandboxLimits | None = None,
        python_path: str | None = None,
    ) -> None:
        self._limits = limits or SandboxLimits()
        self._python_path = python_path or sys.executable

    def execute(
        self,
        code: str,
        input_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Синхронное выполнение кода в sandbox.

        Args:
            code: Python-код для выполнения
            input_data: Входные данные (передаются через stdin)
            timeout: Переопределение таймаута (по умолчанию из limits)

        Returns:
            dict: Результат выполнения

        Raises:
            SandboxTimeoutError: При превышении времени
            SandboxResourceError: При превышении ресурсов
            SandboxSecurityError: При обнаружении нарушения безопасности
            SandboxError: При других ошибках
        """
        timeout = timeout or self._limits.wall_timeout

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "plugin.py")
            output_path = os.path.join(tmpdir, "output.json")

            # Формируем скрипт плагина
            full_code = self._wrap_code(code, output_path, input_data or {})

            with open(script_path, "w") as f:
                f.write(full_code)

            try:
                result = self._run_subprocess(
                    script_path=script_path,
                    timeout=timeout,
                )
                return result
            except subprocess.TimeoutExpired:
                raise SandboxTimeoutError(
                    f"Plugin execution timed out after {timeout}s"
                )

    async def execute_async(
        self,
        code: str,
        input_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Асинхронное выполнение кода в sandbox.

        Использует asyncio subprocess для неблокирующего выполнения.
        """
        import asyncio

        timeout = timeout or self._limits.wall_timeout

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "plugin.py")
            output_path = os.path.join(tmpdir, "output.json")

            full_code = self._wrap_code(code, output_path, input_data or {})

            with open(script_path, "w") as f:
                f.write(full_code)

            try:
                proc = await asyncio.create_subprocess_exec(
                    self._python_path,
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    preexec_fn=lambda: self._apply_restrictions(),
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=timeout,
                    )
                except TimeoutError:
                    proc.kill()
                    raise SandboxTimeoutError(
                        f"Plugin execution timed out after {timeout}s"
                    )

                return self._parse_result(stdout, stderr, proc.returncode)

            except FileNotFoundError:
                raise SandboxError("Python interpreter not found")

    def _run_subprocess(self, script_path: str, timeout: float) -> dict[str, Any]:
        """Запуск subprocess с ограничениями."""
        try:
            result = subprocess.run(
                [self._python_path, script_path],
                capture_output=True,
                timeout=timeout,
                preexec_fn=self._apply_restrictions,
            )
            return self._parse_result(
                result.stdout, result.stderr, result.returncode
            )
        except subprocess.TimeoutExpired:
            raise SandboxTimeoutError(
                f"Plugin execution timed out after {timeout}s"
            )
        except FileNotFoundError:
            raise SandboxError("Python interpreter not found")

    def _apply_restrictions(self) -> None:
        """
        Применение ограничений к subprocess.

        Вызывается в дочернем процессе ПЕРЕД exec.
        """
        # === Resource Limits (rlimit) ===
        # CPU time (секунды)
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (int(self._limits.cpu_time), int(self._limits.cpu_time) + 5),
        )

        # Virtual memory (байты)
        resource.setrlimit(
            resource.RLIMIT_AS,
            (self._limits.memory, self._limits.memory),
        )

        # File size (байты)
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (self._limits.file_size, self._limits.file_size),
        )

        # Max processes
        resource.setrlimit(
            resource.RLIMIT_NPROC,
            (self._limits.max_processes, self._limits.max_processes),
        )

        # === seccomp (если доступен) ===
        self._apply_seccomp()

    def _apply_seccomp(self) -> None:
        """
        Применение seccomp BPF фильтра.

        Блокирует все системные вызовы, кроме явно разрешённых.
        """
        try:
            import seccomp

            filter_instance = seccomp.ScmpFilter(
                default_action=seccomp.KILL
            )

            for syscall_name in self.ALLOWED_SYSCALLS:
                try:
                    seccomp.Syscall.resolve(syscall_name)
                    filter_instance.add_rule(
                        seccomp.ALLOW, syscall_name
                    )
                except (OSError, ValueError):
                    # Не все syscall доступны на данной платформе
                    pass

            filter_instance.load()

        except ImportError:
            logger.warning(
                "seccomp not available — skipping syscall filtering",
                hint="Install scapy or libseccomp for enhanced security",
            )
        except Exception as exc:
            logger.warning(
                "Failed to apply seccomp filter",
                error=str(exc),
            )

    def _wrap_code(
        self,
        code: str,
        output_path: str,
        input_data: dict[str, Any],
    ) -> str:
        """
        Оборачивает код плагина в безопасную обёртку.

        Обёртка:
        1. Устанавливает ограничения на импорты
        2. Перехватывает исключения
        3. Записывает результат в JSON-файл
        """
        return f"""
import json
import sys
import builtins

# Ограничение опасных встроенных функций
_RESTRICTED_BUILTINS = {{
    'open', 'exec', 'eval', 'compile', '__import__',
    'input', 'breakpoint', 'globals', 'locals', 'vars',
}}

_original_builtins = builtins.__dict__.copy()

class RestrictedBuiltins:
    def __getattr__(self, name):
        if name in _RESTRICTED_BUILTINS:
            raise RuntimeError(f"Access to '{{name}}' is not allowed in sandbox")
        return _original_builtins[name]

builtins.__dict__ = RestrictedBuiltins()

# Входные данные
_input_data = {json.dumps(input_data)}

# Результат выполнения
_result = {{
    "success": False,
    "output": None,
    "error": None,
}}

try:
    # === Пользовательский код ===
{textwrap.indent(code, '    ')}

    _result["success"] = True
    _result["output"] = "Plugin executed successfully"

except Exception as e:
    _result["error"] = str(e)
    _result["error_type"] = type(e).__name__

# Записываем результат
with open("{output_path}", "w") as f:
    json.dump(_result, f)
"""

    def _parse_result(
        self,
        stdout: bytes,
        stderr: bytes,
        returncode: int,
    ) -> dict[str, Any]:
        """Парсинг результата выполнения."""
        stderr_str = stderr.decode("utf-8", errors="replace")

        if returncode != 0:
            return {
                "success": False,
                "error": stderr_str or f"Process exited with code {returncode}",
                "returncode": returncode,
            }

        return {
            "success": True,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr_str,
        }
