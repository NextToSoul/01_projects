"""PPCU TestBench — 通信层抽象接口

CommsInterface 定义 async 通信协议，所有底层通信实现（TCP / USB / CAN）
均实现此接口。当前仅 TcpClient 实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CommsError(Exception):
    """通信层异常基类。"""


class ConnectionTimeoutError(CommsError):
    """连接超时。"""


class SendError(CommsError):
    """发送失败。"""


class ReceiveError(CommsError):
    """接收失败。"""


class CommsInterface(ABC):
    """通信层抽象。

    当前仅 TcpClient 实现（TCP → 串口转以太网盒 → RS422），
    后续可扩展 USB / CAN 卡实现。
    所有 I/O 方法均为 async，与 asyncio + qasync GUI 集成。
    """

    @abstractmethod
    async def connect(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """建立 TCP 连接。

        Args:
            host: 目标主机地址。
            port: 目标端口。
            timeout: 连接超时（秒）。

        Returns:
            连接是否成功。

        Raises:
            ConnectionTimeoutError: 连接超时。
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """断开通信连接。"""

    @abstractmethod
    async def send(self, data: bytes) -> None:
        """发送数据。

        Args:
            data: 待发送的字节数据。

        Raises:
            SendError: 发送失败。
        """

    @abstractmethod
    async def receive(self, timeout: float = 1.0) -> bytes | None:
        """接收数据。

        Args:
            timeout: 等待超时（秒）。

        Returns:
            接收到的字节数据；超时返回 None。
        """

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """当前是否已连接。"""
