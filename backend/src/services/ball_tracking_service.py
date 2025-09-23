import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import os
import time
import logging

logger = logging.getLogger(__name__)

class BallTrackingService:
    def __init__(self):
        # Ball detection parameters
        self.min_ball_radius = 3
        self.max_ball_radius = 15

        # Pitch dimensions in meters
        self.pitch_length = 22.0  # 22 yards
        self.pitch_width = 3.05   # 10 feet

        # Camera calibration (assuming typical smartphone camera)
        self.focal_length_px = 1000  # pixels
        self.camera_height = 1.5     # meters above ground
        self.camera_angle = np.radians(15)  # degrees from horizontal

        # Color ranges for detection
        self.ball_color_ranges = {
            'white': ([0, 0, 200], [180, 30, 255]),
            'red': ([0, 50, 50], [10, 255, 255]),
            'orange': ([5, 50, 50], [15, 255, 255])
        }

        # Pitch color range (green grass)
        self.pitch_color_range = ([35, 50, 50], [80, 255, 255])

        # Stump detection parameters
        self.stump_min_area = 50  # Reduced from 100
        self.stump_max_area = 5000  # Increased from 2000

    def track_ball(self, video_path: str) -> Dict[str, Any]:
        """
        Comprehensive ball tracking with pitch analysis, LBW detection, and 3D reconstruction
        """
        start_time = time.time()
        logger.info(f"Starting comprehensive ball tracking for: {video_path}")
        logger.debug(f"Video path exists: {os.path.exists(video_path)}")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(f"Video specs: {fps} FPS, {frame_count} frames, {width}x{height}")
        logger.debug(f"Video codec: {cap.get(cv2.CAP_PROP_FOURCC)}, duration: {frame_count/fps:.2f}s")

        # Initialize tracking data
        tracking_data = {
            'ball_trajectory': [],
            'stumps_position': None,
            'pitch_boundaries': None,
            'bowler_position': None,
            'batter_position': None,
            'lbw_analysis': [],
            'timestamps': [],
            'frame_data': [],
            'last_ball_position': None,  # Track last known ball position for continuity
            'ball_velocity': None  # Track ball velocity for prediction
        }

        # First pass: Analyze pitch and find static elements
        logger.info("First pass: Analyzing pitch and static elements...")
        pitch_info = self._analyze_pitch_and_static_elements(cap, width, height)

        # Store static elements in tracking data
        if pitch_info and pitch_info.get('stumps'):
            tracking_data['stumps_position'] = pitch_info['stumps']
            logger.info(f"Stumps detected at position: {pitch_info['stumps']['position_3d']}")

        # Reset video to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # Second pass: Track dynamic elements
        logger.info("Second pass: Tracking dynamic elements...")
        frame_idx = 0
        prev_frame = None

        while frame_idx < min(frame_count, 300):  # Limit to first 10 seconds for testing
            ret, frame = cap.read()
            if not ret:
                break

            current_time = frame_idx / fps
            logger.debug(f"Processing frame {frame_idx} at {current_time:.2f}s")

            # Process frame
            frame_data = self._process_frame(frame, prev_frame, pitch_info, current_time, frame_idx, tracking_data)

            # Store frame data
            tracking_data['frame_data'].append(frame_data)
            tracking_data['timestamps'].append(current_time)

            # Update trajectory if ball detected with high confidence
            if frame_data['ball_position'] is not None and frame_data['ball_position']['confidence'] > 0.3:
                ball_pos = frame_data['ball_position']

                # Check temporal consistency - ball shouldn't jump too far
                if tracking_data['last_ball_position'] is not None:
                    last_pos = tracking_data['last_ball_position']
                    distance = np.sqrt((ball_pos['x'] - last_pos['x'])**2 + (ball_pos['y'] - last_pos['y'])**2)

                    # If ball moved too far (more than 100 pixels), it might be a false positive
                    if distance > 100:
                        logger.debug(f"Ball position jump too large ({distance:.1f}px), skipping frame {frame_idx}")
                    else:
                        tracking_data['ball_trajectory'].append({
                            'x': ball_pos['x'],
                            'y': ball_pos['y'],
                            'z': ball_pos['z'],
                            't': current_time,
                            'confidence': ball_pos['confidence']
                        })
                        tracking_data['last_ball_position'] = ball_pos
                        logger.debug(f"Added ball position to trajectory: ({ball_pos['x']:.2f}, {ball_pos['y']:.2f}, {ball_pos['z']:.2f}) at t={current_time:.2f}")
                else:
                    # First detection
                    tracking_data['ball_trajectory'].append({
                        'x': ball_pos['x'],
                        'y': ball_pos['y'],
                        'z': ball_pos['z'],
                        't': current_time,
                        'confidence': ball_pos['confidence']
                    })
                    tracking_data['last_ball_position'] = ball_pos
                    logger.debug(f"Added first ball position to trajectory: ({ball_pos['x']:.2f}, {ball_pos['y']:.2f}, {ball_pos['z']:.2f}) at t={current_time:.2f}")
            elif frame_data['ball_position'] is None and len(tracking_data['ball_trajectory']) > 0:
                # No detection but we have previous trajectory - try to predict
                predicted_pos = self._predict_ball_position(tracking_data, current_time)
                if predicted_pos:
                    tracking_data['ball_trajectory'].append(predicted_pos)
                    tracking_data['last_ball_position'] = predicted_pos
                    logger.debug(f"Added predicted ball position: ({predicted_pos['x']:.2f}, {predicted_pos['y']:.2f}, {predicted_pos['z']:.2f}) at t={current_time:.2f}")

            # Update positions
            if frame_data['bowler_position']:
                tracking_data['bowler_position'] = frame_data['bowler_position']
                logger.debug(f"Updated bowler position: ({frame_data['bowler_position']['x']:.2f}, {frame_data['bowler_position']['y']:.2f})")
            if frame_data['batter_position']:
                tracking_data['batter_position'] = frame_data['batter_position']
                logger.debug(f"Updated batter position: ({frame_data['batter_position']['x']:.2f}, {frame_data['batter_position']['y']:.2f})")

            prev_frame = frame.copy()
            frame_idx += 1

            if frame_idx % 30 == 0:  # Log every second
                ball_count = len(tracking_data['ball_trajectory'])
                logger.info(f"Processed {frame_idx}/{frame_count} frames ({frame_idx/frame_count*100:.1f}%). Ball detections: {ball_count}")

        cap.release()

        # Post-processing
        logger.info("Post-processing trajectory data...")
        tracking_data = self._post_process_tracking_data(tracking_data)

        # LBW Analysis
        logger.info("Performing LBW analysis...")
        tracking_data['lbw_analysis'] = self._analyze_lbw_decisions(tracking_data)

        processing_time = time.time() - start_time
        logger.info(f"Ball tracking completed in {processing_time:.2f}s. Detected {len(tracking_data['ball_trajectory'])} ball positions.")

        result = {
            "points": tracking_data['ball_trajectory'],
            "timestamps": tracking_data['timestamps'],
            "confidence_score": self._calculate_trajectory_confidence(tracking_data['ball_trajectory']),
            "ball_detected": len(tracking_data['ball_trajectory']) > 0,
            "processing_time": processing_time,
            "video_info": {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height
            },
            "pitch_info": pitch_info,
            "stumps_position": tracking_data['stumps_position'],
            "bowler_position": tracking_data['bowler_position'],
            "batter_position": tracking_data['batter_position'],
            "lbw_analysis": tracking_data['lbw_analysis'],
            "debug_info": {
                "frames_processed": len(tracking_data['frame_data']),
                "ball_detections": len(tracking_data['ball_trajectory']),
                "pitch_detected": pitch_info is not None
            }
        }

        # Convert numpy types to JSON-serializable Python types
        result = self._convert_numpy_types(result)

        return result

    def _analyze_pitch_and_static_elements(self, cap, width, height):
        """Analyze the pitch and find static elements like stumps"""
        logger.info("Analyzing pitch and static elements...")

        # Sample frames from different parts of the video
        sample_frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Get frames from beginning, middle, and end
        for frame_pos in [0, total_frames//2, total_frames-1]:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if ret:
                sample_frames.append(frame)

        if not sample_frames:
            logger.warning("Could not sample frames for pitch analysis")
            return None

        # Analyze pitch boundaries
        pitch_boundaries = self._detect_pitch_boundaries(sample_frames[0])

        # Find stumps (usually static)
        stumps_position = self._detect_stumps(sample_frames[0])

        pitch_info = {
            'boundaries': pitch_boundaries,
            'stumps': stumps_position,
            'dimensions': {
                'width': width,
                'height': height,
                'pitch_length_m': self.pitch_length,
                'pitch_width_m': self.pitch_width
            },
            'camera_calibration': {
                'focal_length_px': self.focal_length_px,
                'height_m': self.camera_height,
                'angle_rad': self.camera_angle
            }
        }

        logger.info(f"Pitch analysis complete. Stumps: {stumps_position is not None}, Boundaries: {pitch_boundaries is not None}")
        return pitch_info

    def _detect_pitch_boundaries(self, frame):
        """Detect the cricket pitch boundaries using color segmentation"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Create mask for green pitch
            lower_green = np.array(self.pitch_color_range[0])
            upper_green = np.array(self.pitch_color_range[1])
            pitch_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Clean up mask
            kernel = np.ones((5, 5), np.uint8)
            pitch_mask = cv2.morphologyEx(pitch_mask, cv2.MORPH_CLOSE, kernel)
            pitch_mask = cv2.morphologyEx(pitch_mask, cv2.MORPH_OPEN, kernel)

            # Find contours
            contours, _ = cv2.findContours(pitch_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Find largest contour (should be the pitch)
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                if area > 10000:  # Minimum pitch area
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    return {
                        'bbox': (x, y, w, h),
                        'contour': largest_contour.tolist(),
                        'area': area
                    }

        except Exception as e:
            logger.error(f"Error detecting pitch boundaries: {e}")

        return None

    def _detect_stumps(self, frame):
        """Detect cricket stumps using shape and color analysis"""
        try:
            # Convert to grayscale and apply edge detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            logger.debug(f"Found {len(contours)} contours for stump detection")

            potential_stumps = []

            for contour in contours:
                area = cv2.contourArea(contour)
                if self.stump_min_area < area < self.stump_max_area:
                    # Check if it's roughly rectangular (stumps)
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]

                    # Stumps should be tall and narrow
                    aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
                    logger.debug(f"Contour area: {area}, aspect ratio: {aspect_ratio:.2f}")
                    if 2 < aspect_ratio < 8:  # Stumps are much taller than wide
                        potential_stumps.append({
                            'contour': contour,
                            'bbox': cv2.boundingRect(contour),
                            'area': area,
                            'aspect_ratio': aspect_ratio
                        })

            logger.debug(f"Found {len(potential_stumps)} potential stumps")

            if potential_stumps:
                # Find the best stump candidate (usually the tallest)
                best_stump = max(potential_stumps, key=lambda x: x['aspect_ratio'])
                x, y, w, h = best_stump['bbox']

                # Convert to 3D coordinates (stumps are at the wicket)
                stumps_3d = self._pixel_to_3d(x + w/2, y + h, frame.shape[1], frame.shape[0])

                return {
                    'pixel_position': (x + w/2, y + h),
                    'size': (w, h),
                    'position_3d': stumps_3d,
                    'confidence': 0.8
                }

        except Exception as e:
            logger.error(f"Error detecting stumps: {e}")

        return None

    def _process_frame(self, frame, prev_frame, pitch_info, current_time, frame_idx, tracking_data=None):
        """Process a single frame for object detection"""
        frame_data = {
            'frame_idx': frame_idx,
            'timestamp': current_time,
            'ball_position': None,
            'bowler_position': None,
            'batter_position': None,
            'stumps_visible': False
        }

        # Detect ball
        ball_pos = self._detect_ball_comprehensive(frame, prev_frame)
        if ball_pos:
            # Convert to 3D coordinates
            ball_3d = self._pixel_to_3d(ball_pos['x'], ball_pos['y'], frame.shape[1], frame.shape[0])
            frame_data['ball_position'] = {
                'x': ball_3d[0],
                'y': ball_3d[1],
                'z': ball_3d[2],
                'confidence': ball_pos['confidence']
            }

        # Detect bowler (usually moving towards the batsman)
        bowler_pos = self._detect_bowler(frame, prev_frame)
        if bowler_pos:
            bowler_3d = self._pixel_to_3d(bowler_pos['x'], bowler_pos['y'], frame.shape[1], frame.shape[0])
            frame_data['bowler_position'] = {
                'x': bowler_3d[0],
                'y': bowler_3d[1],
                'z': bowler_3d[2],
                'confidence': bowler_pos['confidence']
            }

        # Detect batter (usually near the wicket)
        batter_pos = self._detect_batter(frame)
        if batter_pos:
            batter_3d = self._pixel_to_3d(batter_pos['x'], batter_pos['y'], frame.shape[1], frame.shape[0])
            frame_data['batter_position'] = {
                'x': batter_3d[0],
                'y': batter_3d[1],
                'z': batter_3d[2],
                'confidence': batter_pos['confidence']
            }

        return frame_data

    def _detect_ball_comprehensive(self, frame, prev_frame=None):
        """Comprehensive ball detection using multiple methods"""
        detections = []
        logger.debug("Starting comprehensive ball detection")

        # Method 1: Color-based detection
        color_detection = self._detect_ball_by_color_advanced(frame)
        if color_detection:
            detections.append(color_detection)
            logger.debug(f"Color detection found ball at ({color_detection['x']}, {color_detection['y']}) with confidence {color_detection['confidence']:.2f}")

        # Method 2: Motion detection
        if prev_frame is not None:
            motion_detection = self._detect_ball_by_motion_advanced(frame, prev_frame)
            if motion_detection:
                detections.append(motion_detection)
                logger.debug(f"Motion detection found ball at ({motion_detection['x']}, {motion_detection['y']}) with confidence {motion_detection['confidence']:.2f}")

        # Method 3: Shape-based detection (Hough circles as fallback)
        shape_detection = self._detect_ball_by_shape(frame)
        if shape_detection:
            detections.append(shape_detection)
            logger.debug(f"Shape detection found ball at ({shape_detection['x']}, {shape_detection['y']}) with confidence {shape_detection['confidence']:.2f}")

        # Choose best detection with higher confidence threshold
        if detections:
            # Filter out low confidence detections
            valid_detections = [d for d in detections if d['confidence'] > 0.2]

            if valid_detections:
                # Sort by confidence and return the best
                best_detection = max(valid_detections, key=lambda x: x['confidence'])

                # Additional validation: check if detection is in reasonable area
                if self._is_valid_ball_position(best_detection, frame.shape):
                    logger.debug(f"Selected best detection: {best_detection['method']} method with confidence {best_detection['confidence']:.2f}")
                    return best_detection
                else:
                    logger.debug(f"Rejected detection at ({best_detection['x']}, {best_detection['y']}) - invalid position")

        logger.debug("No valid ball detections found")
        return None

    def _is_valid_ball_position(self, detection, frame_shape):
        """Check if ball position is in a valid location on the frame"""
        height, width = frame_shape[:2]
        x, y = detection['x'], detection['y']

        # Ball should be within frame bounds with margin
        margin = 20
        if x < margin or x > width - margin or y < margin or y > height - margin:
            return False

        # Ball should not be in the very top of frame (usually sky/UI)
        if y < height * 0.1:
            return False

        # Ball should not be in the very bottom of frame (usually ground/grass close to camera)
        if y > height * 0.9:
            return False

        return True

    def _detect_ball_by_color_advanced(self, frame):
        """Advanced color-based ball detection"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Try different ball colors
            for color_name, (lower, upper) in self.ball_color_ranges.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))

                # Clean up mask
                kernel = np.ones((3, 3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 20 < area < 1000:  # Reasonable ball size
                        # Check circularity
                        perimeter = cv2.arcLength(contour, True)
                        if perimeter > 0:
                            circularity = 4 * np.pi * area / (perimeter * perimeter)
                            if circularity > 0.6:  # Reasonably circular
                                # Get center
                                M = cv2.moments(contour)
                                if M["m00"] != 0:
                                    cx = int(M["m10"] / M["m00"])
                                    cy = int(M["m01"] / M["m00"])

                                    return {
                                        'x': cx,
                                        'y': cy,
                                        'confidence': circularity * 0.8,  # Color detection confidence
                                        'method': 'color',
                                        'color': color_name
                                    }

        except Exception as e:
            logger.error(f"Error in color-based ball detection: {e}")

        return None

    def _detect_ball_by_motion_advanced(self, frame, prev_frame):
        """Advanced motion-based ball detection"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur
            gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
            gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

            # Compute frame difference
            frame_diff = cv2.absdiff(gray1, gray2)
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]

            # Dilate to fill holes
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.dilate(thresh, kernel, iterations=2)

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 2000:  # Reasonable motion area for ball
                    # Check aspect ratio
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h

                    if 0.5 < aspect_ratio < 2.0:  # Roughly square
                        # Get center
                        cx = x + w // 2
                        cy = y + h // 2

                        # Calculate motion confidence based on size and shape
                        size_confidence = max(0.0, 1.0 - abs(area - 200) / 400)  # Optimal around 200 pixels, clamped to [0,1]
                        shape_confidence = max(0.0, 1.0 - abs(aspect_ratio - 1.0) * 0.5)  # Clamped to [0,1]

                        confidence = max(0.0, (size_confidence + shape_confidence) / 2 * 0.7)  # Motion detection confidence, clamped to [0,1]

                        return {
                            'x': cx,
                            'y': cy,
                            'confidence': confidence,
                            'method': 'motion',
                            'area': area,
                            'aspect_ratio': aspect_ratio
                        }

        except Exception as e:
            logger.error(f"Error in motion-based ball detection: {e}")

        return None

    def _detect_ball_by_shape(self, frame):
        """Shape-based ball detection using Hough circles"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)

            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=30,
                param1=50,
                param2=25,
                minRadius=self.min_ball_radius,
                maxRadius=self.max_ball_radius
            )

            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")

                # Return the best circle (largest radius, reasonable position)
                best_circle = max(circles, key=lambda c: c[2])
                x, y, r = best_circle

                return {
                    'x': x,
                    'y': y,
                    'confidence': 0.5,  # Lower confidence for shape detection
                    'method': 'shape',
                    'radius': r
                }

        except Exception as e:
            logger.error(f"Error in shape-based ball detection: {e}")

        return None

    def _detect_bowler(self, frame, prev_frame=None):
        """Detect bowler position using motion and pose estimation"""
        # Simplified bowler detection - look for movement in bowling area
        try:
            if prev_frame is None:
                return None

            # Focus on the right side of the frame (bowler's approach)
            height, width = frame.shape[:2]
            roi = frame[:, width//2:]  # Right half

            # Simple motion detection in ROI
            gray1 = cv2.cvtColor(prev_frame[:, width//2:], cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            frame_diff = cv2.absdiff(gray1, gray2)
            thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)[1]

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Find largest moving object in bowling area
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                if 1000 < area < 15000:  # Reasonable human size
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"]) + width//2  # Adjust for ROI offset
                        cy = int(M["m01"] / M["m00"])

                        return {
                            'x': cx,
                            'y': cy,
                            'confidence': 0.6,
                            'area': area
                        }

        except Exception as e:
            logger.error(f"Error detecting bowler: {e}")

        return None

    def _detect_batter(self, frame):
        """Detect batter position near the wicket area"""
        try:
            height, width = frame.shape[:2]

            # Focus on area near stumps (left side for right-handed batsman)
            roi = frame[:, :width//2]

            # Look for vertical edges (batsman silhouette)
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            potential_batters = []

            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 8000:  # Reasonable human size
                    x, y, w, h = cv2.boundingRect(contour)

                    # Check if tall and relatively narrow (human shape)
                    aspect_ratio = h / w
                    if 1.2 < aspect_ratio < 4.0:
                        potential_batters.append({
                            'contour': contour,
                            'bbox': (x, y, w, h),
                            'area': area,
                            'aspect_ratio': aspect_ratio
                        })

            if potential_batters:
                # Choose the one closest to the wicket area (left side)
                best_batter = min(potential_batters, key=lambda b: b['bbox'][0])  # Leftmost
                x, y, w, h = best_batter['bbox']

                return {
                    'x': x + w//2,  # No ROI offset since we're using left half
                    'y': y + h//2,
                    'confidence': 0.7,
                    'area': best_batter['area']
                }

        except Exception as e:
            logger.error(f"Error detecting batter: {e}")

        return None

    def _pixel_to_3d(self, x_pixel, y_pixel, frame_width, frame_height):
        """Convert 2D pixel coordinates to 3D world coordinates"""
        try:
            # Normalize pixel coordinates (-1 to 1)
            x_norm = (x_pixel - frame_width/2) / (frame_width/2)
            y_norm = (y_pixel - frame_height/2) / (frame_height/2)

            # Simple perspective projection (simplified camera model)
            # This is a basic approximation - real 3D reconstruction would need proper camera calibration

            # Assume camera is looking down at the pitch with some angle
            pitch_x = x_norm * (self.pitch_width / 2)  # Scale to pitch width
            pitch_y = (1 - y_norm) * (self.pitch_length / 2)  # Scale to pitch length

            # Estimate height based on position (balls closer to camera appear higher)
            # This is a very simplified model
            distance_factor = 1 - abs(y_norm)  # Closer to bottom of frame = closer to camera
            pitch_z = distance_factor * 2  # Height in meters

            return (pitch_x, pitch_y, pitch_z)

        except Exception as e:
            logger.error(f"Error in pixel to 3D conversion: {e}")
            return (0, 0, 0)

    def _post_process_tracking_data(self, tracking_data):
        """Post-process tracking data for smoothing and validation"""
        try:
            if not tracking_data['ball_trajectory']:
                return tracking_data

            # Sort by time
            tracking_data['ball_trajectory'].sort(key=lambda p: p['t'])

            # Apply Kalman filtering for smoothing
            smoothed_trajectory = self._apply_kalman_filter(tracking_data['ball_trajectory'])

            # Remove outliers
            filtered_trajectory = self._remove_outliers(smoothed_trajectory)

            tracking_data['ball_trajectory'] = filtered_trajectory

            logger.info(f"Post-processing: {len(smoothed_trajectory)} -> {len(filtered_trajectory)} points")

        except Exception as e:
            logger.error(f"Error in post-processing: {e}")

        return tracking_data

    def _apply_kalman_filter(self, trajectory):
        """Apply Kalman filter to smooth trajectory"""
        if len(trajectory) < 2:
            return trajectory

        # Initialize Kalman filter
        kalman = cv2.KalmanFilter(6, 3)  # 6 state (x,y,z,vx,vy,vz), 3 measurements (x,y,z)

        # State: [x, y, z, vx, vy, vz]
        kalman.transitionMatrix = np.eye(6, dtype=np.float32)
        kalman.measurementMatrix = np.array([[1,0,0,0,0,0], [0,1,0,0,0,0], [0,0,1,0,0,0]], np.float32)

        # Process noise and measurement noise
        kalman.processNoiseCov = np.eye(6, dtype=np.float32) * 0.01
        kalman.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.1

        smoothed_points = []

        for point in trajectory:
            measurement = np.array([[point['x']], [point['y']], [point['z']]], np.float32)

            # Predict and correct
            prediction = kalman.predict()
            corrected = kalman.correct(measurement)

            smoothed_point = {
                'x': corrected[0][0],
                'y': corrected[1][0],
                'z': corrected[2][0],
                't': point['t'],
                'confidence': point['confidence']
            }
            smoothed_points.append(smoothed_point)

        return smoothed_points

    def _remove_outliers(self, trajectory):
        """Remove outlier points using statistical methods"""
        if len(trajectory) < 3:
            return trajectory

        # Calculate velocities
        velocities = []
        for i in range(1, len(trajectory)):
            dx = trajectory[i]['x'] - trajectory[i-1]['x']
            dy = trajectory[i]['y'] - trajectory[i-1]['y']
            dt = trajectory[i]['t'] - trajectory[i-1]['t']
            if dt > 0:
                speed = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(speed)

        if not velocities:
            return trajectory

        # Remove points with unrealistic speeds
        mean_speed = np.mean(velocities)
        std_speed = np.std(velocities)
        speed_threshold = mean_speed + 3 * std_speed

        filtered_trajectory = [trajectory[0]]  # Keep first point

        for i in range(1, len(trajectory)):
            if i-1 < len(velocities):
                speed = velocities[i-1]
                if speed < speed_threshold:
                    filtered_trajectory.append(trajectory[i])

        return filtered_trajectory

    def _predict_ball_position(self, tracking_data, current_time):
        """Predict ball position based on recent trajectory"""
        trajectory = tracking_data['ball_trajectory']
        if len(trajectory) < 2:
            return None

        # Get last two points
        last_point = trajectory[-1]
        second_last = trajectory[-2]

        # Calculate velocity
        dt = last_point['t'] - second_last['t']
        if dt <= 0:
            return None

        vx = (last_point['x'] - second_last['x']) / dt
        vy = (last_point['y'] - second_last['y']) / dt
        vz = (last_point['z'] - second_last['z']) / dt

        # Predict next position
        time_diff = current_time - last_point['t']
        predicted_x = last_point['x'] + vx * time_diff
        predicted_y = last_point['y'] + vy * time_diff
        predicted_z = last_point['z'] + vz * time_diff

        # Reduce confidence for predictions
        predicted_confidence = last_point['confidence'] * 0.7

        return {
            'x': predicted_x,
            'y': predicted_y,
            'z': predicted_z,
            't': current_time,
            'confidence': predicted_confidence
        }

    def _analyze_lbw_decisions(self, tracking_data):
        """Analyze LBW (Leg Before Wicket) decisions"""
        lbw_analysis = []

        try:
            trajectory = tracking_data['ball_trajectory']
            stumps_pos = tracking_data['stumps_position']
            batter_pos = tracking_data['batter_position']

            if not trajectory or not stumps_pos:
                return lbw_analysis

            # Find the point where ball is closest to wicket
            wicket_x, wicket_y = stumps_pos['position_3d'][:2] if stumps_pos['position_3d'] else (0, 0)

            for point in trajectory:
                ball_x, ball_y = point['x'], point['y']

                # Calculate distance to wicket
                distance_to_wicket = np.sqrt((ball_x - wicket_x)**2 + (ball_y - wicket_y)**2)

                # Check if ball would hit wicket
                would_hit_wicket = distance_to_wicket < 0.3  # 30cm tolerance

                # Check if ball is in line with wicket (LBW consideration)
                # Simplified: check if ball is between wicket and batter
                lbw_likelihood = 0
                if batter_pos:
                    batter_x, batter_y = batter_pos['x'], batter_pos['y']
                    # Ball is in LBW zone if it's between batter and wicket on x-axis
                    if min(batter_x, wicket_x) < ball_x < max(batter_x, wicket_x):
                        lbw_likelihood = 0.8 if would_hit_wicket else 0.3

                lbw_analysis.append({
                    'timestamp': point['t'],
                    'ball_position': (ball_x, ball_y),
                    'distance_to_wicket': distance_to_wicket,
                    'would_hit_wicket': would_hit_wicket,
                    'lbw_likelihood': lbw_likelihood,
                    'decision': 'OUT' if would_hit_wicket else 'NOT OUT'
                })

        except Exception as e:
            logger.error(f"Error in LBW analysis: {e}")

        return lbw_analysis

    def _calculate_trajectory_confidence(self, trajectory):
        """Calculate overall confidence score for trajectory"""
        if not trajectory:
            return 0.0

        if len(trajectory) < 2:
            return 0.5

        # Average confidence of individual detections
        avg_confidence = np.mean([p['confidence'] for p in trajectory])

        # Consistency score based on smooth motion
        velocities = []
        for i in range(1, len(trajectory)):
            dx = trajectory[i]['x'] - trajectory[i-1]['x']
            dy = trajectory[i]['y'] - trajectory[i-1]['y']
            dt = trajectory[i]['t'] - trajectory[i-1]['t']
            if dt > 0:
                speed = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(speed)

        if velocities:
            speed_std = np.std(velocities)
            speed_mean = np.mean(velocities)
            consistency = 1.0 - min(speed_std / (speed_mean + 1e-6), 1.0)  # Normalize
        else:
            consistency = 0.5

        # Combine scores
        overall_confidence = (avg_confidence * 0.6 + consistency * 0.4)

        return min(overall_confidence, 1.0)

    def _convert_numpy_types(self, obj):
        """
        Recursively convert numpy types to Python native types for JSON serialization.
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj
