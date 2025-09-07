import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import os
import time

class BallTrackingService:
    def __init__(self):
        self.min_radius = 5
        self.max_radius = 20

    def track_ball(self, video_path: str) -> Dict[str, Any]:
        """
        Track ball in video and return trajectory data
        """
        start_time = time.time()

        if not os.path.exists(video_path):
            return {
                "error": "Video file does not exist",
                "points": [],
                "timestamps": [],
                "confidence_score": 0.0,
                "ball_detected": False,
                "processing_time": time.time() - start_time
            }

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {
                "error": "Could not open video file",
                "points": [],
                "timestamps": [],
                "confidence_score": 0.0,
                "ball_detected": False,
                "processing_time": time.time() - start_time
            }

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if frame_count == 0:
            cap.release()
            return {
                "error": "Video has no frames",
                "points": [],
                "timestamps": [],
                "confidence_score": 0.0,
                "ball_detected": False,
                "processing_time": time.time() - start_time
            }

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

            # Detect ball in current frame
            ball_pos = self._detect_ball_in_frame(frame)
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

        processing_time = time.time() - start_time

        if not ball_detected:
            return {
                "points": [],
                "timestamps": [],
                "confidence_score": 0.0,
                "ball_detected": False,
                "processing_time": processing_time
            }

        # Filter and validate trajectory points
        filtered_points = self._filter_trajectory_points(points)
        confidence_score = self._calculate_trajectory_confidence(filtered_points)

        return {
            "points": filtered_points,
            "timestamps": timestamps,
            "confidence_score": float(confidence_score),
            "ball_detected": ball_detected,
            "processing_time": processing_time
        }

    def _detect_ball_in_frame(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect ball in a single frame using Hough circle transform
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Detect circles using Hough transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=self.min_radius,
            maxRadius=self.max_radius
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # Return the first detected circle (could be improved with scoring)
            for (x, y, r) in circles:
                return (x, y)

        return None

    def _calculate_trajectory_confidence(self, points: List[Dict]) -> float:
        """
        Calculate confidence score for trajectory based on point consistency
        """
        if len(points) < 2:
            return 0.0

        # Calculate velocity consistency
        velocities = []
        for i in range(1, len(points)):
            dx = points[i]["x"] - points[i-1]["x"]
            dy = points[i]["y"] - points[i-1]["y"]
            dt = points[i]["t"] - points[i-1]["t"]
            if dt > 0:
                velocity = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(velocity)

        if not velocities:
            return 0.0

        # Calculate velocity variance (lower variance = higher confidence)
        velocity_mean = np.mean(velocities)
        velocity_std = np.std(velocities)

        if velocity_mean == 0:
            return 0.0

        # Normalize confidence between 0 and 1
        cv = velocity_std / velocity_mean  # Coefficient of variation

        # For noisy data with large jumps, CV will be high, resulting in low confidence
        # Scale the confidence calculation to be more sensitive to noise
        confidence = max(0, 1 - cv * 3)  # Increased multiplier to 3 for more sensitivity

        return min(confidence, 1.0)

    def _filter_trajectory_points(self, points: List[Dict]) -> List[Dict]:
        """
        Filter trajectory points to remove noise and duplicates
        """
        if len(points) < 2:
            return points

        filtered = [points[0]]  # Always keep first point

        for point in points[1:]:
            # Check if point is significantly different from last kept point
            last_point = filtered[-1]
            distance = np.sqrt(
                (point["x"] - last_point["x"])**2 +
                (point["y"] - last_point["y"])**2
            )

            # Only keep if distance is significant (not a duplicate)
            if distance > 2.0:  # Minimum movement threshold
                filtered.append(point)

        return filtered

    def _estimate_ball_position(self, points: List[Dict], target_time: float) -> Optional[Dict]:
        """
        Estimate ball position at a specific time using interpolation/extrapolation
        """
        if len(points) < 2:
            return None

        # Find points before and after target time
        before_point = None
        after_point = None

        for i, point in enumerate(points):
            if point["t"] <= target_time:
                before_point = point
            if point["t"] > target_time:
                after_point = point
                break

        if before_point and after_point:
            # Interpolate between two points
            t1, t2 = before_point["t"], after_point["t"]
            x1, y1 = before_point["x"], before_point["y"]
            x2, y2 = after_point["x"], after_point["y"]

            ratio = (target_time - t1) / (t2 - t1)
            x = x1 + (x2 - x1) * ratio
            y = y1 + (y2 - y1) * ratio

            return {"x": x, "y": y, "t": target_time}

        elif before_point:
            # Extrapolate beyond last point (simple linear extrapolation)
            if len(points) >= 2:
                # Use last two points to estimate velocity
                p1 = points[-2]
                p2 = points[-1]
                dt = p2["t"] - p1["t"]
                if dt > 0:
                    vx = (p2["x"] - p1["x"]) / dt
                    vy = (p2["y"] - p1["y"]) / dt

                    time_diff = target_time - p2["t"]
                    x = p2["x"] + vx * time_diff
                    y = p2["y"] + vy * time_diff

                    return {"x": x, "y": y, "t": target_time}

        elif after_point:
            # Extrapolate before first point (backward extrapolation)
            if len(points) >= 2:
                p1 = points[0]
                p2 = points[1]
                dt = p2["t"] - p1["t"]
                if dt > 0:
                    vx = (p2["x"] - p1["x"]) / dt
                    vy = (p2["y"] - p1["y"]) / dt

                    time_diff = target_time - p1["t"]
                    x = p1["x"] + vx * time_diff
                    y = p1["y"] + vy * time_diff

                    return {"x": x, "y": y, "t": target_time}

        return None

    def _validate_trajectory_data(self, points: List[Dict]) -> bool:
        """
        Validate trajectory data for consistency and plausibility
        """
        if not points:
            return False

        # Check for required fields
        required_fields = ["x", "y", "t"]
        for point in points:
            if not all(field in point for field in required_fields):
                return False

            # Check data types
            if not isinstance(point["x"], (int, float)) or not isinstance(point["y"], (int, float)):
                return False

        # Check for reasonable coordinate ranges
        for point in points:
            if not (-1000 <= point["x"] <= 10000 and -1000 <= point["y"] <= 10000):
                return False

        # Check for chronological order
        for i in range(1, len(points)):
            if points[i]["t"] <= points[i-1]["t"]:
                return False

        return True

    def _calculate_velocities(self, points: List[Dict]) -> List[float]:
        """
        Calculate velocities between consecutive points
        """
        if len(points) < 2:
            return []

        velocities = []
        for i in range(1, len(points)):
            dx = points[i]["x"] - points[i-1]["x"]
            dy = points[i]["y"] - points[i-1]["y"]
            dt = points[i]["t"] - points[i-1]["t"]
            if dt > 0:
                velocity = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(velocity)

        return velocities

    def _calculate_accelerations(self, points: List[Dict]) -> List[float]:
        """
        Calculate accelerations between consecutive velocity changes
        """
        velocities = self._calculate_velocities(points)
        if len(velocities) < 2:
            return []

        accelerations = []
        dt = points[1]["t"] - points[0]["t"]  # Assume constant time steps

        for i in range(1, len(velocities)):
            dv = velocities[i] - velocities[i-1]
            if dt > 0:
                acceleration = dv / dt
                accelerations.append(acceleration)

        return accelerations

    def _calculate_trajectory_length(self, points: List[Dict]) -> float:
        """
        Calculate total length of trajectory
        """
        if len(points) < 2:
            return 0.0

        total_length = 0.0
        for i in range(1, len(points)):
            dx = points[i]["x"] - points[i-1]["x"]
            dy = points[i]["y"] - points[i-1]["y"]
            distance = np.sqrt(dx**2 + dy**2)
            total_length += distance

        return total_length

    def _calculate_trajectory_smoothness(self, points: List[Dict]) -> float:
        """
        Calculate trajectory smoothness based on acceleration variance
        """
        accelerations = self._calculate_accelerations(points)
        if not accelerations:
            return 1.0  # Perfect smoothness if no acceleration data

        # If all accelerations are the same (constant velocity), it's smooth
        if len(set(round(a, 6) for a in accelerations)) == 1:
            return 1.0

        # Lower variance = smoother trajectory
        acc_mean = np.mean(accelerations)
        acc_std = np.std(accelerations)

        if acc_std == 0:
            return 1.0

        # Normalize smoothness score (0-1, higher is smoother)
        cv = acc_std / abs(acc_mean) if acc_mean != 0 else acc_std
        smoothness = max(0, 1 - cv)

        return smoothness

    def _calculate_parabolic_trajectory_fit(self, points: List[Dict]) -> float:
        """
        Fit trajectory to parabolic curve and return fit quality (R²)
        """
        if len(points) < 3:
            return 0.0

        # Extract coordinates
        x_coords = np.array([p["x"] for p in points])
        y_coords = np.array([p["y"] for p in points])

        # Fit quadratic polynomial: y = ax² + bx + c
        try:
            coeffs = np.polyfit(x_coords, y_coords, 2)
            y_predicted = np.polyval(coeffs, x_coords)

            # Calculate R²
            ss_res = np.sum((y_coords - y_predicted) ** 2)
            ss_tot = np.sum((y_coords - np.mean(y_coords)) ** 2)

            if ss_tot == 0:
                return 1.0

            r_squared = 1 - (ss_res / ss_tot)
            return max(0, min(1, r_squared))  # Clamp to [0, 1]

        except:
            return 0.0

    def _detect_trajectory_anomalies(self, points: List[Dict]) -> List[int]:
        """
        Detect anomalous points in trajectory using statistical methods
        """
        if len(points) < 3:
            return []

        anomalies = []
        velocities = self._calculate_velocities(points)

        if not velocities:
            return []

        # Use median-based detection for robustness against outliers
        vel_median = np.median(velocities)

        # Detect points with velocity significantly higher than median
        threshold = vel_median * 2  # 2x median velocity

        for i, velocity in enumerate(velocities):
            if velocity > threshold:
                anomalies.append(i + 1)  # +1 because velocities are between points

        return anomalies

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
