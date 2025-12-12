from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from ..core.config import runtime
from ..core.logger import info, warn, error

ROOT = Path(runtime.workspace_root)


def resolve_path(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return p


def write_file(path: str, content: str, overwrite: bool = True) -> str:
    if not runtime.allow_write:
        warn(f"写入被禁用：{path}")
        return "write_disabled"
    p = resolve_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and not overwrite:
        warn(f"文件已存在且不覆盖：{p}")
        return "skipped"
    p.write_text(content, encoding="utf-8")
    info(f"写入文件: {p}")
    return str(p)


def read_file(path: str) -> Optional[str]:
    p = resolve_path(path)
    if not p.exists():
        warn(f"文件不存在：{p}")
        return None
    return p.read_text(encoding="utf-8", errors="ignore")


def make_dirs(path: str):
    p = resolve_path(path)
    p.mkdir(parents=True, exist_ok=True)
    info(f"创建目录: {p}")
    return str(p)

