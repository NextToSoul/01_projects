"""PPCU TestBench — YAML 指令定义加载

从 protocol_defs/{产品}/commands.yaml 加载指令定义，
转换为 CommandDef 对象列表供协议编解码和 UI 使用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import CommandDef


def load_commands(product_dir: str | Path) -> list[CommandDef]:
    """加载产品支持的遥控指令定义。

    Args:
        product_dir: 产品协议目录路径（如 protocol_defs/nebula_ppcu）。

    Returns:
        CommandDef 列表。

    Raises:
        FileNotFoundError: commands.yaml 不存在。
    """
    path = Path(product_dir).resolve() / "commands.yaml"
    if not path.exists():
        raise FileNotFoundError(f"指令定义文件不存在: {path}")

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    commands: list[dict[str, Any]] = data.get("commands") or []
    return [_parse_cmd(c) for c in commands]


# ── 内部工具 ─────────────────────────────────────────────


def _parse_cmd(c: dict[str, Any]) -> CommandDef:
    return CommandDef(
        id=int(c["id"]),
        name=str(c.get("name", "")),
        category=str(c.get("category", "")),
        description=str(c.get("description", "")),
        data_length=int(c.get("data_length", 0)),
        response_type=c.get("response_type"),
    )
