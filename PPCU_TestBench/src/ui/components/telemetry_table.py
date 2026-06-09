"""PPCU TestBench — 遥测参数实时表格控件

列顺序: 时间 | 参数ID | 名称 | 工程量 | 原始值 | 源码值 | 单位 | 状态
顶部显示最后刷新时戳；工程量/原始值变化时浅绿闪烁 2 秒。
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_CHANGE_BG = QBrush(QColor("#d4edda"))
_NORMAL_BG = QBrush(QColor("#ffffff"))
_WARN_FG = QBrush(QColor("#d32f2f"))


class TelemetryTableWidget(QWidget):
    """遥测参数实时表格。

    列顺序: 时间 | 参数ID | 名称 | 工程量 | 原始值 | 源码值 | 单位 | 状态
    顶部显示最后刷新时戳；工程量/原始值变化时浅绿闪烁 2 秒。
    """

    COLUMNS = ["时间", "参数ID", "名称", "工程量", "原始值", "源码值", "单位", "状态"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 时间
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 参数ID
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)           # 名称
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 工程量
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 原始值
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 源码值
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 单位

        self._ts_label = QLabel()
        self._ts_label.setAlignment(Qt.AlignRight)
        self._ts_label.setStyleSheet("color: #888; font-size: 11px; padding: 2px 4px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self._ts_label)
        layout.addWidget(self._table)

        self._param_rows: dict[str, int] = {}
        self._items: dict[tuple[str, int], QTableWidgetItem] = {}
        self._prev_values: dict[tuple[str, int], str] = {}
        self._hl_dirty: set[tuple[str, int]] = set()
        self._hl_timer: QTimer | None = None

    def clear_data(self) -> None:
        """清空所有行、时戳、历史记录。"""
        self._table.setRowCount(0)
        self._param_rows.clear()
        self._items.clear()
        self._prev_values.clear()
        self._hl_dirty.clear()
        if self._hl_timer is not None:
            self._hl_timer.stop()
            self._hl_timer = None
        self._ts_label.clear()

    def update_data(self, data: dict) -> None:
        """用解码后的遥测数据刷新表格（I/O 批量刷新）。"""
        now = datetime.now().strftime("%H:%M:%S")
        self._ts_label.setText(f"最后更新: {now}")

        self._table.setUpdatesEnabled(False)
        try:
            for param_id, tv in data.items():
                row = self._param_rows.get(param_id)
                if row is None:
                    row = self._table.rowCount()
                    self._table.insertRow(row)
                    self._param_rows[param_id] = row

                warning = tv.status == "warning"

                self._set(row, 1, tv.param_id)
                self._set(row, 0, now)
                self._set(row, 2, tv.name)
                eng_text = str(tv.eng_value)
                self._set_with_highlight(row, 3, eng_text, param_id, 3, warning)
                raw_text = str(tv.raw_value)
                self._set_with_highlight(row, 4, raw_text, param_id, 4, warning)
                hex_text = ("0x" + format(tv.raw_value, "X")) if isinstance(tv.raw_value, int) else str(tv.raw_value)
                self._set_with_highlight(row, 5, hex_text, param_id, 5, warning)
                self._set(row, 6, tv.unit)
                self._set(row, 7, tv.status, warn=warning)
        finally:
            self._table.setUpdatesEnabled(True)

    def _set(self, row: int, col: int, text: str, warn: bool = False) -> None:
        key = ("__static__", row, col)
        item = self._items.get(key)
        if item is None:
            item = QTableWidgetItem(text)
            self._items[key] = item
            self._table.setItem(row, col, item)
        else:
            item.setText(text)
        if warn:
            item.setForeground(_WARN_FG)
        else:
            item.setForeground(QBrush())

    def _set_with_highlight(self, row: int, col: int, text: str, param_id: str, col_idx: int, warn: bool) -> None:
        """设置单元格，若值与上次不同则高亮闪烁（延时批量清除）。"""
        key = (param_id, col_idx)
        prev = self._prev_values.get(key, "")
        changed = prev != text

        item = self._items.get(key)
        if item is None:
            item = QTableWidgetItem(text)
            self._items[key] = item
            self._table.setItem(row, col, item)
        else:
            item.setText(text)

        if warn:
            item.setForeground(_WARN_FG)
        else:
            item.setForeground(QBrush())

        if changed and prev != "":
            item.setBackground(_CHANGE_BG)
            self._hl_dirty.add(key)
            self._schedule_highlight_sweep()
        else:
            item.setBackground(_NORMAL_BG)

        self._prev_values[key] = text

    def _schedule_highlight_sweep(self) -> None:
        """调度单次批量清除高亮（2 秒后）。"""
        if self._hl_timer is not None:
            return  # 已调度，等待执行
        self._hl_timer = QTimer(self)
        self._hl_timer.setSingleShot(True)
        self._hl_timer.timeout.connect(self._sweep_highlights)
        self._hl_timer.start(2000)

    def _sweep_highlights(self) -> None:
        """批量清除所有高亮背景。"""
        self._hl_timer = None
        if not self._hl_dirty:
            return
        for key in self._hl_dirty:
            item = self._items.get(key)
            if item is not None:
                item.setBackground(_NORMAL_BG)
        self._hl_dirty.clear()