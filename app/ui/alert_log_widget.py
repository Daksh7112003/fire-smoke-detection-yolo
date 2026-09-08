import os
import time
import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QGroupBox, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

class AlertLogWidget(QWidget):
    """
    Real-time Audit Log Table for hazard detections (Fire/Smoke).
    Allows filtering, CSV export, and double-click seeking to the exact detection frame.
    """
    jump_to_frame = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_log_time = 0.0
        self.log_throttle_interval = 0.5  # Prevent flooding table with duplicate entries per fraction of sec
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        group_box = QGroupBox("DETECTION EVENT AUDIT LOG")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(8)

        # Header controls (Filter, Clear, Export)
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Filter:"))
        
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["All Events", "🔥 Fire Only", "💨 Smoke Only"])
        self.combo_filter.currentIndexChanged.connect(self.apply_filter)
        ctrl_layout.addWidget(self.combo_filter)

        ctrl_layout.addStretch()

        self.btn_export = QPushButton("📥 Export CSV")
        self.btn_export.clicked.connect(self.export_csv)
        ctrl_layout.addWidget(self.btn_export)

        self.btn_clear = QPushButton("🗑 Clear")
        self.btn_clear.clicked.connect(self.clear_log)
        ctrl_layout.addWidget(self.btn_clear)

        group_layout.addLayout(ctrl_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Time", "Hazard", "Confidence", "Frame #", "Video Source"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        group_layout.addWidget(self.table)

        layout.addWidget(group_box)

    def log_event(self, hazard_type: str, conf: float, frame_num: int, source_name: str):
        """Append an event to the log table."""
        now = time.perf_counter()
        if now - self.last_log_time < self.log_throttle_interval:
            return
        self.last_log_time = now

        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        # Timestamp
        time_str = time.strftime("%H:%M:%S")
        item_time = QTableWidgetItem(time_str)
        item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Hazard Pill
        if hazard_type == "FIRE":
            hazard_text = "🔥 FIRE"
            bg_color = QColor("#381A1C")
            fg_color = QColor("#FF7B72")
        else:
            hazard_text = "💨 SMOKE"
            bg_color = QColor("#332512")
            fg_color = QColor("#E3B341")

        item_hazard = QTableWidgetItem(hazard_text)
        item_hazard.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_hazard.setBackground(bg_color)
        item_hazard.setForeground(fg_color)
        item_hazard.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        # Confidence
        item_conf = QTableWidgetItem(f"{conf * 100:.1f}%")
        item_conf.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Frame number
        item_frame = QTableWidgetItem(str(frame_num))
        item_frame.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_frame.setData(Qt.ItemDataRole.UserRole, frame_num)

        # Source
        source_basename = os.path.basename(source_name) if source_name else "Live"
        item_source = QTableWidgetItem(source_basename)

        self.table.setItem(row_idx, 0, item_time)
        self.table.setItem(row_idx, 1, item_hazard)
        self.table.setItem(row_idx, 2, item_conf)
        self.table.setItem(row_idx, 3, item_frame)
        self.table.setItem(row_idx, 4, item_source)

        # Auto scroll to latest event
        self.table.scrollToBottom()

    def on_item_double_clicked(self, item):
        row = item.row()
        frame_item = self.table.item(row, 3)
        if frame_item:
            frame_num = frame_item.data(Qt.ItemDataRole.UserRole)
            if frame_num is not None:
                self.jump_to_frame.emit(int(frame_num))

    def apply_filter(self, idx: int):
        for r in range(self.table.rowCount()):
            item_hazard = self.table.item(r, 1)
            if not item_hazard:
                continue
            text = item_hazard.text()
            if idx == 0:
                self.table.setRowHidden(r, False)
            elif idx == 1:
                self.table.setRowHidden(r, "FIRE" not in text)
            elif idx == 2:
                self.table.setRowHidden(r, "SMOKE" not in text)

    def clear_log(self):
        self.table.setRowCount(0)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Log to CSV", "detection_log.csv", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Hazard", "Confidence", "Frame Number", "Source File"])
            for r in range(self.table.rowCount()):
                row_data = [
                    self.table.item(r, c).text() if self.table.item(r, c) else ""
                    for c in range(5)
                ]
                writer.writerow(row_data)
