from __future__ import annotations
import subprocess
from typing import Optional, Tuple
from ..core.config import runtime
from ..core.logger import info, warn, error

# 仅允许安全前缀命令，拒绝 npm/npx/yarn/pnpm/git/curl/wget 等
_ALLOWED_PREFIXES = (
    "python ",
    "py ",
    "pip ",
    "pip3 ",
    "mkdir ",
    "md ",
)


def _allowed(command: str) -> bool:
    c = command.strip().lower()
    return any(c.startswith(p) for p in _ALLOWED_PREFIXES)


def run(command: str, cwd: Optional[str] = None, timeout: int = 180) -> tuple[int, str, str]:
    if not runtime.allow_shell:
        warn(f"Shell 执行被禁用：{command}")
        return 0, "", ""
    if not _allowed(command):
        warn(f"Shell 命令不在白名单内，已拒绝：{command}")
        return 0, "", "blocked"
    info(f"执行命令: {command}")
    try:
        proc = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            warn(f"命令退出码 {proc.returncode}\nSTDERR: {proc.stderr[:500]}")
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        error("命令超时")
        return 124, "", "timeout"

