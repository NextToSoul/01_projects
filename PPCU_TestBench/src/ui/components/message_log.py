"""PPCU TestBench — 双向报文日志控件"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MessageLogWidget(QWidget):
    """报文日志控件。

    上行（发送）蓝色，下行（接收）绿色。
    显示 HEX + ASCII 两行。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Consolas", 9))
        self._text.setMaximumBlockCount(500)

        btn_clear = QPushButton("\u6e05\u7a7a")
        btn_clear.clicked.connect(self._text.clear)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_clear)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("\u62a5\u6587\u65e5\u5fd7"))
        layout.addWidget(self._text)
        layout.addLayout(btn_layout)

    def append_send(self, data: bytes) -> None:
        """追加发送报文（蓝色）。"""
        self._append(data, "#1a73e8", "\u2192 发送")

    def append_receive(self, data: bytes) -> None:
        """追加接收报文（绿色）。"""
        self._append(data, "#0d652d", "\u2190 接收")

    def _append(self, data: bytes, color: str, direction: str) -> None:
        hex_str = data.hex(" ").upper()
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
        html = (
            f'<div style="color:{color}; font-family:Consolas,monospace;">'
            f"<b>{direction}</b> [{len(data)}B] {hex_str}<br>"
            f'<span style="color:#888;">{"&#160;" * 12}{ascii_str}</span>'
            f"</div>"
        )
        self._text.appendHtml(html)
