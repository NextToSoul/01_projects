"""PPCU TestBench — 通讯面板"""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
)
from ..components.message_log import MessageLogWidget

class CommPanel(QWidget):
    connect_requested = Signal(str, int)
    disconnect_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._host = QLineEdit("192.168.117.26")
        self._port = QLineEdit("20004")
        self._status = QLabel("\u672a\u8fde\u63a5")
        self._status.setStyleSheet("color: #888;")

        hl = QHBoxLayout()
        hl.addWidget(QLabel("\u4e3b\u673a:"))
        hl.addWidget(self._host)
        hl.addWidget(QLabel("\u7aef\u53e3:"))
        hl.addWidget(self._port)

        self._btn_conn = QPushButton("\u8fde\u63a5")
        self._btn_conn.clicked.connect(self._on_connect)
        self._btn_dis = QPushButton("\u65ad\u5f00")
        self._btn_dis.clicked.connect(self._on_disconnect)
        self._btn_dis.setEnabled(False)
        bl = QHBoxLayout()
        bl.addWidget(self._btn_conn)
        bl.addWidget(self._btn_dis)
        bl.addStretch()
        bl.addWidget(self._status)

        grp = QGroupBox("\u901a\u8baf\u8bbe\u7f6e")
        self._grp = grp
        w = QVBoxLayout()
        w.addLayout(hl)
        w.addLayout(bl)
        grp.setLayout(w)

        self._log = MessageLogWidget()
        l = QVBoxLayout(self)
        l.addWidget(grp)
        l.addWidget(self._log, 1)

    def _on_connect(self):
        try:
            port = int(self._port.text())
        except ValueError:
            self._status.setText("\u7aef\u53e3\u53f7\u65e0\u6548")
            self._status.setStyleSheet("color: red;")
            return
        self.connect_requested.emit(self._host.text(), port)
        self._status.setStyleSheet("color: orange;")
        self._status.setText("\u8fde\u63a5\u4e2d...")

    def _on_disconnect(self):
        self.disconnect_requested.emit()

    def on_connected(self):
        self._btn_conn.setEnabled(False)
        self._btn_dis.setEnabled(True)
        self._status.setText("\u5df2\u8fde\u63a5")
        self._status.setStyleSheet("color: green;")

    def on_disconnected(self):
        self._btn_conn.setEnabled(True)
        self._btn_dis.setEnabled(False)
        self._status.setText("\u672a\u8fde\u63a5")
        self._status.setStyleSheet("color: #888;")

    def on_error(self, msg: str):
        self._status.setText(msg)
        self._status.setStyleSheet("color: red;")

    def append_send(self, data: bytes):
        self._log.append_send(data)

    def append_recv(self, data: bytes):
        self._log.append_receive(data)

    @property
    def connection_bar(self):
        return self._grp

    @property
    def log_widget(self):
        return self._log
