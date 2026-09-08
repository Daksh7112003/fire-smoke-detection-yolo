import os
import time
import cv2
import numpy as np
import torch
from ultralytics import YOLO

class FireSmokeDetector:
    """
    Persistent YOLO Detector for Fire and Smoke Detection.
    Optimized for NVIDIA GPU acceleration (CUDA) and high FPS inference.
    """
    
    COLOR_MAP = {
        "fire": (30, 50, 240),      # Vivid Crimson / Flame Red
        "smoke": (10, 175, 245),    # Bright Amber / Gold
        "default": (0, 220, 120)    # Emerald Green fallback
    }

    def __init__(self, weights_path: str = "weights/fire_smoke_yolov8n.pt", device: str = None):
        self.weights_path = weights_path
        self.model = None
        self.classes = {}
        self.is_loaded = False
        
        # Determine best available compute device
        if device is not None:
            self.device = device
        else:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
            
        self.load_model(weights_path)

    def load_model(self, weights_path: str):
        """Load or switch YOLO weights and move to GPU."""
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights not found at '{weights_path}'")
        
        self.weights_path = weights_path
        self.model = YOLO(weights_path)
        
        # Move model to target device (GPU)
        try:
            self.model.to(self.device)
        except Exception as e:
            print(f"[Warning] Could not move model to {self.device}: {e}, falling back to CPU")
            self.device = "cpu"
            self.model.to("cpu")

        self.classes = self.model.names if hasattr(self.model, "names") else {}
        self.is_loaded = True
        
        # Warmup model on GPU so the first frame doesn't hitch
        try:
            dummy = np.zeros((384, 640, 3), dtype=np.uint8)
            self.model(dummy, device=self.device, verbose=False)
        except Exception:
            pass

    def get_model_info(self) -> dict:
        """Retrieve model metadata and active compute device."""
        if not self.is_loaded or self.model is None:
            return {"status": "Not loaded"}
        
        device_name = self.device
        if "cuda" in self.device and torch.cuda.is_available():
            device_name = f"GPU: {torch.cuda.get_device_name(0)}"
        else:
            device_name = "CPU"

        return {
            "path": os.path.basename(self.weights_path),
            "classes": self.classes,
            "num_classes": len(self.classes),
            "device": device_name,
            "task": getattr(self.model, "task", "detect")
        }

    def predict(self, frame: np.ndarray, conf: float = 0.40, iou: float = 0.45) -> dict:
        """
        Perform inference on a single BGR frame.
        Returns detections list, timing metrics, and counts.
        """
        if not self.is_loaded or self.model is None:
            return {
                "detections": [],
                "fire_count": 0,
                "smoke_count": 0,
                "latency_ms": 0.0,
                "max_conf": 0.0
            }

        start_time = time.perf_counter()
        
        # Run inference on GPU (verbose=False for maximum speed)
        results = self.model(frame, conf=conf, iou=iou, device=self.device, imgsz=640, verbose=False)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        detections = []
        fire_count = 0
        smoke_count = 0
        max_conf = 0.0

        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                xyxy = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                cls_ids = boxes.cls.cpu().numpy()

                for i in range(len(xyxy)):
                    c_conf = float(confs[i])
                    c_id = int(cls_ids[i])
                    c_name = self.classes.get(c_id, f"class_{c_id}").lower()
                    x1, y1, x2, y2 = [int(v) for v in xyxy[i]]

                    if "fire" in c_name:
                        fire_count += 1
                        display_name = "Fire"
                    elif "smoke" in c_name:
                        smoke_count += 1
                        display_name = "Smoke"
                    else:
                        display_name = c_name.capitalize()

                    if c_conf > max_conf:
                        max_conf = c_conf

                    detections.append({
                        "box": [x1, y1, x2, y2],
                        "conf": c_conf,
                        "class_id": c_id,
                        "class_name": display_name,
                        "raw_name": c_name
                    })

        return {
            "detections": detections,
            "fire_count": fire_count,
            "smoke_count": smoke_count,
            "latency_ms": latency_ms,
            "max_conf": max_conf
        }

    def annotate(self, frame: np.ndarray, detections: list, 
                 show_boxes: bool = True, show_labels: bool = True, 
                 show_conf: bool = True) -> np.ndarray:
        """
        Draw professional bounding boxes and labels onto the frame.
        """
        if not show_boxes and not show_labels:
            return frame

        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            conf = det["conf"]
            label_name = det["class_name"]
            raw_name = det["raw_name"]
            
            # Select color based on class
            if "fire" in raw_name:
                color = self.COLOR_MAP["fire"]
                icon = "FIRE"
            elif "smoke" in raw_name:
                color = self.COLOR_MAP["smoke"]
                icon = "SMOKE"
            else:
                color = self.COLOR_MAP["default"]
                icon = label_name.upper()

            # 1. Draw bounding box with rounded corner accents
            if show_boxes:
                # Main bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
                
                # Corner accent lines (tactical/modern HUD style)
                corner_len = min(20, max(5, int((x2 - x1) * 0.15)), max(5, int((y2 - y1) * 0.15)))
                c_thick = 3
                # Top-left
                cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), color, c_thick, cv2.LINE_AA)
                cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), color, c_thick, cv2.LINE_AA)
                # Top-right
                cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), color, c_thick, cv2.LINE_AA)
                cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), color, c_thick, cv2.LINE_AA)
                # Bottom-left
                cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), color, c_thick, cv2.LINE_AA)
                cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), color, c_thick, cv2.LINE_AA)
                # Bottom-right
                cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), color, c_thick, cv2.LINE_AA)
                cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), color, c_thick, cv2.LINE_AA)

            # 2. Draw label pill
            if show_labels:
                text_parts = [icon]
                if show_conf:
                    text_parts.append(f"{conf * 100:.1f}%")
                label_text = "  ".join(text_parts)

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.55
                thickness = 1
                (t_w, t_h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
                
                # Badge coordinates above the box or inside if too close to top
                badge_y1 = max(0, y1 - t_h - 10)
                badge_y2 = badge_y1 + t_h + 10
                badge_x1 = x1
                badge_x2 = x1 + t_w + 16

                # Fill badge background
                cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), color, -1)
                
                # Text in white or dark depending on background
                text_color = (255, 255, 255)
                cv2.putText(annotated, label_text, (badge_x1 + 8, badge_y2 - 6),
                            font, font_scale, text_color, thickness, cv2.LINE_AA)

        return annotated
