"""PPCU TestBench — 协议层抽象接口

ProtocolInterface 定义每个产品协议实现的契约。
子类（如 NebulaRS422Protocol）需实现所有 @abstractmethod 方法。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .models import Command, CommandDef, Response, TelemetryValue, TmParamDef


class ProtocolInterface(ABC):
    """协议层抽象。

    每个产品（星云 PPCU、后续产品 B/C 等）实现一个子类。
    子类需重写所有 @abstractmethod 方法。
    """

    @property
    @abstractmethod
    def product_name(self) -> str:
        """产品名称标识，用于 UI 显示和日志。"""

    @abstractmethod
    def build_request(self, cmd: Command) -> bytes:
        """将指令对象打包为待发送的字节帧。

        Args:
            cmd: 指令对象（含指令码和参数）。

        Returns:
            完整帧字节（帧头 + 数据域 + 校验和）。
        """

    @abstractmethod
    def parse_response(self, raw: bytes) -> Response | None:
        """解析 PPCU 应答帧。

        Args:
            raw: 收到的原始字节。

        Returns:
            解析成功返回 Response；帧头错误 / 校验失败 / 截断返回 None。
        """

    @abstractmethod
    def decode_telemetry(
        self, raw: bytes, tm_type: str
    ) -> dict[str, TelemetryValue]:
        """从应答帧数据域解码遥测参数。

        Args:
            raw: 遥测应答的数据域字节（不含帧头和校验）。
            tm_type: 遥测类型（"tm1" / "tm2" / "query"）。

        Returns:
            参数 ID → TelemetryValue 的映射。
        """

    def verify_checksum(self, frame: bytes) -> bool:
        """校验整个帧的累加和是否正确。

        默认实现调用 compute_checksum 比对帧末尾 2 字节。
        子类可通过重写 compute_checksum 来复用此逻辑。
        """
        if len(frame) < 4:
            return False
        return self.compute_checksum(frame[2:-2]) == frame[-2:]

    @abstractmethod
    def compute_checksum(self, payload: bytes) -> bytes:
        """计算累加和（2 字节，大端）。

        Args:
            payload: 从索引 2（版本号）到数据域末尾的字节段。

        Returns:
            2 字节校验值（大端序）。
        """

    @abstractmethod
    def get_tm_params(self, tm_type: str) -> Sequence[TmParamDef]:
        """获取指定遥测类型的参数定义列表。"""

    @abstractmethod
    def get_commands(self) -> Sequence[CommandDef]:
        """获取此产品支持的所有指令定义。"""
