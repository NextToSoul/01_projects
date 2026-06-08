"""PPCU TestBench — 主窗口"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QStatusBar,
    QLabel,
)

from .panels.comm_panel import CommPanel
from .panels.telemetry_panel import TelemetryPanel


class MainWindow(QMainWindow):
    """PPCU TestBench 主窗口。

    标签页布局:
      [通讯] [遥测] [测试] [报告] [配置]
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PPCU TestBench v0.1.0")
        self.resize(1200, 800)

        # 面板
        self._comm = CommPanel()
        self._telemetry = TelemetryPanel()

        # 标签页
        self._tabs = QTabWidget()
        self._tabs.addTab(self._comm, "\u901a\u8baf")
        self._tabs.addTab(self._telemetry, "\u9065\u6d4b")
        # [M3] self._tabs.addTab(test_panel, "\u6d4b\u8bd5")
        # [M4] self._tabs.addTab(report_panel, "\u62a5\u544a")
        # [M4] self._tabs.addTab(config_panel, "\u914d\u7f6e")

        self.setCentralWidget(self._tabs)

        # 状态栏
        self._status = QLabel("\u5c31\u7eea")
        self._status.setStyleSheet("padding: 0 8px;")
        status_bar = QStatusBar()
        status_bar.addWidget(self._status)
        self.setStatusBar(status_bar)

    @property
    def comm_panel(self) -> CommPanel:
        return self._comm

    @property
    def telemetry_panel(self) -> TelemetryPanel:
        return self._telemetry

    def set_status(self, text: str) -> None:
        self._status.setText(text)
