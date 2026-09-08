import sys
import os
import time
import numpy as np
from PyQt6.QtWidgets import QApplication
from app.core.detector import FireSmokeDetector
from app.core.video_worker import VideoWorker

def test_detector():
    print("[1/3] Testing FireSmokeDetector...")
    weights_path = "weights/fire_smoke_yolov8n.pt"
    assert os.path.exists(weights_path), "Weights file missing!"
    
    detector = FireSmokeDetector(weights_path)
    info = detector.get_model_info()
    print(f"   Model Info: {info}")
    assert detector.is_loaded, "Model should be loaded"
    assert "fire" in str(info["classes"]).lower() or "smoke" in str(info["classes"]).lower()

    # Test prediction on dummy image
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = detector.predict(dummy_frame)
    print(f"   Inference Latency: {res['latency_ms']:.2f} ms")
    assert "detections" in res
    assert "fire_count" in res
    assert "smoke_count" in res

    # Test both Abonia1 and Kerby models
    for wp in ["weights/abonia_fire_smoke_yolov8.pt", "weights/fire_smoke_yolov8n.pt"]:
        if os.path.exists(wp):
            d = FireSmokeDetector(wp)
            info = d.get_model_info()
            print(f"   Tested {wp}: {info['classes']} on {info['device']}")
            assert d.is_loaded
    print("   FireSmokeDetector test passed!")

def test_worker_and_signals():
    print("[2/3] Testing VideoWorker & Signals...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    worker = VideoWorker("weights/fire_smoke_yolov8n.pt")
    
    signals_received = {
        "frame_ready": 0,
        "progress": 0,
        "stats": 0,
        "model_loaded": 0
    }

    def on_frame(f, det):
        signals_received["frame_ready"] += 1

    def on_progress(cf, tf, cs, ts):
        signals_received["progress"] += 1

    def on_stats(fps, lat, fire, smoke):
        signals_received["stats"] += 1

    def on_model_loaded(info):
        signals_received["model_loaded"] += 1

    worker.frame_ready.connect(on_frame)
    worker.playback_progress.connect(on_progress)
    worker.stats_updated.connect(on_stats)
    worker.model_loaded.connect(on_model_loaded)

    worker.start()
    
    # Wait for model initialization
    time.sleep(1.5)
    app.processEvents()

    sample_vid = "sample_videos/test_fire_smoke.mp4"
    assert os.path.exists(sample_vid), "Sample video missing!"
    
    # Load video source (model remains active)
    worker.load_source(sample_vid, auto_play=True)
    
    # Let it process several frames
    start = time.time()
    while time.time() - start < 1.5:
        app.processEvents()
        time.sleep(0.05)

    worker.close()
    print(f"   Signals received: {signals_received}")
    assert signals_received["model_loaded"] > 0, "Model loaded signal was not emitted"
    assert signals_received["frame_ready"] > 0, "Frame ready signal was not emitted"
    print("   VideoWorker test passed!")

def test_main_window_instantiation():
    print("[3/3] Testing MainWindow instantiation...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    from app.ui.main_window import MainWindow
    window = MainWindow("weights/fire_smoke_yolov8n.pt")
    assert window is not None
    assert window.video_display is not None
    assert window.playlist is not None
    assert window.stats_panel is not None
    assert window.alert_log is not None

    # Clean up
    window.worker.close()
    window.close()
    print("   MainWindow test passed!")

if __name__ == "__main__":
    test_detector()
    test_worker_and_signals()
    test_main_window_instantiation()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! ✅")
