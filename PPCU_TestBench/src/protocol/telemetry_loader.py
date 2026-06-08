"""PPCU TestBench — YAML 遥测参数定义加载

从 protocol_defs/{产品}/telemetry_{tm_type}.yaml 加载参数定义，
转换为 TmParamDef 对象列表供编解码使用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import TmParamDef


def load_tm_defs(product_dir: str | Path, tm_type: str) -> list[TmParamDef]:
    """加载指定遥测类型的参数定义。

    Args:
        product_dir: 产品协议目录路径（如 protocol_defs/nebula_ppcu）。
        tm_type: 遥测类型标识（tm1 / tm2 / query）。

    Returns:
        TmParamDef 列表。

    Raises:
        FileNotFoundError: YAML 文件不存在。
        ValueError: 文件中 tm_type 与请求不匹配。
    """
    path = Path(product_dir).resolve() / f"telemetry_{tm_type}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"遥测定义文件不存在: {path} (tm_type={tm_type})"
        )

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    if data.get("tm_type") != tm_type:
        raise ValueError(
            f"tm_type 不匹配: 期望 '{tm_type}'，"
            f"实际 '{data.get('tm_type')}'"
        )

    params: list[dict[str, Any]] = data.get("params") or []
    return [_parse_param(p) for p in params]


def load_enums(product_dir: str | Path) -> dict[str, dict[int, str]]:
    """加载枚举定义（enums.yaml）。

    Returns:
        枚举名 → {整数值: 文本标签} 的映射。文件不存在时返回空字典。
    """
    path = Path(product_dir).resolve() / "enums.yaml"
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    enums: dict[str, Any] = data.get("enums") or {}
    result: dict[str, dict[int, str]] = {}
    for enum_name, values in enums.items():
        parsed: dict[int, str] = {}
        for key, label in values.items():
            parsed[_to_int(key)] = label
        result[enum_name] = parsed
    return result


# ── 内部工具 ─────────────────────────────────────────────


def _parse_param(p: dict[str, Any]) -> TmParamDef:
    return TmParamDef(
        id=str(p.get("id", "")),
        name=str(p.get("name", "")),
        byte_offset=int(p.get("byte_offset", 0)),
        bit_offset=int(p.get("bit_offset", 0)),
        bit_length=int(p.get("bit_length", 0)),
        byte_length=int(p.get("byte_length", 2)),
        type=str(p.get("type", "uint16")),
        endian=str(p.get("endian", "big")),
        scale=float(p.get("scale", 1.0)),
        decimal_places=int(p.get("decimal_places", 2)),
        unit=str(p.get("unit", "")),
        enum_ref=p.get("enum_ref"),
        range_min=_to_float(p.get("range_min")),
        range_max=_to_float(p.get("range_max")),
    )


def _to_int(value: Any) -> int:
    """YAML 可能将 0x0 解析为字符串，统一转 int。"""
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    return int(value)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
