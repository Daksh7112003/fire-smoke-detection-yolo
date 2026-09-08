from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QSlider, QCheckBox, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

class StatsPanelWidget(QWidget):
    """
    HUD and Control Panel:
    - Hazard Status Banner
    - Live Performance Metrics (FPS, Latency, Object Counts)
    - Threshold Sliders (Confidence, IoU)
    - Overlay Toggles
    - Active Model Information & Swapper
    """
    conf_changed = pyqtSignal(float)
    iou_changed = pyqtSignal(float)
    overlays_changed = pyqtSignal(bool, bool, bool)
    model_switch_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_alert_enabled = True
        self.hazard_reset_timer = QTimer(self)
        self.hazard_reset_timer.setInterval(1200)
        self.hazard_reset_timer.timeout.connect(self.reset_hazard_banner)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Prominent Hazard Status Banner
        self.banner = QLabel("🟢 SYSTEM SECURE — NO HAZARDS")
        self.banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banner.setStyleSheet("""
            background-color: #1F3A2A;
            color: #3FB950;
            border: 1px solid #238636;
            border-radius: 6px;
            font-size: 13px;
            font-weight: bold;
            padding: 10px;
        """)
        layout.addWidget(self.banner)

        # 2. Live Performance & Hazard Counters
        metrics_group = QGroupBox("LIVE METRICS & COUNTERS")
        metrics_layout = QVBoxLayout(metrics_group)
        metrics_layout.setSpacing(6)

        # Row 1: Fire & Smoke counts
        counts_layout = QHBoxLayout()
        self.lbl_fire_count = QLabel("🔥 Fire: 0")
        self.lbl_fire_count.setStyleSheet("""
            background-color: #381A1C; color: #FF7B72; border: 1px solid #7D2426; 
            padding: 6px; border-radius: 4px; font-weight: bold;
        """)
        self.lbl_smoke_count = QLabel("💨 Smoke: 0")
        self.lbl_smoke_count.setStyleSheet("""
            background-color: #332512; color: #E3B341; border: 1px solid #7E5710; 
            padding: 6px; border-radius: 4px; font-weight: bold;
        """)
        counts_layout.addWidget(self.lbl_fire_count)
        counts_layout.addWidget(self.lbl_smoke_count)
        metrics_layout.addLayout(counts_layout)

        # Row 2: FPS & Latency
        perf_layout = QHBoxLayout()
        self.lbl_fps = QLabel("FPS: --")
        self.lbl_fps.setStyleSheet("color: #58A6FF; font-weight: 600;")
        
        self.lbl_latency = QLabel("Latency: -- ms")
        self.lbl_latency.setStyleSheet("color: #8B949E;")
        
        perf_layout.addWidget(self.lbl_fps)
        perf_layout.addWidget(self.lbl_latency)
        metrics_layout.addLayout(perf_layout)

        layout.addWidget(metrics_group)

        # 3. Detection Parameters & Thresholds
        settings_group = QGroupBox("DETECTION THRESHOLDS")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(8)

        # Confidence Slider
        conf_header = QHBoxLayout()
        conf_header.addWidget(QLabel("Confidence:"))
        self.lbl_conf_val = QLabel("40%")
        self.lbl_conf_val.setStyleSheet("color: #58A6FF; font-weight: bold;")
        conf_header.addWidget(self.lbl_conf_val)
        settings_layout.addLayout(conf_header)

        self.slider_conf = QSlider(Qt.Orientation.Horizontal)
        self.slider_conf.setRange(5, 100)
        self.slider_conf.setValue(40)
        self.slider_conf.valueChanged.connect(self.on_conf_changed)
        settings_layout.addWidget(self.slider_conf)

        # IoU Slider
        iou_header = QHBoxLayout()
        iou_header.addWidget(QLabel("IoU (NMS):"))
        self.lbl_iou_val = QLabel("45%")
        self.lbl_iou_val.setStyleSheet("color: #58A6FF; font-weight: bold;")
        iou_header.addWidget(self.lbl_iou_val)
        settings_layout.addLayout(iou_header)

        self.slider_iou = QSlider(Qt.Orientation.Horizontal)
        self.slider_iou.setRange(10, 95)
        self.slider_iou.setValue(45)
        self.slider_iou.valueChanged.connect(self.on_iou_changed)
        settings_layout.addWidget(self.slider_iou)

        # Display Toggles
        self.chk_boxes = QCheckBox("Draw Bounding Boxes")
        self.chk_boxes.setChecked(True)
        self.chk_boxes.toggled.connect(self.on_overlays_changed)
        settings_layout.addWidget(self.chk_boxes)

        self.chk_labels = QCheckBox("Draw Class Labels")
        self.chk_labels.setChecked(True)
        self.chk_labels.toggled.connect(self.on_overlays_changed)
        settings_layout.addWidget(self.chk_labels)

        self.chk_conf = QCheckBox("Show Confidence %")
        self.chk_conf.setChecked(True)
        self.chk_conf.toggled.connect(self.on_overlays_changed)
        settings_layout.addWidget(self.chk_conf)

        self.chk_audio = QCheckBox("Alert Sound on Detection")
        self.chk_audio.setChecked(True)
        self.chk_audio.toggled.connect(self.on_audio_toggled)
        settings_layout.addWidget(self.chk_audio)

        layout.addWidget(settings_group)

        # 4. Model Status & Custom Weight Loader
        model_group = QGroupBox("ACTIVE YOLO ENGINE")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(6)

        self.lbl_model_status = QLabel("● Active (In-Memory)")
        self.lbl_model_status.setStyleSheet("color: #3FB950; font-weight: 600;")
        model_layout.addWidget(self.lbl_model_status)

        self.lbl_device = QLabel("Hardware: Initializing...")
        self.lbl_device.setStyleSheet("color: #58A6FF; font-weight: 600; font-size: 11px;")
        model_layout.addWidget(self.lbl_device)

        self.lbl_model_name = QLabel("Weights: fire_smoke_yolov8n.pt")
        self.lbl_model_name.setStyleSheet("color: #8B949E; font-size: 11px;")
        self.lbl_model_name.setWordWrap(True)
        model_layout.addWidget(self.lbl_model_name)

        self.lbl_classes = QLabel("Classes: [smoke, fire]")
        self.lbl_classes.setStyleSheet("color: #8B949E; font-size: 11px;")
        model_layout.addWidget(self.lbl_classes)

        self.btn_load_model = QPushButton("📂 Load Custom Model (.pt)")
        self.btn_load_model.clicked.connect(self.browse_model_weights)
        model_layout.addWidget(self.btn_load_model)

        layout.addWidget(model_group)
        layout.addStretch()

    # ---------------- Slots & Handlers ---------------- #

    def update_metrics(self, fps: float, latency_ms: float, fire_count: int, smoke_count: int):
        self.lbl_fps.setText(f"FPS: {fps:.1f}")
        self.lbl_latency.setText(f"Latency: {latency_ms:.1f} ms")
        self.lbl_fire_count.setText(f"🔥 Fire: {fire_count}")
        self.lbl_smoke_count.setText(f"💨 Smoke: {smoke_count}")

    def trigger_hazard(self, hazard_type: str, count: int, max_conf: float):
        """Update banner to alert status."""
        self.hazard_reset_timer.stop()
        
        if hazard_type == "FIRE":
            self.banner.setText(f"🚨 FIRE DETECTED! ({count}) — {max_conf*100:.0f}%")
            self.banner.setStyleSheet("""
                background-color: #DA3633;
                color: #FFFFFF;
                border: 2px solid #F85149;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
            """)
        elif hazard_type == "SMOKE":
            self.banner.setText(f"⚠️ SMOKE DETECTED! ({count}) — {max_conf*100:.0f}%")
            self.banner.setStyleSheet("""
                background-color: #9E6A03;
                color: #FFFFFF;
                border: 2px solid #F2CC60;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
            """)

        self.hazard_reset_timer.start()

    def reset_hazard_banner(self):
        self.banner.setText("🟢 SYSTEM SECURE — NO HAZARDS")
        self.banner.setStyleSheet("""
            background-color: #1F3A2A;
            color: #3FB950;
            border: 1px solid #238636;
            border-radius: 6px;
            font-size: 13px;
            font-weight: bold;
            padding: 10px;
        """)

    def set_model_info(self, info: dict):
        self.lbl_model_name.setText(f"Weights: {info.get('path', 'Unknown')}")
        self.lbl_device.setText(f"Device: {info.get('device', 'Auto')}")
        classes_dict = info.get("classes", {})
        classes_str = ", ".join(classes_dict.values()) if classes_dict else "Unknown"
        self.lbl_classes.setText(f"Classes: [{classes_str}]")

    def on_conf_changed(self, value: int):
        self.lbl_conf_val.setText(f"{value}%")
        self.conf_changed.emit(value / 100.0)

    def on_iou_changed(self, value: int):
        self.lbl_iou_val.setText(f"{value}%")
        self.iou_changed.emit(value / 100.0)

    def on_overlays_changed(self):
        self.overlays_changed.emit(
            self.chk_boxes.isChecked(),
            self.chk_labels.isChecked(),
            self.chk_conf.isChecked()
        )

    def on_audio_toggled(self, checked: bool):
        self.audio_alert_enabled = checked

    def browse_model_weights(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLO Model Weights", "", "PyTorch Weights (*.pt);;All Files (*.*)"
        )
        if path:
            self.model_switch_requested.emit(path)
