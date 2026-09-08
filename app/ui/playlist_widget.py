import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QListWidgetItem, QFileDialog, QGroupBox,
    QCheckBox, QLabel, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm", ".m4v"}

class PlaylistWidget(QWidget):
    """
    Playlist / Queue management widget for adding, ordering,
    and switching video inputs seamlessly while model stays active.
    """
    video_selected = pyqtSignal(str)
    camera_selected = pyqtSignal(int)
    loop_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = -1
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        group_box = QGroupBox("VIDEO QUEUE & SOURCES")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(8)

        # Video List
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        group_layout.addWidget(self.list_widget)

        # Action Buttons Row 1: Add Video / Folder
        btn_layout_1 = QHBoxLayout()
        self.btn_add_files = QPushButton("+ Add Video(s)")
        self.btn_add_files.setObjectName("primaryBtn")
        self.btn_add_files.clicked.connect(self.browse_files)
        
        self.btn_add_folder = QPushButton("+ Add Folder")
        self.btn_add_folder.clicked.connect(self.browse_folder)
        
        btn_layout_1.addWidget(self.btn_add_files)
        btn_layout_1.addWidget(self.btn_add_folder)
        group_layout.addLayout(btn_layout_1)

        # Action Buttons Row 2: Camera & Stream
        btn_layout_2 = QHBoxLayout()
        self.btn_camera = QPushButton("📹 Live Camera")
        self.btn_camera.clicked.connect(self.open_camera_dialog)

        self.btn_remove = QPushButton("✕ Remove")
        self.btn_remove.clicked.connect(self.remove_selected)

        self.btn_clear = QPushButton("🗑 Clear")
        self.btn_clear.clicked.connect(self.clear_all)

        btn_layout_2.addWidget(self.btn_camera)
        btn_layout_2.addWidget(self.btn_remove)
        btn_layout_2.addWidget(self.btn_clear)
        group_layout.addLayout(btn_layout_2)

        # Options: Auto-play next & Loop
        options_layout = QHBoxLayout()
        self.chk_autoplay_next = QCheckBox("Auto-play Next")
        self.chk_autoplay_next.setChecked(True)
        
        self.chk_loop = QCheckBox("Loop Video")
        self.chk_loop.setChecked(False)
        self.chk_loop.toggled.connect(self.loop_toggled.emit)

        options_layout.addWidget(self.chk_autoplay_next)
        options_layout.addWidget(self.chk_loop)
        group_layout.addLayout(options_layout)

        main_layout.addWidget(group_box)

    def add_video_path(self, path: str, auto_select_if_first: bool = True):
        """Add a single video file to playlist."""
        if not os.path.exists(path):
            return
        
        filename = os.path.basename(path)
        item = QListWidgetItem(f"🎬 {filename}")
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setToolTip(path)
        self.list_widget.addItem(item)

        if auto_select_if_first and self.list_widget.count() == 1:
            self.select_index(0)

    def add_multiple_paths(self, paths: list):
        """Add multiple video paths."""
        for p in paths:
            if os.path.isfile(p):
                ext = os.path.splitext(p)[1].lower()
                if ext in VIDEO_EXTENSIONS:
                    self.add_video_path(p, auto_select_if_first=False)
            elif os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS:
                            self.add_video_path(os.path.join(root, f), auto_select_if_first=False)

        if self.current_index == -1 and self.list_widget.count() > 0:
            self.select_index(0)

    def browse_files(self):
        filters = "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.m4v);;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", "", filters)
        if files:
            self.add_multiple_paths(files)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Video Folder")
        if folder:
            self.add_multiple_paths([folder])

    def open_camera_dialog(self):
        cam_id, ok = QInputDialog.getInt(
            self, "Open Camera Stream", "Enter Camera Device Index (0 for default):", 0, 0, 10, 1
        )
        if ok:
            item = QListWidgetItem(f"📹 Live Camera Device #{cam_id}")
            item.setData(Qt.ItemDataRole.UserRole, f"cam:{cam_id}")
            self.list_widget.addItem(item)
            row = self.list_widget.count() - 1
            self.select_index(row)

    def on_item_double_clicked(self, item):
        row = self.list_widget.row(item)
        self.select_index(row)

    def select_index(self, index: int):
        if 0 <= index < self.list_widget.count():
            self.current_index = index
            self.list_widget.setCurrentRow(index)
            item = self.list_widget.item(index)
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, str) and data.startswith("cam:"):
                cam_idx = int(data.split(":")[1])
                self.camera_selected.emit(cam_idx)
            else:
                self.video_selected.emit(data)

    def play_next(self):
        """Advance to next item in playlist if available."""
        if not self.chk_autoplay_next.isChecked():
            return False
        
        next_index = self.current_index + 1
        if next_index < self.list_widget.count():
            self.select_index(next_index)
            return True
        return False

    def remove_selected(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)
            if row == self.current_index:
                self.current_index = -1
                if self.list_widget.count() > 0:
                    self.select_index(min(row, self.list_widget.count() - 1))

    def clear_all(self):
        self.list_widget.clear()
        self.current_index = -1
