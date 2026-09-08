import os
import cv2
import numpy as np

def create_sample_fire_smoke_video(output_path="sample_videos/test_fire_smoke.mp4", duration_sec=5, fps=25):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 640, 480
    total_frames = duration_sec * fps
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    np.random.seed(42)
    
    for i in range(total_frames):
        # Dark industrial/room background
        frame = np.full((height, width, 3), 20, dtype=np.uint8)
        
        # Subtle room floor and wall
        cv2.rectangle(frame, (0, int(height*0.7)), (width, height), (35, 30, 25), -1)
        cv2.line(frame, (0, int(height*0.7)), (width, int(height*0.7)), (50, 45, 40), 2)
        
        # Simulated animated fire plume
        fire_center_x = int(width * 0.35 + 10 * np.sin(i * 0.2))
        fire_base_y = int(height * 0.72)
        
        # Flame glow gradient
        for r in range(70, 10, -10):
            alpha = (80 - r) / 80.0
            color = (0, int(120 * alpha), int(255 * alpha)) # BGR: orange-yellow to red
            cv2.circle(frame, (fire_center_x, fire_base_y - int(r*0.6)), r, color, -1)
            
        # Flame flickering cores
        flame_h = int(60 + 25 * np.sin(i * 0.4) + 15 * np.random.rand())
        pts = np.array([
            [fire_center_x - 30, fire_base_y],
            [fire_center_x + 30, fire_base_y],
            [fire_center_x + 10, fire_base_y - flame_h],
            [fire_center_x - 5, fire_base_y - int(flame_h * 1.2)],
            [fire_center_x - 15, fire_base_y - int(flame_h * 0.8)]
        ], np.int32)
        cv2.fillPoly(frame, [pts], (20, 160, 255))
        
        # Simulated rising smoke plume
        smoke_center_x = int(fire_center_x + (i % fps) * 2 + 15 * np.sin(i * 0.1))
        smoke_base_y = fire_base_y - flame_h - 20
        
        for s in range(5):
            sx = int(smoke_center_x + np.sin(i * 0.1 + s) * 25)
            sy = int(smoke_base_y - s * 30 - (i % 20))
            if 0 <= sy < height:
                sr = 35 + s * 12
                # Gray translucent smoke puff
                overlay = frame.copy()
                cv2.circle(overlay, (sx, sy), sr, (140, 140, 140), -1)
                cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

        # Add timestamp text in corner
        cv2.putText(frame, f"CAM-01 [TEST STREAM] Frame {i+1}/{total_frames}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1, cv2.LINE_AA)
        
        out.write(frame)
        
    out.release()
    print(f"Sample video created at: {output_path} ({total_frames} frames)")

if __name__ == "__main__":
    create_sample_fire_smoke_video()
