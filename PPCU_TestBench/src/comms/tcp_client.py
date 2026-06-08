"""PPCU TestBench — TCP 通信层实现

通过 asyncio 流式 API 实现 TCP → 串口转以太网盒 → RS422 通信。
"""

from __future__ import annotations

import asyncio
import logging

from .interface import (
    CommsInterface,
    ConnectionTimeoutError,
    ReceiveError,
    SendError,
)

logger = logging.getLogger(__name__)


class TcpClient(CommsInterface):
    """TCP 客户端实现。

    用法:
        client = TcpClient()
        await client.connect("192.168.117.26", 20004)
        await client.send(b"\\xEB\\x90...")
        data = await client.receive(timeout=2.0)
        await client.disconnect()
    """

    def __init__(self) -> None:
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected: bool = False

    async def connect(
        self, host: str, port: int, timeout: float = 3.0
    ) -> bool:
        """建立 TCP 连接。"""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout,
            )
            self._connected = True
            logger.info("已连接 %s:%d", host, port)
            return True
        except asyncio.TimeoutError:
            logger.warning("连接 %s:%d 超时 (%.1fs)", host, port, timeout)
            raise ConnectionTimeoutError(
                f"连接 {host}:{port} 超时"
            ) from None
        except OSError as exc:
            logger.error("连接 %s:%d 失败: %s", host, port, exc)
            return False

    async def disconnect(self) -> None:
        """断开连接。"""
        writer = self._writer
        self._reader = None
        self._writer = None
        self._connected = False

        if writer is not None:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        logger.info("已断开连接")

    async def send(self, data: bytes) -> None:
        """发送数据。"""
        if not self._connected or self._writer is None:
            raise SendError("未连接，无法发送")

        try:
            self._writer.write(data)
            await self._writer.drain()
            logger.debug("发送 %d 字节", len(data))
        except Exception as exc:
            raise SendError(f"发送失败: {exc}") from exc

    async def receive(self, timeout: float = 1.0) -> bytes | None:
        """接收数据。"""
        if not self._connected or self._reader is None:
            raise ReceiveError("未连接，无法接收")

        try:
            data = await asyncio.wait_for(
                self._reader.read(4096), timeout=timeout
            )
            if not data:
                # 空字节表示对端关闭连接
                self._connected = False
                logger.warning("对端关闭连接")
                return None
            logger.debug("接收 %d 字节", len(data))
            return data
        except asyncio.TimeoutError:
            return None
        except Exception as exc:
            raise ReceiveError(f"接收失败: {exc}") from exc

    @property
    def is_connected(self) -> bool:
        return self._connected
