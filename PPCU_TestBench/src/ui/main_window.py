"""PPCU TestBench — 主窗口"""
from typing import Optional
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from qasync import asyncSlot

from src.comms.tcp_client import TcpClient, ConnectionTimeoutError
from src.protocol.factory import create_protocol
from src.protocol.interface import ProtocolInterface
from src.protocol.models import Command

from .panels.comm_panel import CommPanel
from .panels.telemetry_panel import TelemetryPanel

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


class MainWindow(QMainWindow):
    """PPCU TestBench 主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PPCU TestBench v0.1.0")
        self.resize(1200, 800)

        self._client = TcpClient()
        self._proto: Optional[ProtocolInterface] = None

        # 面板
        self._comm = CommPanel()
        self._telemetry = TelemetryPanel()

        # 信号 → 槽（异步）
        self._comm.connect_requested.connect(self._on_connect)
        self._comm.disconnect_requested.connect(self._on_disconnect)

        # 标签页
        self._tabs = QTabWidget()
        self._tabs.addTab(self._comm, "\u901a\u8baf")
        self._tabs.addTab(self._telemetry, "\u9065\u6d4b")

        self.setCentralWidget(self._tabs)

        # 状态栏
        self._status = QLabel("\u5c31\u7eea")
        self._status.setStyleSheet("padding: 0 8px;")
        sb = QStatusBar()
        sb.addWidget(self._status)
        self.setStatusBar(sb)

        # TM1 轮询定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.setInterval(1000)

    # ── 异步槽函数 ────────────────────────────────────────

    @asyncSlot()
    async def _on_connect(self, host: str, port: int) -> None:
        try:
            ok = await self._client.connect(host, port)
            if not ok:
                self._comm.on_error(f"\u8fde\u63a5\u5931\u8d25: {host}:{port}")
                return
            self._proto = create_protocol("nebula_ppcu", CONFIG_DIR)
            self._comm.on_connected()
            self._timer.start()
            self.set_status(f"\u5df2\u8fde\u63a5 {host}:{port}")
        except ConnectionTimeoutError:
            self._comm.on_error("\u8fde\u63a5\u8d85\u65f6")
        except Exception as exc:
            self._comm.on_error(str(exc))

    @asyncSlot()
    async def _on_disconnect(self) -> None:
        self._timer.stop()
        await self._client.disconnect()
        self._comm.on_disconnected()
        self._proto = None
        self.set_status("\u5df2\u65ad\u5f00")

    @asyncSlot()
    async def _poll(self) -> None:
        """定时轮询 TM1 遥测。"""
        if not self._client.is_connected or self._proto is None:
            return
        try:
            cmd = Command(cmd_id=0x005A, name="\u9065\u6d4b1\u8bf7\u6c42")
            frame = self._proto.build_request(cmd)
            self._comm.append_send(frame)
            await self._client.send(frame)

            data = await self._client.receive(timeout=2.0)
            if data is None:
                return
            self._comm.append_recv(data)

            result = self._proto.parse_response(data)
            if result and result.parsed and result.data:
                self._telemetry.update_tm(result.tm_type, result.data)
        except Exception as exc:
            self.set_status(f"\u8f6e\u8be2\u5f02\u5e38: {exc}")
            self._timer.stop()
            await self._client.disconnect()
            self._comm.on_disconnected()

    def set_status(self, text: str) -> None:
        self._status.setText(text)
