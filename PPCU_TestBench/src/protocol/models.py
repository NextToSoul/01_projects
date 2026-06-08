"""PPCU TestBench — 协议层数据模型

Command / Response / TelemetryValue / TmParamDef / CommandDef
协议层的核心类型定义，所有模块共用同一组模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Command:
    """构建完成的指令对象（已含具体参数值），准备发送。"""

    cmd_id: int
    name: str
    params: dict[str, Any] | None = None


@dataclass
class CommandDef:
    """指令定义（来自 commands.yaml）。"""

    id: int
    name: str
    category: str
    description: str = ""
    data_length: int = 0
    response_type: str | None = None


@dataclass
class Response:
    """PPCU 应答帧解析结果。"""

    raw: bytes
    parsed: bool = False
    tm_type: str | None = None
    data: dict[str, Any] | None = None


@dataclass
class TelemetryValue:
    """单个遥测参数的解析结果（含工程量转换）。"""

    param_id: str
    name: str
    raw_value: int = 0
    eng_value: float | str = ""
    unit: str = ""
    status: str = "normal"


@dataclass
class TmParamDef:
    """遥测参数定义（来自 telemetry_*.yaml）。"""

    id: str
    name: str
    byte_offset: int = 0
    bit_offset: int = 0
    bit_length: int = 0
    byte_length: int = 2
    type: str = "uint16"  # uint16 | int16 | float32 | enum
    endian: str = "big"
    scale: float = 1.0
    decimal_places: int = 2
    unit: str = ""
    enum_ref: str | None = None
    range_min: float | None = None
    range_max: float | None = None
