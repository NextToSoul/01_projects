"""PPCU TestBench — 指令控制面板"""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class CommandPanel(QWidget):
    single_query_requested = Signal(str)
    poll_started = Signal(str)
    poll_stopped = Signal(str)

    TM_TYPES = [
        ("tm1", "TM1", "0x005A"),
        ("tm2", "TM2", "0x00AA"),
        ("query", "查询包", "0x0310"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._btns = {}
        self._status = QLabel("")
        self._setup_ui()
        self.set_idle()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        grp = QGroupBox("指令控制")
        body = QVBoxLayout()
        for key, label, code in self.TM_TYPES:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label} ({code}):"))
            btn = QPushButton("单次查询")
            btn.clicked.connect(lambda checked, t=key: self.single_query_requested.emit(t))
            if key in ("tm1", "tm2"):
                start = QPushButton("开始轮询")
                start.clicked.connect(lambda checked, t=key: self.poll_started.emit(t))
                stop = QPushButton("停止轮询")
                stop.setEnabled(False)
                stop.clicked.connect(lambda checked, t=key: self.poll_stopped.emit(t))
                self._btns[key] = {"single": btn, "start": start, "stop": stop}
                row.addWidget(btn)
                row.addWidget(start)
                row.addWidget(stop)
            else:
                self._btns[key] = {"single": btn}
                row.addWidget(btn)
            row.addStretch()
            body.addLayout(row)
        grp.setLayout(body)
        layout.addWidget(grp)
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("状态:"))
        status_row.addWidget(self._status)
        status_row.addStretch()
        layout.addLayout(status_row)
        layout.addStretch()

    def set_idle(self):
        for btns in self._btns.values():
            btns["single"].setEnabled(False)
            if "start" in btns:
                btns["start"].setEnabled(False)
                btns["stop"].setEnabled(False)
        self._status.setText("空闲")

    def set_connected(self):
        for btns in self._btns.values():
            btns["single"].setEnabled(True)
            if "start" in btns:
                btns["start"].setEnabled(True)
                btns["stop"].setEnabled(False)
        self._status.setText("就绪")

    def set_polling_state(self, active_types: set):
        for key, btns in self._btns.items():
            on = key in active_types
            btns["single"].setEnabled(not on)
            if "start" in btns:
                btns["start"].setEnabled(not on)
                btns["stop"].setEnabled(on)
        if active_types:
            labels = []
            for k, label, _ in self.TM_TYPES:
                if k in active_types:
                    labels.append(label.split()[0])
            self._status.setText(f"轮询中 ({'+'.join(labels)})")
        else:
            self._status.setText("就绪")

    def set_busy(self, tm_type):
        btns = self._btns.get(tm_type)
        if btns:
            btns["single"].setEnabled(False)

    def set_idle_for(self, tm_type, poll_types: set):
        btns = self._btns.get(tm_type)
        if btns is None:
            return
        btns["single"].setEnabled(tm_type not in poll_types)
        if "start" in btns:
            btns["start"].setEnabled(tm_type not in poll_types)
            btns["stop"].setEnabled(tm_type in poll_types)
