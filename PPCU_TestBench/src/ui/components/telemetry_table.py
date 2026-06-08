"""PPCU TestBench — 遥测参数实时表格控件"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class TelemetryTableWidget(QWidget):
    """遥测参数实时表格。

    动态添加行，仅第一次创建行，后续直接更新值。
    异常值自动红色标记。
    """

    COLUMNS = ["\u53c2\u6570ID", "\u540d\u79f0", "\u539f\u59cb\u503c", "\u5de5\u7a0b\u91cf", "\u5355\u4f4d", "\u72b6\u6001"]

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
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)

        self._param_rows: dict[str, int] = {}

    def clear_data(self) -> None:
        """清空所有行。"""
        self._table.setRowCount(0)
        self._param_rows.clear()

    def update_data(self, data: dict) -> None:
        """用解码后的遥测数据刷新表格。"""
        for param_id, tv in data.items():
            row = self._param_rows.get(param_id)
            if row is None:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._param_rows[param_id] = row

            warning = tv.status == "warning"
            self._set(row, 0, tv.param_id)
            self._set(row, 1, tv.name)
            self._set(row, 2, str(tv.raw_value))
            self._set(row, 3, str(tv.eng_value))
            self._set(row, 4, tv.unit)
            self._set(row, 5, tv.status, warn=warning)

    def _set(self, row: int, col: int, text: str, warn: bool = False) -> None:
        item = QTableWidgetItem(text)
        if warn:
            item.setForeground(QBrush(QColor("#d32f2f")))
            item.setFont(item.font())
        self._table.setItem(row, col, item)
