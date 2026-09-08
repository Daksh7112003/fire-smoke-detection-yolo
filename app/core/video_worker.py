import time
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from app.core.detector import FireSmokeDetector

class InferenceWorker(QThread):
    """
    Dedicated background worker thread for GPU YOLO inference.
    Decoupled from video playback so playback stays locked at steady 30 FPS.
    """
    stats_updated = pyqtSignal(float, float, int, int)  # (fps, latency_ms, fire_count, smoke_count)
    hazard_alert = pyqtSignal(str, int, float)          # (hazard_type, count, max_conf)
    model_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, weights_path: str = "weights/fire_smoke_yolov8n.pt", parent=None):
        super().__init__(parent)
        self.weights_path = weights_path
        self.detector = None
        self.is_running = True
        
        # Frame queue (holds the latest frame to process)
        self.latest_frame = None
        self.has_new_frame = False
        
        # Inference settings
        self.conf_threshold = 0.40
        self.iou_threshold = 0.45
        
        # Shared detection results
        self.results_mutex = QMutex()
        self.latest_detections = {
            "detections": [],
            "fire_count": 0,
            "smoke_count": 0,
            "latency_ms": 0.0,
            "max_conf": 0.0,
            "timestamp": 0.0
        }
        
        self.cond_mutex = QMutex()
        self.wait_condition = QWaitCondition()

    def run(self):
        try:
            self.detector = FireSmokeDetector(self.weights_path)
            self.model_loaded.emit(self.detector.get_model_info())
        except Exception as e:
            self.error_occurred.emit(f"Failed to load YOLO model: {str(e)}")
            return

        fps_timer = time.perf_counter()
        inference_count = 0
        inference_fps = 0.0

        while self.is_running:
            self.cond_mutex.lock()
            while not self.has_new_frame and self.is_running:
                self.wait_condition.wait(self.cond_mutex, 50)
                
            if not self.is_running:
                self.cond_mutex.unlock()
                break

            # Grab latest frame
            frame_to_process = self.latest_frame
            self.has_new_frame = False
            self.cond_mutex.unlock()

            if frame_to_process is None:
                continue

            # Run GPU inference
            res = self.detector.predict(
                frame_to_process, 
                conf=self.conf_threshold, 
                iou=self.iou_threshold
            )
            res["timestamp"] = time.perf_counter()

            # Store result thread-safely
            self.results_mutex.lock()
            self.latest_detections = res
            self.results_mutex.unlock()

            # Alerts
            if res["fire_count"] > 0:
                self.hazard_alert.emit("FIRE", res["fire_count"], res["max_conf"])
            elif res["smoke_count"] > 0:
                self.hazard_alert.emit("SMOKE", res["smoke_count"], res["max_conf"])

            # Calculate inference FPS
            inference_count += 1
            now = time.perf_counter()
            if now - fps_timer >= 0.5:
                inference_fps = inference_count / (now - fps_timer)
                inference_count = 0
                fps_timer = now

            self.stats_updated.emit(
                inference_fps, res["latency_ms"], res["fire_count"], res["smoke_count"]
            )

    def submit_frame(self, frame: np.ndarray):
        """Submit a frame for asynchronous inference without blocking."""
        self.cond_mutex.lock()
        self.latest_frame = frame
        self.has_new_frame = True
        self.wait_condition.wakeOne()
        self.cond_mutex.unlock()

    def get_latest_detections(self) -> dict:
        """Fetch the most recent detection result."""
        self.results_mutex.lock()
        res = self.latest_detections
        self.results_mutex.unlock()
        return res

    def set_thresholds(self, conf: float, iou: float):
        self.conf_threshold = conf
        self.iou_threshold = iou

    def switch_model(self, new_weights: str):
        self.cond_mutex.lock()
        try:
            self.detector.load_model(new_weights)
            self.weights_path = new_weights
            self.model_loaded.emit(self.detector.get_model_info())
        except Exception as e:
            self.error_occurred.emit(f"Failed to switch model: {str(e)}")
        finally:
            self.cond_mutex.unlock()

    def stop(self):
        self.is_running = False
        self.cond_mutex.lock()
        self.wait_condition.wakeAll()
        self.cond_mutex.unlock()
        self.wait(1000)


