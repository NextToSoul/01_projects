"""PPCU TestBench — 遥测面板"""

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from ..components.telemetry_table import TelemetryTableWidget


class TelemetryPanel(QWidget):
    """遥测面板：TM1 / TM2 / 查询 三个子页签。"""

    TM_TYPES = [
        ("tm1", "TM1 (\u5468\u671f 1s)"),
        ("tm2", "TM2 (\u5468\u671f 2s)"),
        ("query", "\u67e5\u8be2"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tabs = QTabWidget()
        self._tables: dict[str, TelemetryTableWidget] = {}

        for key, label in self.TM_TYPES:
            table = TelemetryTableWidget()
            self._tables[key] = table
            self._tabs.addTab(table, label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)

    def update_tm(self, tm_type: str, data: dict) -> None:
        """更新指定遥测类型的表格数据。"""
        table = self._tables.get(tm_type)
        if table is not None:
            table.update_data(data)

    def clear_all(self) -> None:
        """清空所有表格。"""
        for table in self._tables.values():
            table.clear_data()
