import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from app.ui.main_window import MainWindow

def main():
    parser = argparse.ArgumentParser(description="Fire & Smoke YOLO PyQt6 Application")
    parser.add_argument("--weights", type=str, default="weights/fire_smoke_yolov8n.pt", help="Path to YOLO weights .pt file")
    parser.add_argument("--video", type=str, default="", help="Optional initial video path to open")
    args = parser.parse_args()

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("FireSmokeDetectorYOLO")
    app.setOrganizationName("FireSmokeSafety")

    # Check weights path
    weights_path = args.weights
    if not os.path.exists(weights_path):
        if os.path.exists("weights/fire_smoke_yolov8n.pt"):
            weights_path = "weights/fire_smoke_yolov8n.pt"

    window = MainWindow(weights_path=weights_path)
    window.show()

    # Load initial video if specified
    if args.video and os.path.exists(args.video):
        window.playlist.add_video_path(args.video)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
