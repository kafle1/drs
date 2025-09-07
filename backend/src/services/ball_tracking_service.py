import cv2
import numpy as np
from typing import List, Dict, Any
import os

class BallTrackingService:
    def __init__(self):
        self.min_radius = 5
        self.max_radius = 20

    def track_ball(self, video_path: str) -> Dict[str, Any]:
        """
        Track ball in video and return trajectory data
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        points = []
        timestamps = []
        ball_detected = False
        confidence_scores = []

        prev_frame = None

        for frame_num in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = frame_num / fps

            # Simple ball detection using color and motion
            ball_pos = self._detect_ball(frame, prev_frame)
            if ball_pos:
                points.append({
                    "x": float(ball_pos[0]),
                    "y": float(ball_pos[1]),
                    "z": 0.0,  # 2D for now
                    "t": timestamp
                })
                timestamps.append(timestamp)
                confidence_scores.append(0.8)  # Placeholder confidence
                ball_detected = True

            prev_frame = frame.copy()

        cap.release()

        if not ball_detected:
            return {
                "points": [],
                "timestamps": [],
                "confidence_score": 0.0,
                "ball_detected": False
            }

        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0

        return {
            "points": points,
            "timestamps": timestamps,
            "confidence_score": float(avg_confidence),
            "ball_detected": ball_detected
        }

    def _detect_ball(self, frame, prev_frame) -> tuple:
        """
        Simple ball detection - in real implementation, use more sophisticated methods
        """
        # Convert to HSV for color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define range for ball color (white/red cricket ball)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])

        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:  # Minimum area
                continue

            # Get bounding circle
            (x, y), radius = cv2.minEnclosingCircle(contour)
            if self.min_radius < radius < self.max_radius:
                return (int(x), int(y))

        return None
