"""PPCU TestBench — 星云 PPCU RS422 协议编解码实现

实现 ProtocolInterface，完成帧构建、应答解析、遥测解码。

帧结构（通讯协议 A04）:
  指令帧:  EB 90 | APID(2) | Seq(2) | Len(2) | CmdID(2) | [Data] | CS(2)
  应答帧:  1A CF | APID(2) | Seq(2) | Len(2) | Telemetry   | CS(2)

校验: 从字节 2 到数据域末尾，累加和 → 取反 → 低 16bit → 大端。
"""

from __future__ import annotations

import struct
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .checksum import compute_checksum as _compute_checksum
from .command_loader import load_commands
from .interface import ProtocolInterface
from .models import Command, CommandDef, Response, TelemetryValue, TmParamDef
from .telemetry_loader import load_enums, load_tm_defs


class NebulaRS422Protocol(ProtocolInterface):
    """星云 400W 霍尔电推进 PPCU — RS422 协议实现。

    使用前先通过 build_request 构造指令帧，通过 parse_response
    解析 PPCU 应答，通过 decode_telemetry 提取工程量值。
    """

    COMMAND_HEADER = bytes([0xEB, 0x90])
    RESPONSE_HEADER = bytes([0x1A, 0xCF])
    COMMAND_APID = bytes([0x05, 0x20])

    # APID → 遥测类型映射（用于应答帧分发）
    _APID_TO_TM: dict[bytes, str] = {
        bytes([0x05, 0x25]): "tm1",
        bytes([0x05, 0x26]): "tm2",
        bytes([0x05, 0x21]): "query",
        bytes([0x05, 0x27]): "ack",
    }

    def __init__(self, product_dir: str | Path) -> None:
        self._product_dir = Path(product_dir)
        self._sequence: int = 0
        self._tm_params: dict[str, list[TmParamDef]] = {}
        self._command_defs: list[CommandDef] | None = None
        self._enums: dict[str, dict[int, str]] = {}

    # ── ProtocolInterface ────────────────────────────────────

    @property
    def product_name(self) -> str:
        return "星云 400W 霍尔电推进 PPCU"

    def build_request(self, cmd: Command) -> bytes:
        """组装指令帧。

        帧格式（不含数据域时 10 字节固定头 + 2 字节校验）:
          [EB 90] [05 20] [Seq] [Len] [CmdID_hi, CmdID_lo] [Dat...] [CS]
        """
        cmd_id_bytes = cmd.cmd_id.to_bytes(2, byteorder="big")

        # 数据域 = 指令码 + 参数
        data = bytearray(cmd_id_bytes)
        if cmd.params:
            for v in cmd.params.values():
                data.extend(self._pack_param(v))

        # 帧长 = 帧头(4) + 序列(2) + 长度域(2) + 数据域 + 校验(2)
        # 长度域从 APID 开始到校验前
        frame = bytearray()
        frame.extend(self.COMMAND_HEADER)          #  0-1: 帧头
        frame.extend(self.COMMAND_APID)             #  2-3: APID
        frame.extend(self._next_sequence())          #  4-5: 序列号
        frame.extend((len(data) // 2).to_bytes(2, "big"))  #  6-7: 长度(16-bit words)
        frame.extend(data)                           #  8+:  数据域
        frame.extend(self.compute_checksum(bytes(frame[2:])))  # 末尾: 校验

        return bytes(frame)

    def parse_response(self, raw: bytes) -> Response | None:
        """解析 PPCU 应答帧。"""
        if len(raw) < 10:  # 最短帧: 帧头 + APID + Seq + Len + CS
            return None
        if raw[:2] != self.RESPONSE_HEADER:
            return None

        apid = raw[2:4]
        tm_type = self._APID_TO_TM.get(apid)
        if tm_type is None:
            return Response(raw=raw, parsed=False)

        data_len = int.from_bytes(raw[6:8], "big")
        if len(raw) < data_len + 8:
            return None  # 截断

        if not self.verify_checksum(raw):
            return Response(raw=raw, parsed=False)

        # 应答数据域（不含校验）: 从字节 8 开始，共 data_len - 2 字节
        body = raw[8 : -2]

        if tm_type in ("tm1", "tm2", "query"):
            decoded = self.decode_telemetry(body, tm_type)
            return Response(
                raw=raw, parsed=True, tm_type=tm_type, data=decoded
            )

        return Response(raw=raw, parsed=True, tm_type=tm_type)

    def decode_telemetry(
        self, raw: bytes, tm_type: str
    ) -> dict[str, TelemetryValue]:
        """从遥测应答的数据域解码参数。"""
        params = self.get_tm_params(tm_type)
        enums = self._get_enums()
        result: dict[str, TelemetryValue] = {}

        for p in params:
            try:
                raw_value = self._extract_raw(data=raw, param=p)
                eng_value: float | str
                unit: str
                status: str

                if p.type == "enum":
                    eng_value = self._resolve_enum(raw_value, p, enums)
                    unit = "-"
                    status = "normal"
                else:
                    eng_value = round(float(raw_value) * p.scale, p.decimal_places)
                    unit = p.unit
                    status = self._check_limits(eng_value, p)

                result[p.id] = TelemetryValue(
                    param_id=p.id,
                    name=p.name,
                    raw_value=int(raw_value) if not isinstance(raw_value, float) else raw_value,
                    eng_value=eng_value,
                    unit=unit,
                    status=status,
                )
            except (IndexError, ValueError, struct.error):
                result[p.id] = TelemetryValue(
                    param_id=p.id, name=p.name, status="error"
                )

        return result

    def compute_checksum(self, payload: bytes) -> bytes:
        """委托给 checksum 模块。"""
        return _compute_checksum(payload)

    def get_tm_params(self, tm_type: str) -> Sequence[TmParamDef]:
        if tm_type not in self._tm_params:
            self._tm_params[tm_type] = load_tm_defs(
                self._product_dir, tm_type
            )
        return self._tm_params[tm_type]

    def get_commands(self) -> Sequence[CommandDef]:
        if self._command_defs is None:
            self._command_defs = load_commands(self._product_dir)
        return self._command_defs

    # ── 内部方法 ────────────────────────────────────────────

    def _next_sequence(self) -> bytes:
        """14 位源包序列计数，自动递增、溢出归零。"""
        seq = self._sequence
        self._sequence = (self._sequence + 1) & 0x3FFF
        flags = 3  # CCSDS 分组标志: 0b11 = standalone packet
        return ((flags << 14) | seq).to_bytes(2, byteorder="big")

    def _get_enums(self) -> dict[str, dict[int, str]]:
        if not self._enums:
            self._enums = load_enums(self._product_dir)
        return self._enums

    @staticmethod
    def _extract_raw(data: bytes, param: TmParamDef) -> int | float:
        """从遥测数据中提取参数的原始值。"""
        # 位域方式（enum）: 按 bit_offset + bit_length 提取
        if param.bit_length > 0:
            byte_val = data[param.byte_offset]
            mask = (1 << param.bit_length) - 1
            return (byte_val >> param.bit_offset) & mask

        # 字节方式（uint16 / int16 / float32）
        chunk = data[param.byte_offset : param.byte_offset + param.byte_length]
        if len(chunk) < param.byte_length:
            chunk = chunk.ljust(param.byte_length, b"\x00")

        if param.type == "float32":
            return struct.unpack(">f", chunk[:4])[0]

        return int.from_bytes(
            chunk[:param.byte_length],
            byteorder=param.endian if hasattr(param, "endian") else "big",
            signed=(param.type == "int16"),
        )

    @staticmethod
    def _resolve_enum(
        raw_value: int, param: TmParamDef, enums: dict[str, dict[int, str]]
    ) -> str:
        if param.enum_ref and param.enum_ref in enums:
            return enums[param.enum_ref].get(raw_value, f"0x{raw_value:X}")
        return f"0x{raw_value:X}"

    @staticmethod
    def _check_limits(value: float, param: TmParamDef) -> str:
        if param.range_min is not None and value < param.range_min:
            return "warning"
        if param.range_max is not None and value > param.range_max:
            return "warning"
        return "normal"

    @staticmethod
    def _pack_param(value: Any) -> bytes:
        """将参数值打包为帧中的字节。"""
        if isinstance(value, int):
            return value.to_bytes(2, "big")
        if isinstance(value, float):
            return struct.pack(">f", value)
        if isinstance(value, bytes):
            return value
        if isinstance(value, bool):
            return b"\x01" if value else b"\x00"
        return str(value).encode("utf-8")
