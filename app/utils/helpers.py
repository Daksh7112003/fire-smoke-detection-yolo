import os
import time
import cv2
import numpy as np

def format_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds < 0:
        seconds = 0
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def save_snapshot(frame: np.ndarray, base_dir: str = "snapshots", prefix: str = "detection") -> str:
    """Save an annotated frame as an image file."""
    os.makedirs(base_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.jpg"
    full_path = os.path.join(base_dir, filename)
    cv2.imwrite(full_path, frame)
    return full_path

def play_alert_sound():
    """Trigger a short system alert sound on Windows if available."""
    try:
        import winsound
        winsound.Beep(1000, 180)
    except Exception:
        pass
