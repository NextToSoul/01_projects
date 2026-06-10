"""PPCU TestBench — 立即遥控指令面板

支持模糊搜索、分组折叠、参数编辑、帧预览、发送确认。
"""

from __future__ import annotations

from pathlib import Path


from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.protocol.checksum import compute_checksum
from src.protocol.remote_command_loader import RemoteCommandDef, load_remote_commands

# 配置表路径
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "项目文档" / "通讯协议" / "excel版遥测大表" / "立即遥控指令配置表.xlsx"


class RemoteCommandPanel(QWidget):
    """立即遥控指令面板。"""
    send_requested = Signal(bytes)  # 发送信号，携带待发送的 Command

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._commands: list[RemoteCommandDef] = []
        self._selected: RemoteCommandDef | None = None
        # 组展开状态
        self._group_widgets: dict[str, QWidget] = {}
        self._group_toggles: dict[str, QToolButton] = {}
        self._group_expanded: dict[str, bool] = {}
        self._seq_counter: int = 0
        self._cmd_buttons: dict[str, QPushButton] = {}  # cmd_id -> button

        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        grp = QGroupBox("立即遥控指令")
        gl = QVBoxLayout(grp)
        gl.setContentsMargins(4, 4, 4, 4)
        gl.setSpacing(4)

        # 搜索框
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索指令名称或代号...")
        self._search.textChanged.connect(self._on_search)
        btn_clear = QPushButton("清空")
        btn_clear.setFixedWidth(50)
        btn_clear.clicked.connect(lambda: self._search.clear())
        search_row.addWidget(self._search)
        search_row.addWidget(btn_clear)
        gl.addLayout(search_row)

        # 指令列表滚动区
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._list_widget)
        gl.addWidget(self._scroll, 1)

        # 选中详情区域
        self._detail = QFrame()
        self._detail.setFrameShape(QFrame.StyledPanel)
        dl = QVBoxLayout(self._detail)
        dl.setContentsMargins(4, 4, 4, 4)
        dl.setSpacing(4)

        self._detail_name = QLabel("未选中指令")
        self._detail_name.setStyleSheet("font-weight: bold;")
        dl.addWidget(self._detail_name)

        info_row = QHBoxLayout()
        self._detail_code = QLabel("")
        self._detail_len = QLabel("")
        info_row.addWidget(self._detail_code)
        info_row.addWidget(self._detail_len)
        info_row.addStretch()
        dl.addLayout(info_row)

        param_row = QHBoxLayout()
        param_row.addWidget(QLabel("参数值:"))
        self._param_input = QLineEdit()
        self._param_input.setPlaceholderText("HEX 字节，空格分隔，如 01 18")
        self._param_input.textChanged.connect(self._on_param_changed)
        param_row.addWidget(self._param_input)
        dl.addLayout(param_row)

        dl.addWidget(QLabel("帧预览:"))
        self._frame_preview = QLabel("")
        self._frame_preview.setFont(QFont("Consolas", 9))
        self._frame_preview.setStyleSheet("color: #555; background: #f5f5f5; padding: 4px; border: 1px solid #ddd; border-radius: 3px;")
        self._frame_preview.setWordWrap(True)
        self._frame_preview.setTextInteractionFlags(Qt.TextSelectableByMouse)
        dl.addWidget(self._frame_preview)

        btn_row = QHBoxLayout()
        self._btn_pack = QPushButton("指令组包")
        self._btn_pack.clicked.connect(self._on_pack)
        self._btn_send = QPushButton("指令发送")
        self._btn_send.setStyleSheet(
            "QPushButton { background-color: #d32f2f; color: white; font-weight: bold; padding: 6px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #b71c1c; }"
            "QPushButton:disabled { background-color: #ccc; color: #888; }"
        )
        self._btn_send.clicked.connect(self._on_send)
        self._btn_send.setEnabled(False)
        btn_row.addWidget(self._btn_pack)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_send)
        dl.addLayout(btn_row)

        self._detail.setVisible(False)
        gl.addWidget(self._detail)

        layout.addWidget(grp)

    def _load_config(self) -> None:
        if not _CONFIG_PATH.exists():
            self._detail_name.setText(f"配置表不存在: {_CONFIG_PATH}")
            return
        try:
            self._commands = load_remote_commands(_CONFIG_PATH)
        except Exception as exc:
            self._detail_name.setText(f"加载配置失败: {exc}")
            return
        self._rebuild_list()

    def _rebuild_list(self, filter_text: str = "") -> None:
        """按 Excel 顺序展示指令列表（带过滤）。"""
        # 清除旧内容
        while self._list_layout.count() > 0:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filter_text = filter_text.strip().lower()

        for cmd in self._commands:
            if filter_text and filter_text not in cmd.name.lower() and filter_text not in cmd.id.lower():
                continue

            label = cmd.id + "  " + cmd.name
            btn = QPushButton(label)
            tip = "指令码: {:04X}".format(cmd.cmd_id)
            if cmd.params:
                tip += "\n参数: " + cmd.params.hex(" ").upper()
            btn.setToolTip(tip)
            btn.setFixedHeight(26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=cmd: self._select_command(c))
            self._list_layout.addWidget(btn)

        self._list_layout.addStretch()
    def _on_search(self, text: str) -> None:
        self._rebuild_list(text)

    def _select_command(self, cmd: RemoteCommandDef) -> None:
        self._selected = cmd
        self._detail.setVisible(True)

        self._detail_name.setText(f"{cmd.name}  ({cmd.id})")
        hi = cmd.cmd_id >> 8
        lo = cmd.cmd_id & 0xFF
        self._detail_code.setText(f"指令码: {hi:02X} {lo:02X}")
        self._detail_len.setText(f"  字数: {cmd.data_len_words}")
        self._param_input.setText(cmd.params.hex(" ").upper() if cmd.params else "")
        self._frame_preview.clear()
        self._btn_send.setEnabled(True)

    def _on_param_changed(self, text: str) -> None:
        text = text.strip()
        self._param_input.setStyleSheet("")
        if not text:
            return
        parts = text.split()
        try:
            for p in parts:
                int(p, 16)
        except ValueError:
            self._param_input.setStyleSheet("border: 1px solid red;")

    def _parse_param_bytes(self) -> bytes:
        text = self._param_input.text().strip()
        if not text:
            return b""
        return bytes(int(x, 16) for x in text.split())

    def _build_frame(self) -> bytes:
        """按 Excel 配置构建完整指令帧，数据域长度使用配置表值。"""
        # _selected is guaranteed non-None by caller
        cmd = self._selected
        params = self._parse_param_bytes()
        data = cmd.cmd_id.to_bytes(2, "big") + params
        len_field = cmd.data_len_words.to_bytes(2, "big")
        header = bytes([0xEB, 0x90, 0x05, 0x20])
        seq = (self._seq_counter & 0x3FFF).to_bytes(2, "big")
        self._seq_counter = (self._seq_counter + 1) & 0x3FFF
        payload = header[2:] + seq + len_field + data
        cs = compute_checksum(payload)
        return header + seq + len_field + data + cs

    def _on_pack(self) -> None:
        if self._selected is None:
            return
        try:
            frame = self._build_frame()
            self._frame_preview.setText(frame.hex(" ").upper())
        except Exception as exc:
            self._frame_preview.setText(f"组包失败: {exc}")

    def _on_send(self) -> None:
        if self._selected is None:
            return
        try:
            frame = self._build_frame()
            hex_str = frame.hex(" ").upper()
        except Exception as exc:
            QMessageBox.warning(self, "组包错误", str(exc))
            return

        reply = QMessageBox.question(
            self,
            "确认发送指令",
            f"指令: {self._selected.name}\n"
            f"指令码: {self._selected.cmd_id:04X}\n"
            f"参数: {self._param_input.text()}\n"
            f"帧: {hex_str}\n\n"
            f"确认发送?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.send_requested.emit(frame)