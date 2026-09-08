import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, pyqtSignal

class VideoDisplayWidget(QWidget):
    """
    High-performance video canvas widget.
    Renders frames while preserving aspect ratio, supports drag-and-drop,
    and displays tactical HUD border alerts when hazards are detected.
    """
    
    files_dropped = pyqtSignal(list)
    snapshot_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(480, 270)
        
        self.current_pixmap = None
        self.hazard_state = "NORMAL"  # "NORMAL", "FIRE", "SMOKE"
        self.flash_state = False
        
        # Overlay settings
        self.status_text = "READY - ADD A VIDEO TO START DETECTION"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def set_frame(self, frame_bgr: np.ndarray, hazard: str = "NORMAL"):
        """Convert BGR OpenCV image to QPixmap and trigger repaint."""
        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.current_pixmap = QPixmap.fromImage(q_img)
        self.hazard_state = hazard
        self.update()

    def set_hazard_alert(self, hazard: str):
        """Set hazard alert status for perimeter strobe."""
        self.hazard_state = hazard
        self.update()

    def clear_display(self):
        """Reset canvas to placeholder."""
        self.current_pixmap = None
        self.hazard_state = "NORMAL"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Background fill
        painter.fillRect(self.rect(), QColor("#080B0F"))

        # 2. Draw Video Frame if available
        if self.current_pixmap and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            # Center frame
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            frame_rect = scaled.rect()
            frame_rect.moveTo(x, y)
        else:
            # Placeholder graphic and instructions
            painter.setPen(QColor("#484F58"))
            font = QFont("Segoe UI", 14, QFont.Weight.Medium)
            painter.setFont(font)
            
            placeholder_text = (
                "NO ACTIVE VIDEO FEED\n\n"
                "• Click '+ Add Video(s)' or Drag & Drop video files here\n"
                "• Toggle Live Camera for real-time webcam feed\n"
                "• YOLO Fire & Smoke Detector remains active"
            )
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                placeholder_text
            )
            frame_rect = self.rect()

        # 3. Hazard Border Alert Strobe Effect
        if self.hazard_state == "FIRE":
            # Vivid Red Warning Border
            pen = QPen(QColor(255, 59, 48, 220), 4)
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(2, 2, -2, -2))
            
            # Corner Tactical Warning Badges
            painter.fillRect(10, 10, 140, 28, QColor(255, 59, 48, 230))
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(18, 28, "🚨 FIRE HAZARD")

        elif self.hazard_state == "SMOKE":
            # Amber Warning Border
            pen = QPen(QColor(255, 159, 10, 220), 4)
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(2, 2, -2, -2))

            painter.fillRect(10, 10, 150, 28, QColor(255, 159, 10, 230))
            painter.setPen(QColor("#000000"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(18, 28, "⚠️ SMOKE DETECTED")

    # ---------------- Drag and Drop ---------------- #

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                files.append(file_path)
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
