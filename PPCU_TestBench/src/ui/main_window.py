"""PPCU TestBench — 主窗口"""
from typing import Optional
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from src.comms.tcp_client import TcpClient, ConnectionTimeoutError
from src.comms.interface import SendError, ReceiveError
from src.protocol.factory import create_protocol
from src.protocol.interface import ProtocolInterface
from src.protocol.models import Command
import asyncio

from .panels.comm_panel import CommPanel
from .panels.command_panel import CommandPanel
from .panels.telemetry_panel import TelemetryPanel

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

CMD_IDS = {
    "tm1": 0x005A,
    "tm2": 0x00AA,
    "query": 0x0310,
}


class MainWindow(QMainWindow):
    """PPCU TestBench 主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PPCU TestBench v0.1.0")
        self.resize(1200, 800)
        self._client = TcpClient()
        self._proto: Optional[ProtocolInterface] = None
        self._busy: dict[str, bool] = {"tm1": False, "tm2": False, "query": False}
        self._poll_active: dict[str, bool] = {"tm1": False, "tm2": False}
        self._poll_cycle: bool = False
        self._poll_task: asyncio.Task | None = None
        self._comms_lock = asyncio.Lock()
        self._comm = CommPanel()
        self._command = CommandPanel()
        self._telemetry = TelemetryPanel()
        self._comm.connect_requested.connect(self._on_connect)
        self._comm.disconnect_requested.connect(self._on_disconnect)
        self._command.single_query_requested.connect(self._on_single_query)
        self._command.poll_started.connect(self._on_start_poll)
        self._command.poll_stopped.connect(self._on_stop_poll)
        central = QWidget()
        lo = QVBoxLayout(central)
        lo.setContentsMargins(4, 4, 4, 4)
        lo.setSpacing(4)
        lo.addWidget(self._comm.connection_bar)
        sp = QSplitter(Qt.Horizontal)
        sp.setChildrenCollapsible(False)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(self._command)
        ll.addWidget(self._comm.log_widget, 1)
        sp.addWidget(left)
        sp.addWidget(self._telemetry)
        sp.setSizes([450, 750])
        lo.addWidget(sp, 1)
        self.setCentralWidget(central)
        self._status = QLabel("\u5c31\u7eea")
        self._status.setStyleSheet("padding: 0 8px;")
        sb = QStatusBar()
        sb.addWidget(self._status)
        self.setStatusBar(sb)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.setInterval(1000)

        # Menu bar: File > Import Telemetry
        menubar = self.menuBar()
        file_menu = menubar.addMenu("\u6587\u4ef6")
        act = file_menu.addAction("\u5bfc\u5165\u9065\u6d4b\u5b9a\u4e49")
        act.triggered.connect(self._on_import_telemetry)
 
    def closeEvent(self, event):
        self._timer.stop()
        for t in self._poll_active:
            self._poll_active[t] = False
            self._busy[t] = False
        self._proto = None
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None
        event.accept()

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
            self._command.set_connected()
            self.set_status(f"\u5df2\u8fde\u63a5 {host}:{port}")
        except ConnectionTimeoutError:
            self._comm.on_error("\u8fde\u63a5\u8d85\u65f6")
        except Exception as exc:
            self._comm.on_error(str(exc))

    @asyncSlot()
    async def _on_disconnect(self) -> None:
        self._stop_polling()
        self._timer.stop()
        await self._client.disconnect()
        self._comm.on_disconnected()
        self._command.set_idle()
        self._proto = None
        self.set_status("\u5df2\u65ad\u5f00")

    @asyncSlot()
    async def _send_and_receive(self, tm_type: str) -> None:
        async with self._comms_lock:
            cmd = Command(cmd_id=CMD_IDS[tm_type], name=f"{tm_type}\u8bf7\u6c42")
            frame = self._proto.build_request(cmd)
            self._comm.append_send(frame)
            await self._client.send(frame)
            data = await self._client.receive(timeout=2.0)
            if data is None:
                if not self._client.is_connected:
                    raise ConnectionError("\u8fde\u63a5\u5df2\u65ad\u5f00")
                return
            self._comm.append_recv(data)
            result = self._proto.parse_response(data)
            if result and result.parsed and result.data:
                self._telemetry.update_tm(result.tm_type, result.data)

    @asyncSlot()
    async def _on_single_query(self, tm_type: str) -> None:
        if self._busy[tm_type] or not self._client.is_connected or self._proto is None:
            return
        self._command.set_busy(tm_type)
        self._busy[tm_type] = True
        self._poll_task = asyncio.current_task()
        try:
            await self._send_and_receive(tm_type)
        except (SendError, OSError, ReceiveError, ConnectionError) as exc:
            self.set_status(f"\u67e5\u8be2\u5931\u8d25: {exc}")
            await self._handle_connection_lost()
        finally:
            self._busy[tm_type] = False
            self._poll_task = None
            if self._client.is_connected:
                self._command.set_idle_for(tm_type, {t for t, v in self._poll_active.items() if v})

    @asyncSlot()
    async def _on_start_poll(self, tm_type: str) -> None:
        self._poll_active[tm_type] = True
        active = {t for t, v in self._poll_active.items() if v}
        self._command.set_polling_state(active)
        labels = " + ".join(t.upper() for t in active)
        self.set_status(f"\u8f6e\u8be2\u4e2d ({labels})")
        self._timer.start()

    @asyncSlot()
    async def _on_stop_poll(self, tm_type: str) -> None:
        self._poll_active[tm_type] = False
        self._busy[tm_type] = False
        active = {t for t, v in self._poll_active.items() if v}
        if active:
            self._command.set_polling_state(active)
            labels = " + ".join(t.upper() for t in active)
            self.set_status(f"\u8f6e\u8be2\u4e2d ({labels})")
        else:
            self._command.set_connected()
            self._timer.stop()
            self.set_status("\u5c31\u7eea")

    def _stop_polling(self) -> None:
        self._timer.stop()
        for t in self._poll_active:
            self._poll_active[t] = False
            self._busy[t] = False
 
    @asyncSlot()
    async def _on_import_telemetry(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "\u9009\u62e9\u9065\u6d4b\u5b9a\u4e49\u6587\u4ef6",
            "", "Excel Files (*.xlsx)")
        if not filepath:
            return
        import os, sys, tempfile
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from tools.import_from_excel import import_excel
        out_dir = tempfile.gettempdir()
        proj_dir = Path(__file__).resolve().parent.parent.parent / "protocol_defs" / "nebula_ppcu"
        import shutil
        results = import_excel(filepath, out_dir)
        import time
        bk = None
        existing = list(proj_dir.glob("telemetry_*.yaml")) + [proj_dir / "enums.yaml"]
        existing = [f for f in existing if f.is_file()]
        if existing:
            ts = time.strftime("%Y%m%d_%H%M%S")
            bk = os.path.join(tempfile.gettempdir(), "ppcu_backup_" + ts)
            os.mkdir(bk)
            for f in existing:
                shutil.copy2(str(f), os.path.join(bk, f.name))
        ok = 0
        for t, c in results:
            try:
                shutil.copy2(os.path.join(out_dir, "telemetry_" + t + ".yaml"),
                str(proj_dir / ("telemetry_" + t + ".yaml")))
                ok += 1
            except:
                pass
        try:
            shutil.copy2(os.path.join(out_dir, "enums.yaml"),
                        str(proj_dir / "enums.yaml"))
        except:
            pass
        msg = "\u5bfc\u5165\u5b8c\u6210: " + str(len(results)) + " \u4e2a\u9065\u6d4b\u5305\n"
        if ok == len(results):
            msg += "\n\u5df2\u81ea\u52a8\u590d\u5236\u5230\u9879\u76ee\u76ee\u5f55\uff0c"
        else:
            for t, c in results:
                msg += "  " + t + ": " + str(c) + " \u53c2\u6570\n"
            msg += "\n\u81ea\u52a8\u590d\u5236\u5931\u8d25(" + str(ok) + "/" + str(len(results)) + ")\uff0c\u8bf7\u624b\u52a8:\n"
            msg += '  Copy-Item "$env:TEMP\\telemetry_*.yaml" .\\protocol_defs\\nebula_ppcu\\ -Force\n'
            msg += '  Copy-Item "$env:TEMP\\enums.yaml" .\\protocol_defs\\nebula_ppcu\\ -Force\n'
        msg += "\u91cd\u542f\u7a0b\u5e8f\u540e\u751f\u6548"
        if bk:
            msg += "\n\u5907\u4efd: " + bk
        QMessageBox.information(self, "\u5bfc\u5165\u5b8c\u6210", msg)

    @asyncSlot()
    async def _poll(self) -> None:
        if self._poll_cycle:
            return
        self._poll_cycle = True
        self._poll_task = asyncio.current_task()
        try:
            if self._proto is None or not self._client.is_connected:
                await self._handle_connection_lost()
                return
            tasks = []
            for t, active in self._poll_active.items():
                if active and not self._busy[t]:
                    self._busy[t] = True
                    tasks.append(self._send_one_poll(t))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as exc:
            self.set_status(f"\u8f6e\u8be2\u5f02\u5e38: {exc}")
        finally:
            for t in self._poll_active:
                self._busy[t] = False
            self._poll_task = None
            self._poll_cycle = False
            if any(self._poll_active.values()):
                self._timer.start()

    async def _send_one_poll(self, tm_type: str) -> None:
        try:
            await self._send_and_receive(tm_type)
        except (SendError, OSError) as exc:
            self.set_status(f"\u8f6e\u8be2\u53d1\u9001\u5931\u8d25 ({tm_type}): {exc}")
            raise
        except (ReceiveError, ConnectionError) as exc:
            self.set_status(f"\u8f6e\u8be2\u5f02\u5e38 ({tm_type}): {exc}")
            raise

    async def _handle_connection_lost(self) -> None:
        self._stop_polling()
        self._timer.stop()
        self._proto = None
        try:
            await self._client.disconnect()
        except Exception:
            pass
        self._comm.on_disconnected()
        self._command.set_idle()
        self.set_status("\u8fde\u63a5\u5df2\u65ad\u5f00")
 
    def set_status(self, text: str) -> None:
        self._status.setText(text)
