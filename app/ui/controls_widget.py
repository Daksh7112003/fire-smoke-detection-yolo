from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QSlider, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from app.utils.helpers import format_time

class VideoControlsWidget(QWidget):
    """
    Playback transport controls: Play, Pause, Stop, Step, 
    Interactive Scrubber Slider, Playback Speed, and Snapshot button.
    """
    play_toggled = pyqtSignal()
    stop_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)
    step_forward_clicked = pyqtSignal()
    step_backward_clicked = pyqtSignal()
    speed_changed = pyqtSignal(float)
    snapshot_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_slider_tracking = False
        self.total_frames = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        # 1. Timeline Scrubber and Timestamp Row
        timeline_layout = QHBoxLayout()
        timeline_layout.setSpacing(8)

        self.lbl_current_time = QLabel("00:00")
        self.lbl_current_time.setStyleSheet("color: #58A6FF; font-weight: 600; min-width: 45px;")
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setObjectName("timelineSlider")
        self.slider.setRange(0, 1000)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.sliderMoved.connect(self.on_slider_moved)

        self.lbl_total_time = QLabel("00:00")
        self.lbl_total_time.setStyleSheet("color: #8B949E; min-width: 45px;")

        timeline_layout.addWidget(self.lbl_current_time)
        timeline_layout.addWidget(self.slider)
        timeline_layout.addWidget(self.lbl_total_time)
        layout.addLayout(timeline_layout)

        # 2. Transport Buttons Row
        transport_layout = QHBoxLayout()
        transport_layout.setSpacing(8)

        self.btn_step_back = QPushButton("⏮ -1")
        self.btn_step_back.setObjectName("controlBtn")
        self.btn_step_back.setToolTip("Step 1 frame backward")
        self.btn_step_back.clicked.connect(self.step_backward_clicked.emit)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setObjectName("primaryBtn")
        self.btn_play.setMinimumWidth(85)
        self.btn_play.clicked.connect(self.play_toggled.emit)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("controlBtn")
        self.btn_stop.clicked.connect(self.stop_clicked.emit)

        self.btn_step_forward = QPushButton("+1 ⏭")
        self.btn_step_forward.setObjectName("controlBtn")
        self.btn_step_forward.setToolTip("Step 1 frame forward")
        self.btn_step_forward.clicked.connect(self.step_forward_clicked.emit)

        transport_layout.addWidget(self.btn_step_back)
        transport_layout.addWidget(self.btn_play)
        transport_layout.addWidget(self.btn_stop)
        transport_layout.addWidget(self.btn_step_forward)

        transport_layout.addSpacing(15)

        # Playback Speed Selector
        lbl_speed = QLabel("Speed:")
        lbl_speed.setStyleSheet("color: #8B949E;")
        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["0.25x", "0.5x", "1.0x", "1.5x", "2.0x"])
        self.combo_speed.setCurrentText("1.0x")
        self.combo_speed.currentIndexChanged.connect(self.on_speed_changed)
        
        transport_layout.addWidget(lbl_speed)
        transport_layout.addWidget(self.combo_speed)

        transport_layout.addStretch()

        # Snapshot Capture Button
        self.btn_snapshot = QPushButton("📷 Capture Snapshot")
        self.btn_snapshot.setObjectName("controlBtn")
        self.btn_snapshot.setToolTip("Save annotated frame to snapshots folder")
        self.btn_snapshot.clicked.connect(self.snapshot_clicked.emit)
        transport_layout.addWidget(self.btn_snapshot)

        layout.addLayout(transport_layout)

    def set_playing_state(self, is_playing: bool):
        if is_playing:
            self.btn_play.setText("⏸ Pause")
            self.btn_play.setObjectName("controlBtn")
        else:
            self.btn_play.setText("▶ Play")
            self.btn_play.setObjectName("primaryBtn")
        self.btn_play.setStyle(self.btn_play.style())

    def update_progress(self, curr_frame: int, total_frames: int, curr_sec: float, total_sec: float):
        self.total_frames = total_frames
        self.lbl_current_time.setText(format_time(curr_sec))
        self.lbl_total_time.setText(format_time(total_sec))

        if not self.is_slider_tracking and total_frames > 0:
            pos = int((curr_frame / total_frames) * 1000)
            self.slider.blockSignals(True)
            self.slider.setValue(pos)
            self.slider.blockSignals(False)

    def on_slider_pressed(self):
        self.is_slider_tracking = True

    def on_slider_released(self):
        self.is_slider_tracking = False
        if self.total_frames > 0:
            target_frame = int((self.slider.value() / 1000.0) * self.total_frames)
            self.seek_requested.emit(target_frame)

    def on_slider_moved(self, value):
        if self.total_frames > 0:
            sec = (value / 1000.0) * (self.total_frames / 30.0)
            self.lbl_current_time.setText(format_time(sec))

    def on_speed_changed(self, idx):
        text = self.combo_speed.currentText().replace("x", "")
        try:
            val = float(text)
            self.speed_changed.emit(val)
        except ValueError:
            pass