class VideoWorker(QThread):
    """
    Master Playback Worker Thread.
    Decoupled from inference to guarantee smooth, zero-lag 30+ FPS playback.
    """
    frame_ready = pyqtSignal(np.ndarray, dict)
    playback_progress = pyqtSignal(int, int, float, float)
    stats_updated = pyqtSignal(float, float, int, int)
    hazard_alert = pyqtSignal(str, int, float)
    video_finished = pyqtSignal()
    status_changed = pyqtSignal(str)
    model_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, weights_path: str = "weights/fire_smoke_yolov8n.pt", parent=None):
        super().__init__(parent)
        self.weights_path = weights_path
        
        # Dedicated GPU inference worker
        self.inference_worker = InferenceWorker(weights_path)
        self.inference_worker.stats_updated.connect(self.stats_updated.emit)
        self.inference_worker.hazard_alert.connect(self.hazard_alert.emit)
        self.inference_worker.model_loaded.connect(self.model_loaded.emit)
        self.inference_worker.error_occurred.connect(self.error_occurred.emit)
        self.inference_worker.start()

        # Source state
        self.cap = None
        self.current_source = None
        self.is_camera = False
        
        # Video properties
        self.total_frames = 0
        self.native_fps = 30.0
        self.duration_sec = 0.0
        self.current_frame_idx = 0
        
        # Playback controls
        self.is_running = True
        self.is_paused = True
        self.playback_speed = 1.0
        self.loop_video = False
        self.seek_requested = -1
        self.step_requested = 0
        
        # Visualization options
        self.show_boxes = True
        self.show_labels = True
        self.show_conf = True

        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()

    def run(self):
        self.status_changed.emit("YOLO Engine Active on GPU. Ready for video input.")

        while self.is_running:
            self.mutex.lock()
            
            if self.cap is None or not self.cap.isOpened():
                self.wait_condition.wait(self.mutex, 100)
                self.mutex.unlock()
                continue

            if self.is_paused and self.seek_requested < 0 and self.step_requested == 0:
                self.wait_condition.wait(self.mutex, 100)
                self.mutex.unlock()
                continue

            # Handle seeking
            if self.seek_requested >= 0:
                target_frame = max(0, min(self.seek_requested, self.total_frames - 1))
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                self.current_frame_idx = target_frame
                self.seek_requested = -1

            # Handle single-frame stepping
            if self.step_requested != 0:
                target_frame = max(0, min(self.current_frame_idx + self.step_requested, self.total_frames - 1))
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                self.current_frame_idx = target_frame
                self.step_requested = 0

            # Clock timing for smooth 30 FPS playback
            frame_start = time.perf_counter()
            
            ret, frame = self.cap.read()
            if not ret:
                if not self.is_camera and self.loop_video:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame_idx = 0
                    self.mutex.unlock()
                    continue
                else:
                    self.is_paused = True
                    self.mutex.unlock()
                    self.video_finished.emit()
                    continue

            self.current_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            curr_sec = self.current_frame_idx / max(1.0, self.native_fps)
            
            s_boxes = self.show_boxes
            s_labels = self.show_labels
            s_conf = self.show_conf
            speed = self.playback_speed
            is_paused_now = self.is_paused
            fps = self.native_fps
            self.mutex.unlock()

            # Submit frame asynchronously to GPU inference worker (non-blocking)
            self.inference_worker.submit_frame(frame)

            # Get latest available detections to overlay
            det_res = self.inference_worker.get_latest_detections()
            
            # Annotate frame
            if self.inference_worker.detector:
                annotated = self.inference_worker.detector.annotate(
                    frame, det_res.get("detections", []),
                    show_boxes=s_boxes, show_labels=s_labels, show_conf=s_conf
                )
            else:
                annotated = frame

            # Deliver smooth frame to UI
            self.frame_ready.emit(annotated, det_res)
            self.playback_progress.emit(
                self.current_frame_idx, self.total_frames, curr_sec, self.duration_sec
            )

            # Precise frame-rate throttling to ensure rock-solid 30 FPS
            if not self.is_camera and not is_paused_now:
                target_frame_time = (1.0 / max(10.0, fps)) / max(0.1, speed)
                elapsed = time.perf_counter() - frame_start
                sleep_duration = target_frame_time - elapsed
                if sleep_duration > 0.001:
                    time.sleep(sleep_duration)

    # ---------------- Control Methods ---------------- #

    def load_source(self, source_path: str or int, auto_play: bool = True):
        self.mutex.lock()
        try:
            if self.cap is not None:
                self.cap.release()

            if isinstance(source_path, int) or (isinstance(source_path, str) and source_path.isdigit()):
                cam_idx = int(source_path)
                self.cap = cv2.VideoCapture(cam_idx)
                self.is_camera = True
                self.current_source = f"Camera #{cam_idx}"
                self.total_frames = 0
                self.native_fps = 30.0
                self.duration_sec = 0.0
            else:
                self.cap = cv2.VideoCapture(source_path)
                self.is_camera = False
                self.current_source = source_path
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps_val = self.cap.get(cv2.CAP_PROP_FPS)
                self.native_fps = fps_val if (fps_val and fps_val > 5.0) else 30.0
                self.duration_sec = self.total_frames / max(1.0, self.native_fps)

            self.current_frame_idx = 0
            if not self.cap.isOpened():
                self.error_occurred.emit(f"Could not open video: {source_path}")
                return

            self.is_paused = not auto_play
            self.status_changed.emit(f"Active Source: {self.current_source} | GPU Accelerated (30 FPS)")
            self.wait_condition.wakeAll()
        finally:
            self.mutex.unlock()

    def play(self):
        self.mutex.lock()
        self.is_paused = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def pause(self):
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()

    def toggle_play(self):
        self.mutex.lock()
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.wait_condition.wakeAll()
        self.mutex.unlock()
        return not self.is_paused

    def stop(self):
        self.mutex.lock()
        self.is_paused = True
        if self.cap is not None and not self.is_camera:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_idx = 0
        self.mutex.unlock()

    def seek_to_frame(self, frame_idx: int):
        self.mutex.lock()
        self.seek_requested = frame_idx
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def step_forward(self):
        self.mutex.lock()
        self.step_requested = 1
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def step_backward(self):
        self.mutex.lock()
        self.step_requested = -1
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def set_speed(self, speed: float):
        self.mutex.lock()
        self.playback_speed = max(0.1, min(speed, 5.0))
        self.mutex.unlock()

    def set_loop(self, loop: bool):
        self.mutex.lock()
        self.loop_video = loop
        self.mutex.unlock()

    def set_conf_threshold(self, conf: float):
        self.inference_worker.set_thresholds(conf, self.inference_worker.iou_threshold)

    def set_iou_threshold(self, iou: float):
        self.inference_worker.set_thresholds(self.inference_worker.conf_threshold, iou)

    def set_overlays(self, show_boxes: bool, show_labels: bool, show_conf: bool):
        self.mutex.lock()
        self.show_boxes = show_boxes
        self.show_labels = show_labels
        self.show_conf = show_conf
        self.mutex.unlock()

    def switch_model(self, new_weights: str):
        self.inference_worker.switch_model(new_weights)

    def close(self):
        self.mutex.lock()
        self.is_running = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()
        
        self.inference_worker.stop()
        self.wait(1000)
        
        if self.cap is not None:
            self.cap.release()
