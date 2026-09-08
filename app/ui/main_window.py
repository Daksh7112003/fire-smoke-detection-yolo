import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from app.core.video_worker import VideoWorker
from app.ui.video_widget import VideoDisplayWidget
from app.ui.controls_widget import VideoControlsWidget
from app.ui.playlist_widget import PlaylistWidget
from app.ui.stats_panel import StatsPanelWidget
from app.ui.alert_log_widget import AlertLogWidget
from app.ui.styles import DARK_THEME_QSS
from app.utils.helpers import save_snapshot, play_alert_sound

class MainWindow(QMainWindow):
    """
    Main Application Window for YOLO Fire & Smoke Real-Time Detection.
    Maintains persistent YOLO inference across video queues and streaming sources.
    """

    def __init__(self, weights_path: str = "weights/fire_smoke_yolov8n.pt"):
        super().__init__()
        self.setWindowTitle("Fire & Smoke YOLO Detection System — Real-Time Vision")
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)
        
        # Apply dark industrial stylesheet
        self.setStyleSheet(DARK_THEME_QSS)

        self.last_frame = None
        self.current_source_name = ""
        self.weights_path = weights_path

        # 1. Initialize UI Components
        self.init_ui()

        # 2. Setup Menus & Shortcuts
        self.init_menus()

        # 3. Initialize Background Video & Inference Worker
        self.init_worker()

        # 4. Connect Signals and Slots
        self.connect_signals()

        # Timer to reset hazard highlight border on the video widget
        self.hazard_display_timer = QTimer(self)
        self.hazard_display_timer.setInterval(800)
        self.hazard_display_timer.timeout.connect(lambda: self.video_display.set_hazard_alert("NORMAL"))

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Main 3-panel horizontal splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(4)

        # Left Panel: Video Playlist / Queue
        self.playlist = PlaylistWidget()
        self.playlist.setMinimumWidth(240)
        self.main_splitter.addWidget(self.playlist)

        # Center Panel: Video Display + Playback Controls
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)

        self.video_display = VideoDisplayWidget()
        self.controls = VideoControlsWidget()

        center_layout.addWidget(self.video_display, stretch=1)
        center_layout.addWidget(self.controls, stretch=0)
        self.main_splitter.addWidget(center_container)

        # Right Panel: Stats HUD + Thresholds + Audit Log
        right_container = QWidget()
        right_container.setMinimumWidth(280)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.stats_panel = StatsPanelWidget()
        self.alert_log = AlertLogWidget()

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.stats_panel)
        right_splitter.addWidget(self.alert_log)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 2)

        right_layout.addWidget(right_splitter)
        self.main_splitter.addWidget(right_container)

        # Splitter proportion defaults: 22% Left, 54% Center, 24% Right
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 6)
        self.main_splitter.setStretchFactor(2, 2)

        main_layout.addWidget(self.main_splitter)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Initializing YOLO Engine...")

    def init_menus(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        act_add_video = QAction("Add Video(s)...", self)
        act_add_video.setShortcut(QKeySequence("Ctrl+O"))
        act_add_video.triggered.connect(self.playlist.browse_files)
        file_menu.addAction(act_add_video)

        act_add_folder = QAction("Add Video Folder...", self)
        act_add_folder.setShortcut(QKeySequence("Ctrl+Shift+O"))
        act_add_folder.triggered.connect(self.playlist.browse_folder)
        file_menu.addAction(act_add_folder)

        act_open_camera = QAction("Open Live Camera...", self)
        act_open_camera.setShortcut(QKeySequence("Ctrl+K"))
        act_open_camera.triggered.connect(self.playlist.open_camera_dialog)
        file_menu.addAction(act_open_camera)

        file_menu.addSeparator()

        act_snapshot = QAction("Capture Snapshot", self)
        act_snapshot.setShortcut(QKeySequence("Ctrl+S"))
        act_snapshot.triggered.connect(self.capture_snapshot)
        file_menu.addAction(act_snapshot)

        file_menu.addSeparator()

        act_exit = QAction("Exit", self)
        act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Model Menu
        model_menu = menubar.addMenu("&Model")

        act_default_model = QAction("Default: Kerby Benchmark (YOLOv8n)", self)
        act_default_model.triggered.connect(lambda: self.worker.switch_model("weights/fire_smoke_yolov8n.pt"))
        model_menu.addAction(act_default_model)

        model_menu.addSeparator()

        act_load_model = QAction("Load Custom Model (.pt)...", self)
        act_load_model.setShortcut(QKeySequence("Ctrl+M"))
        act_load_model.triggered.connect(self.stats_panel.browse_model_weights)
        model_menu.addAction(act_load_model)

        # View Menu
        view_menu = menubar.addMenu("&View")

        act_fullscreen = QAction("Toggle Fullscreen", self)
        act_fullscreen.setShortcut(QKeySequence("F11"))
        act_fullscreen.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(act_fullscreen)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        act_about = QAction("About / Paper Findings", self)
        act_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(act_about)

    def init_worker(self):
        """Start the VideoWorker QThread with the persistent YOLO model."""
        self.worker = VideoWorker(weights_path=self.weights_path, parent=self)
        self.worker.start()

    def connect_signals(self):
        # 1. Playlist to Worker
        self.playlist.video_selected.connect(self.on_video_selected)
        self.playlist.camera_selected.connect(self.on_camera_selected)
        self.playlist.loop_toggled.connect(self.worker.set_loop)
        
        # Drag and drop onto video viewport
        self.video_display.files_dropped.connect(self.playlist.add_multiple_paths)

        # 2. Worker to UI
        self.worker.frame_ready.connect(self.on_frame_ready)
        self.worker.playback_progress.connect(self.controls.update_progress)
        self.worker.stats_updated.connect(self.stats_panel.update_metrics)
        self.worker.hazard_alert.connect(self.on_hazard_alert)
        self.worker.video_finished.connect(self.on_video_finished)
        self.worker.status_changed.connect(self.status_bar.showMessage)
        self.worker.model_loaded.connect(self.stats_panel.set_model_info)
        self.worker.error_occurred.connect(self.on_error)

        # 3. Controls to Worker
        self.controls.play_toggled.connect(self.on_toggle_play)
        self.controls.stop_clicked.connect(self.on_stop)
        self.controls.seek_requested.connect(self.worker.seek_to_frame)
        self.controls.step_forward_clicked.connect(self.worker.step_forward)
        self.controls.step_backward_clicked.connect(self.worker.step_backward)
        self.controls.speed_changed.connect(self.worker.set_speed)
        self.controls.snapshot_clicked.connect(self.capture_snapshot)

        # 4. Stats Panel to Worker
        self.stats_panel.conf_changed.connect(self.worker.set_conf_threshold)
        self.stats_panel.iou_changed.connect(self.worker.set_iou_threshold)
        self.stats_panel.overlays_changed.connect(self.worker.set_overlays)
        self.stats_panel.model_switch_requested.connect(self.worker.switch_model)

        # 5. Alert Log to Worker
        self.alert_log.jump_to_frame.connect(self.worker.seek_to_frame)

    # ---------------- UI Event Handlers ---------------- #

    def on_video_selected(self, path: str):
        self.current_source_name = path
        self.worker.load_source(path, auto_play=True)
        self.controls.set_playing_state(True)

    def on_camera_selected(self, cam_idx: int):
        self.current_source_name = f"Camera #{cam_idx}"
        self.worker.load_source(cam_idx, auto_play=True)
        self.controls.set_playing_state(True)

    def on_toggle_play(self):
        is_playing = self.worker.toggle_play()
        self.controls.set_playing_state(is_playing)

    def on_stop(self):
        self.worker.stop()
        self.controls.set_playing_state(False)
        self.video_display.clear_display()

    def on_frame_ready(self, frame, detections_dict):
        self.last_frame = frame
        hazard_type = "NORMAL"
        if detections_dict.get("fire_count", 0) > 0:
            hazard_type = "FIRE"
        elif detections_dict.get("smoke_count", 0) > 0:
            hazard_type = "SMOKE"
            
        self.video_display.set_frame(frame, hazard=hazard_type)

    def on_hazard_alert(self, hazard_type: str, count: int, max_conf: float):
        # Update HUD banner
        self.stats_panel.trigger_hazard(hazard_type, count, max_conf)
        
        # Highlight video border
        self.video_display.set_hazard_alert(hazard_type)
        self.hazard_display_timer.start()

        # Log into audit table
        curr_frame = self.worker.current_frame_idx
        self.alert_log.log_event(hazard_type, max_conf, curr_frame, self.current_source_name)

        # Sound alert if enabled
        if self.stats_panel.audio_alert_enabled:
            play_alert_sound()

    def on_video_finished(self):
        # Auto-play next video in queue
        advanced = self.playlist.play_next()
        if not advanced:
            self.controls.set_playing_state(False)
            self.status_bar.showMessage("Video playback completed.")

    def capture_snapshot(self):
        if self.last_frame is not None:
            saved_path = save_snapshot(self.last_frame, base_dir="snapshots", prefix="fire_smoke_det")
            self.status_bar.showMessage(f"Snapshot saved: {saved_path}", 4000)
        else:
            self.status_bar.showMessage("No frame available to capture snapshot.", 3000)

    def on_error(self, message: str):
        self.status_bar.showMessage(f"Error: {message}")
        QMessageBox.warning(self, "Detection System Warning", message)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_about_dialog(self):
        text = (
            "<h3>Fire & Smoke Detection using YOLO</h3>"
            "<p><b>Model Architecture:</b> Lightweight Anchor-Free YOLO (Ultralytics)</p>"
            "<p><b>Research Paper Benchmark:</b> YOLO11n / YOLOv8n fine-tuned on Kerby dataset (35,000+ images).</p>"
            "<p><b>Latency:</b> ~38-40ms real-time inference pipeline.</p>"
            "<p><b>Application Features:</b>"
            "<ul>"
            "<li>Persistent YOLO worker remains loaded in memory while switching videos</li>"
            "<li>Multi-video queue, folder scanning, and live camera streaming</li>"
            "<li>Real-time bounding box annotations with Fire/Smoke hazard classification</li>"
            "<li>Hazard strobe alerts, audio alarms, and interactive event audit log</li>"
            "</ul></p>"
        )
        QMessageBox.about(self, "About Fire & Smoke YOLO Application", text)

    def closeEvent(self, event):
        """Clean shutdown of threads on window close."""
        self.worker.close()
        event.accept()
