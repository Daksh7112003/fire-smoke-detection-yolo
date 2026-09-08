import os
import time
import threading
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

_last_beep_time = 0.0
_beep_lock = threading.Lock()

def _play_sound_async():
    try:
        import winsound
        # Use MessageBeep or Beep in separate thread
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass

def play_alert_sound(cooldown_sec: float = 3.0):
    """
    Trigger a non-blocking system alert sound with cooldown.
    Never blocks the caller or Qt GUI thread.
    """
    global _last_beep_time
    now = time.perf_counter()
    with _beep_lock:
        if now - _last_beep_time < cooldown_sec:
            return
        _last_beep_time = now

    threading.Thread(target=_play_sound_async, daemon=True).start()
