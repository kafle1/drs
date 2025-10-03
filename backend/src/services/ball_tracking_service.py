import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import time
import logging
from config import BALL_TRACKING, PITCH_CONFIG, STUMP_CONFIG, MAX_PROCESSING_FRAMES

logger = logging.getLogger(__name__)

class BallTrackingService:
    def __init__(self):
        # Ball detection parameters from config
        self.min_ball_radius = BALL_TRACKING["min_radius"]
        self.max_ball_radius = BALL_TRACKING["max_radius"]
        self.min_confidence = BALL_TRACKING["min_confidence"]
        self.max_velocity = BALL_TRACKING["max_velocity_px_per_sec"]
        self.prediction_tolerance = BALL_TRACKING["prediction_tolerance_px"]

        # Pitch dimensions from config
        self.pitch_length = PITCH_CONFIG["length_m"]
        self.pitch_width = PITCH_CONFIG["width_m"]
        self.camera_height = PITCH_CONFIG["camera_height_m"]
        self.camera_angle = np.radians(PITCH_CONFIG["camera_angle_deg"])
        self.focal_length_px = PITCH_CONFIG["focal_length_px"]

        # Stump detection parameters from config
        self.stump_min_area = STUMP_CONFIG["min_area"]
        self.stump_max_area = STUMP_CONFIG["max_area"]

        # Color ranges for detection
        self.ball_color_ranges = {
            'white': ([0, 0, 200], [180, 30, 255]),
            'red': ([0, 50, 50], [10, 255, 255]),
            'orange': ([5, 50, 50], [15, 255, 255])
        }

        # Pitch color range (green grass)
        self.pitch_color_range = ([35, 50, 50], [80, 255, 255])

    def track_ball(self, video_path: str) -> Dict[str, Any]:
        """
        Comprehensive ball tracking with pitch analysis, LBW detection, and 3D reconstruction
        """
        start_time = time.time()
        logger.info(f"Starting comprehensive ball tracking for: {video_path}")

        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(f"Video specs: {fps} FPS, {frame_count} frames, {width}x{height}")

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
            'last_ball_position': None,
            'ball_velocity': None
        }

        # First pass: Analyze pitch and find static elements
        logger.info("First pass: Analyzing pitch and static elements...")
        pitch_info = self._analyze_pitch_and_static_elements(cap, width, height)

        # Store static elements in tracking data
        if pitch_info and pitch_info.get('stumps'):
            tracking_data['stumps_position'] = pitch_info['stumps']
            logger.info(f"Stumps detected at position: {pitch_info['stumps'].get('position_3d', 'N/A')}")

        # Reset video to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # Second pass: Track dynamic elements
        logger.info("Second pass: Tracking dynamic elements...")
        frame_idx = 0
        prev_frame = None
        max_frames = min(frame_count, MAX_PROCESSING_FRAMES)

        while frame_idx < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = frame_idx / fps

            # Process frame
            frame_data = self._process_frame(frame, prev_frame, pitch_info, current_time, frame_idx, tracking_data)

            # Store frame data
            tracking_data['frame_data'].append(frame_data)
            tracking_data['timestamps'].append(current_time)

            # Update trajectory if ball detected with high confidence
            if frame_data['ball_position'] is not None and frame_data['ball_position']['confidence'] > self.min_confidence:
                ball_pos = frame_data['ball_position']

                # Check temporal consistency - ball shouldn't jump too far
                if tracking_data['last_ball_position'] is not None:
                    last_pos = tracking_data['last_ball_position']
                    distance = np.sqrt((ball_pos['x'] - last_pos['x'])**2 + (ball_pos['y'] - last_pos['y'])**2)

                    # Calculate expected maximum distance based on time and typical ball speed
                    time_diff = current_time - last_pos.get('t', current_time - 0.1)
                    max_expected_distance = time_diff * self.max_velocity

                    # Check velocity consistency
                    velocity_consistent = True
                    if tracking_data['ball_velocity'] is not None and time_diff > 0:
                        expected_x = last_pos['x'] + tracking_data['ball_velocity']['vx'] * time_diff
                        expected_y = last_pos['y'] + tracking_data['ball_velocity']['vy'] * time_diff
                        prediction_error = np.sqrt((ball_pos['x'] - expected_x)**2 + (ball_pos['y'] - expected_y)**2)
                        velocity_consistent = prediction_error < self.prediction_tolerance

                    # If ball moved too far or velocity is inconsistent, it might be a false positive
                    if distance > max_expected_distance or not velocity_consistent:
                        logger.debug(f"Ball position inconsistent at frame {frame_idx}, skipping")
                    else:
                        # Update velocity estimate
                        if time_diff > 0:
                            vx = (ball_pos['x'] - last_pos['x']) / time_diff
                            vy = (ball_pos['y'] - last_pos['y']) / time_diff
                            vz = (ball_pos['z'] - last_pos['z']) / time_diff
                            tracking_data['ball_velocity'] = {'vx': vx, 'vy': vy, 'vz': vz}

                        ball_pos['t'] = current_time
                        tracking_data['ball_trajectory'].append(ball_pos)
                        tracking_data['last_ball_position'] = ball_pos
                else:
                    # First detection - initialize velocity as zero
                    tracking_data['ball_velocity'] = {'vx': 0, 'vy': 0, 'vz': 0}
                    ball_pos['t'] = current_time
                    tracking_data['ball_trajectory'].append(ball_pos)
                    tracking_data['last_ball_position'] = ball_pos

            elif frame_data['ball_position'] is None and len(tracking_data['ball_trajectory']) > 0:
                # No detection but we have previous trajectory - try to predict
                predicted_pos = self._predict_ball_position(tracking_data, current_time)
                if predicted_pos:
                    tracking_data['ball_trajectory'].append(predicted_pos)
                    tracking_data['last_ball_position'] = predicted_pos

            # Update positions
            if frame_data['bowler_position']:
                tracking_data['bowler_position'] = frame_data['bowler_position']
            if frame_data['batter_position']:
                tracking_data['batter_position'] = frame_data['batter_position']

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

        # Synchronize timestamps with trajectory points
        timestamps = [point['t'] for point in tracking_data['ball_trajectory']]

        result = {
            "points": tracking_data['ball_trajectory'],
            "timestamps": timestamps,
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
        """Enhanced stump detection using multiple methods"""
        try:
            height, width = frame.shape[:2]

            # Method 1: Edge-based detection
            stumps_from_edges = self._detect_stumps_by_edges(frame)

            # Method 2: Color-based detection - temporarily disabled
            stumps_from_color = []  # self._detect_stumps_by_color(frame)

            # Method 3: Shape-based detection - temporarily disabled
            stumps_from_shape = []  # self._detect_stumps_by_shape(frame)

            # Combine detections
            all_candidates = []
            if stumps_from_edges:
                all_candidates.extend(stumps_from_edges)
            if stumps_from_color:
                all_candidates.extend(stumps_from_color)
            if stumps_from_shape:
                all_candidates.extend(stumps_from_shape)

            logger.debug(f"Found {len(all_candidates)} stump candidates from all methods")

            if not all_candidates:
                return None

            # Group nearby detections (they might be detecting the same stumps)
            grouped_stumps = self._group_stump_candidates(all_candidates)

            # Find the best stump group (should be 3 stumps in a line)
            best_group = None
            best_score = 0

            for group in grouped_stumps:
                if len(group) >= 2:  # At least 2 stumps detected
                    # Calculate group properties
                    centers = []
                    for s in group:
                        try:
                            # Ensure x and y are numbers
                            x_val = s.get('x') if hasattr(s, 'get') else None
                            y_val = s.get('y') if hasattr(s, 'get') else None
                            
                            if x_val is None or y_val is None:
                                continue
                            
                            # Convert to float, handling various cases
                            if isinstance(x_val, (int, float)):
                                x = float(x_val)
                            elif isinstance(x_val, (tuple, list)) and len(x_val) > 0:
                                x = float(x_val[0]) if isinstance(x_val[0], (int, float)) else 0.0
                            else:
                                x = 0.0
                            
                            if isinstance(y_val, (int, float)):
                                y = float(y_val)
                            elif isinstance(y_val, (tuple, list)) and len(y_val) > 0:
                                y = float(y_val[0]) if isinstance(y_val[0], (int, float)) else 0.0
                            else:
                                y = 0.0
                            
                            centers.append((x, y))
                        except (KeyError, TypeError, IndexError, ValueError, AttributeError):
                            logger.warning(f"Invalid stump candidate: {s}")
                            continue
                    
                    if len(centers) < 2:
                        continue
                    avg_x = sum(x for x, y in centers) / len(centers)
                    avg_y = sum(y for y in centers) / len(centers)

                    # Check if stumps are roughly aligned (small y variation)
                    y_coords = [y for x, y in centers]
                    y_spread = max(y_coords) - min(y_coords)

                    # Check x spacing (stumps are ~2.5 inches apart = ~20-30 pixels)
                    x_coords = sorted([x for x, y in centers])
                    x_spacings = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords)-1)]
                    avg_spacing = sum(x_spacings) / len(x_spacings) if x_spacings else 0

                    # Score the group
                    alignment_score = max(0, 1.0 - y_spread / 50)  # Prefer small y spread
                    spacing_score = max(0, 1.0 - abs(avg_spacing - 25) / 25)  # Prefer ~25px spacing
                    count_score = min(1.0, len(group) / 3.0)  # Prefer 3 stumps

                    total_score = (alignment_score * 0.4 + spacing_score * 0.4 + count_score * 0.2)

                    if total_score > best_score:
                        best_score = total_score
                        best_group = {
                            'x': avg_x,
                            'y': avg_y,
                            'width': max(x_coords) - min(x_coords) + 30,  # Add padding
                            'height': max(y_coords) - min(y_coords) + 20,  # Add padding
                            'stumps': group,
                            'score': total_score
                        }

            if best_group and best_score > 0.3:  # Minimum confidence threshold
                # Convert to 3D coordinates - ensure all values are floats
                try:
                    x_pos = float(best_group['x'])
                    y_pos = float(best_group['y'])
                    width_val = float(best_group['width'])
                    height_val = float(best_group['height'])
                    base_y = y_pos + height_val
                    
                    stumps_3d = self._pixel_to_3d(x_pos, base_y, width, height)

                    logger.info(f"Stumps detected at pixel ({x_pos:.1f}, {y_pos:.1f}) "
                              f"with confidence {best_score:.2f}")

                    return {
                        'pixel_position': (x_pos, base_y),
                        'size': (width_val, height_val),
                        'position_3d': stumps_3d,
                        'confidence': best_score,
                        'stump_count': len(best_group['stumps'])
                    }
                except (TypeError, ValueError) as e:
                    logger.error(f"Error converting stump coordinates: {e}")
                    return None

        except Exception as e:
            logger.error(f"Error detecting stumps: {e}")

        return None

    def _detect_stumps_by_edges(self, frame):
        """Detect stumps using edge detection"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            candidates = []

            for contour in contours:
                try:
                    area = cv2.contourArea(contour)
                    if 30 < area < 1000:  # Reasonable stump size
                        x, y, w, h = cv2.boundingRect(contour)
                        x, y, w, h = int(x), int(y), int(w), int(h)

                        # Use bounding rect dimensions for aspect ratio
                        aspect_ratio = h / w if w > 0 else 0

                        if aspect_ratio > 2:  # Tall objects
                            candidates.append({
                                'x': float(x + w//2),
                                'y': float(y + h//2),
                                'width': float(w),
                                'height': float(h),
                                'confidence': 0.7,  # Moderate confidence for edge detection
                                'method': 'edges'
                            })
                except (cv2.error, TypeError, ValueError, IndexError) as e:
                    logger.warning(f"Error processing contour in edge detection: {e}")
                    continue

            return candidates

        except Exception as e:
            logger.error(f"Error in edge-based stump detection: {e}")
            return []

    def _detect_stumps_by_color(self, frame):
        """Detect stumps using color segmentation"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Brown color range for wooden stumps
            lower_brown = np.array([10, 30, 30])
            upper_brown = np.array([30, 150, 150])

            mask = cv2.inRange(hsv, lower_brown, upper_brown)

            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            candidates = []

            for contour in contours:
                try:
                    area = cv2.contourArea(contour)
                    if 20 < area < 800:
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = h / w if w > 0 else 0

                        if aspect_ratio > 2:  # Tall objects
                            candidates.append({
                                'x': float(x + w//2),
                                'y': float(y + h//2),
                                'width': float(w),
                                'height': float(h),
                                'confidence': 0.6,  # Moderate confidence for color detection
                                'method': 'color'
                            })
                except (cv2.error, TypeError, ValueError) as e:
                    logger.warning(f"Error processing contour in color detection: {e}")
                    continue

            return candidates

        except Exception as e:
            logger.error(f"Error in color-based stump detection: {e}")
            return []

    def _detect_stumps_by_shape(self, frame):
        """Detect stumps using Hough line detection"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            # Detect lines
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)

            if lines is None:
                return []

            # Group lines that might form stumps
            vertical_lines = []
            for line in lines:
                try:
                    line_data = line[0]
                    if len(line_data) >= 4:
                        try:
                            x1 = float(line_data[0])
                            y1 = float(line_data[1])
                            x2 = float(line_data[2])
                            y2 = float(line_data[3])
                        except (IndexError, TypeError, ValueError):
                            continue
                        angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

                        if 60 < angle < 120:  # Roughly vertical
                            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                            if length > 20:  # Minimum length
                                vertical_lines.append({
                                    'x': float((x1 + x2) // 2),
                                    'y': float((y1 + y2) // 2),
                                    'length': float(length),
                                    'angle': float(angle)
                                })
                except (IndexError, TypeError):
                    continue

            # Convert vertical lines to stump candidates
            candidates = []
            for line in vertical_lines:
                candidates.append({
                    'x': float(line['x']),
                    'y': float(line['y']),
                    'width': 5.0,  # Estimated width
                    'height': float(line['length']),
                    'confidence': 0.5,  # Lower confidence for shape detection
                    'method': 'shape'
                })

            return candidates

        except Exception as e:
            logger.error(f"Error in shape-based stump detection: {e}")
            return []

    def _group_stump_candidates(self, candidates, distance_threshold=50):
        """Group nearby stump candidates that likely represent the same stumps"""
        if not candidates:
            return []

        groups = []

        for candidate in candidates:
            # Ensure candidate is a dict with valid coordinates
            try:
                if not hasattr(candidate, 'get'):
                    logger.warning(f"Invalid candidate type: {type(candidate)}")
                    continue
                cand_x_val = candidate.get('x')
                cand_y_val = candidate.get('y')
                if cand_x_val is None or cand_y_val is None:
                    logger.warning(f"Invalid candidate missing coordinates: {candidate}")
                    continue
                
                # Convert to float
                if isinstance(cand_x_val, (int, float)):
                    cand_x = float(cand_x_val)
                elif isinstance(cand_x_val, (tuple, list)) and len(cand_x_val) > 0:
                    cand_x = float(cand_x_val[0]) if isinstance(cand_x_val[0], (int, float)) else 0.0
                else:
                    cand_x = 0.0
                
                if isinstance(cand_y_val, (int, float)):
                    cand_y = float(cand_y_val)
                elif isinstance(cand_y_val, (tuple, list)) and len(cand_y_val) > 0:
                    cand_y = float(cand_y_val[0]) if isinstance(cand_y_val[0], (int, float)) else 0.0
                else:
                    cand_y = 0.0
            except (KeyError, TypeError, ValueError, IndexError, AttributeError) as e:
                logger.warning(f"Error processing candidate: {e}, candidate: {candidate}")
                continue

            # Find existing group this candidate belongs to
            found_group = False

            for group in groups:
                for existing in group:
                    try:
                        if not isinstance(existing, dict):
                            continue
                        if 'x' not in existing or 'y' not in existing:
                            continue
                        ex_x = float(existing['x']) if not isinstance(existing['x'], (tuple, list)) else float(existing['x'][0])
                        ex_y = float(existing['y']) if not isinstance(existing['y'], (tuple, list)) else float(existing['y'][1])
                        distance = np.sqrt((cand_x - ex_x)**2 + (cand_y - ex_y)**2)
                        if distance < distance_threshold:
                            group.append(candidate)
                            found_group = True
                            break
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Error calculating distance: {e}")
                        continue

                if found_group:
                    break

            if not found_group:
                groups.append([candidate])

        return groups

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
        """Advanced color-based ball detection with adaptive thresholding"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Define multiple color ranges for cricket balls (white, red, orange, pink)
            ball_color_ranges = {
                'white': [
                    ([0, 0, 200], [180, 30, 255]),  # Standard white
                    ([0, 0, 180], [180, 40, 255]),  # Brighter white
                ],
                'red': [
                    ([0, 50, 50], [10, 255, 255]),   # Red
                    ([170, 50, 50], [180, 255, 255]), # Red (wraparound)
                ],
                'orange': [
                    ([5, 50, 50], [15, 255, 255]),   # Orange
                    ([0, 70, 50], [10, 255, 255]),   # Dark orange
                ],
                'pink': [
                    ([150, 30, 150], [170, 150, 255]), # Pink
                    ([160, 20, 180], [180, 120, 255]), # Light pink
                ]
            }

            candidates = []

            for color_name, ranges in ball_color_ranges.items():
                for lower, upper in ranges:
                    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))

                    # Apply morphological operations to clean up the mask
                    kernel = np.ones((3, 3), np.uint8)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

                    # Find contours
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    for contour in contours:
                        area = cv2.contourArea(contour)
                        if 15 < area < 1500:  # Reasonable ball size range
                            # Get bounding rectangle
                            x, y, w, h = cv2.boundingRect(contour)

                            # Calculate shape properties
                            aspect_ratio = float(w) / h if h > 0 else 0
                            perimeter = cv2.arcLength(contour, True)
                            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

                            # Calculate compactness (area to bounding box ratio)
                            rect_area = w * h
                            compactness = area / rect_area if rect_area > 0 else 0

                            # Additional check: ensure the object isn't too elongated
                            if 0.4 < aspect_ratio < 2.5 and circularity > 0.5:
                                # Get center
                                M = cv2.moments(contour)
                                if M["m00"] != 0:
                                    cx = int(M["m10"] / M["m00"])
                                    cy = int(M["m01"] / M["m00"])

                                    # Calculate color confidence based on HSV properties
                                    roi_hsv = hsv[y:y+h, x:x+w]
                                    if roi_hsv.size > 0:
                                        mean_h, mean_s, mean_v = cv2.mean(roi_hsv)[:3]

                                        # Color purity score (higher saturation = more pure color)
                                        color_purity = mean_s / 255.0

                                        # Brightness score (balls should be reasonably bright)
                                        brightness_score = mean_v / 255.0

                                        # Combine scores
                                        size_score = max(0.0, 1.0 - abs(area - 200) / 400)
                                        shape_score = circularity
                                        color_score = (color_purity * 0.7 + brightness_score * 0.3)
                                        compactness_score = compactness

                                        confidence = (
                                            size_score * 0.25 +
                                            shape_score * 0.35 +
                                            color_score * 0.25 +
                                            compactness_score * 0.15
                                        )

                                        confidence = max(0.0, min(1.0, confidence))

                                        if confidence > 0.2:  # Minimum threshold
                                            candidates.append({
                                                'x': cx,
                                                'y': cy,
                                                'confidence': confidence,
                                                'method': 'color',
                                                'color': color_name,
                                                'area': area,
                                                'circularity': circularity,
                                                'color_purity': color_purity
                                            })

            # Return the best candidate
            if candidates:
                best_candidate = max(candidates, key=lambda c: c['confidence'])
                logger.debug(f"Color detection found ball at ({best_candidate['x']}, {best_candidate['y']}) "
                           f"with confidence {best_candidate['confidence']:.2f} (color: {best_candidate['color']})")
                return best_candidate

        except Exception as e:
            logger.error(f"Error in color-based ball detection: {e}")

        return None

    def _detect_ball_by_motion_advanced(self, frame, prev_frame):
        """Advanced motion-based ball detection with improved filtering"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise
            gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
            gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

            # Compute frame difference
            frame_diff = cv2.absdiff(gray1, gray2)

            # Apply threshold to get binary image
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]

            # Dilate to fill holes and connect components
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.dilate(thresh, kernel, iterations=2)

            # Apply morphological operations to clean up noise
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            best_detection = None
            best_score = 0

            for contour in contours:
                area = cv2.contourArea(contour)
                if 30 < area < 3000:  # Reasonable motion area for ball (adjusted range)
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)

                    # Calculate aspect ratio
                    aspect_ratio = float(w) / h if h > 0 else 0

                    # Ball should be roughly circular (aspect ratio close to 1)
                    if 0.3 < aspect_ratio < 3.0:  # More lenient aspect ratio
                        # Calculate circularity
                        perimeter = cv2.arcLength(contour, True)
                        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

                        # Calculate compactness (area to bounding box ratio)
                        rect_area = w * h
                        compactness = area / rect_area if rect_area > 0 else 0

                        # Calculate motion intensity in the region
                        roi_diff = frame_diff[y:y+h, x:x+w]
                        motion_intensity = np.mean(roi_diff) / 255.0

                        # Combine scores for final confidence
                        size_score = max(0.0, 1.0 - abs(area - 400) / 800)  # Optimal around 400 pixels
                        shape_score = max(0.0, 1.0 - abs(aspect_ratio - 1.0) * 0.3)  # Prefer square shapes
                        circularity_score = min(1.0, circularity * 2)  # Boost circular objects
                        compactness_score = compactness  # Higher is better
                        motion_score = motion_intensity  # Higher motion intensity is better

                        # Weighted combination
                        confidence = (
                            size_score * 0.2 +
                            shape_score * 0.2 +
                            circularity_score * 0.3 +
                            compactness_score * 0.2 +
                            motion_score * 0.1
                        )

                        # Ensure confidence is in [0,1] range
                        confidence = max(0.0, min(1.0, confidence))

                        # Only consider detections with reasonable confidence
                        if confidence > best_score and confidence > 0.15:
                            cx = x + w // 2
                            cy = y + h // 2

                            best_detection = {
                                'x': cx,
                                'y': cy,
                                'confidence': confidence,
                                'method': 'motion',
                                'area': area,
                                'aspect_ratio': aspect_ratio,
                                'circularity': circularity,
                                'motion_intensity': motion_intensity
                            }
                            best_score = confidence

            return best_detection

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
        """Convert 2D pixel coordinates to normalized 3D coordinates for frontend"""
        try:
            # Normalize pixel coordinates to [-1, 1] range for frontend compatibility
            x_norm = (x_pixel - frame_width/2) / (frame_width/2)
            y_norm = (y_pixel - frame_height/2) / (frame_height/2)

            # For 3D visualization, we need to map pixel positions to normalized pitch coordinates
            # Frontend expects: x,y,z where x,y are in [-1,1] range representing pitch position
            # z represents height above ground in normalized units

            # Convert to normalized pitch coordinates
            # x: left-right position on pitch (-1 = left edge, 1 = right edge)
            pitch_x_norm = x_norm

            # y: length position on pitch (-1 = bowler end, 1 = batsman end)
            # Flip y because pixel coordinates have origin at top-left
            pitch_y_norm = -y_norm

            # z: height above ground (normalized)
            # Estimate height based on vertical position in frame
            # Balls higher in frame are closer to camera and thus higher
            height_factor = (frame_height - y_pixel) / frame_height  # Higher in frame = closer
            pitch_z_norm = height_factor * 0.5  # Scale to reasonable normalized height

            # Ensure values are clamped to [-1, 1] range
            pitch_x_norm = max(-1.0, min(1.0, pitch_x_norm))
            pitch_y_norm = max(-1.0, min(1.0, pitch_y_norm))
            pitch_z_norm = max(0.0, min(1.0, pitch_z_norm))  # Height should be positive

            return (pitch_x_norm, pitch_y_norm, pitch_z_norm)

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
        """Apply Kalman filter to smooth trajectory with improved robustness"""
        if len(trajectory) < 2:
            return trajectory

        try:
            # Initialize Kalman filter with better parameters
            kalman = cv2.KalmanFilter(6, 3)  # 6 state (x,y,z,vx,vy,vz), 3 measurements (x,y,z)

            # State: [x, y, z, vx, vy, vz]
            kalman.transitionMatrix = np.eye(6, dtype=np.float32)
            kalman.measurementMatrix = np.array([[1,0,0,0,0,0], [0,1,0,0,0,0], [0,0,1,0,0,0]], np.float32)

            # Process noise - adjust based on expected ball movement
            kalman.processNoiseCov = np.eye(6, dtype=np.float32) * 0.03  # Reduced from 0.01

            # Measurement noise - higher for less accurate detections
            kalman.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.2  # Increased from 0.1

            # Initialize state with first measurement
            first_point = trajectory[0]
            kalman.statePost = np.array([
                [first_point['x']], [first_point['y']], [first_point['z']],
                [0], [0], [0]  # Initial velocities
            ], dtype=np.float32)

            smoothed_points = [first_point]  # Keep original first point

            for i in range(1, len(trajectory)):
                point = trajectory[i]

                # Create measurement
                measurement = np.array([[point['x']], [point['y']], [point['z']]], np.float32)

                # Predict
                prediction = kalman.predict()

                # Update with measurement
                corrected = kalman.correct(measurement)

                # Create smoothed point
                smoothed_point = {
                    'x': float(corrected[0][0]),
                    'y': float(corrected[1][0]),
                    'z': float(corrected[2][0]),
                    't': point['t'],
                    'confidence': point['confidence']
                }
                smoothed_points.append(smoothed_point)

            return smoothed_points

        except Exception as e:
            logger.error(f"Error in Kalman filtering: {e}")
            return trajectory  # Return original trajectory if filtering fails

    def _remove_outliers(self, trajectory):
        """Remove outlier points using multiple statistical methods"""
        if len(trajectory) < 3:
            return trajectory

        try:
            # Method 1: Velocity-based outlier detection
            velocities = []
            accelerations = []

            for i in range(1, len(trajectory)):
                dx = trajectory[i]['x'] - trajectory[i-1]['x']
                dy = trajectory[i]['y'] - trajectory[i-1]['y']
                dz = trajectory[i]['z'] - trajectory[i-1]['z']
                dt = trajectory[i]['t'] - trajectory[i-1]['t']

                if dt > 0:
                    speed = np.sqrt(dx**2 + dy**2 + dz**2) / dt
                    velocities.append(speed)

                    # Calculate acceleration if we have enough points
                    if i > 1:
                        prev_speed = velocities[-2] if len(velocities) > 1 else speed
                        acceleration = abs(speed - prev_speed) / dt
                        accelerations.append(acceleration)

            if not velocities:
                return trajectory

            # Calculate velocity statistics
            mean_velocity = np.mean(velocities)
            std_velocity = np.std(velocities)

            # Calculate acceleration statistics if available
            accel_threshold = float('inf')
            if accelerations:
                mean_accel = np.mean(accelerations)
                std_accel = np.std(accelerations)
                accel_threshold = mean_accel + 3 * std_accel

            # Velocity threshold for outliers
            velocity_threshold = mean_velocity + 3 * std_velocity

            # Method 2: Distance-based outlier detection (sudden jumps)
            distances = []
            for i in range(1, len(trajectory)):
                dx = trajectory[i]['x'] - trajectory[i-1]['x']
                dy = trajectory[i]['y'] - trajectory[i-1]['y']
                dz = trajectory[i]['z'] - trajectory[i-1]['z']
                distance = np.sqrt(dx**2 + dy**2 + dz**2)
                distances.append(distance)

            if distances:
                mean_distance = np.mean(distances)
                std_distance = np.std(distances)
                distance_threshold = mean_distance + 3 * std_distance
            else:
                distance_threshold = float('inf')

            # Filter points
            filtered_trajectory = [trajectory[0]]  # Always keep first point

            for i in range(1, len(trajectory)):
                point = trajectory[i]
                keep_point = True

                # Check velocity outlier
                if i-1 < len(velocities):
                    velocity = velocities[i-1]
                    if velocity > velocity_threshold:
                        logger.debug(f"Removing velocity outlier at t={point['t']:.2f}: velocity={velocity:.2f} > {velocity_threshold:.2f}")
                        keep_point = False

                # Check acceleration outlier
                if i-2 >= 0 and i-2 < len(accelerations):
                    acceleration = accelerations[i-2]
                    if acceleration > accel_threshold:
                        logger.debug(f"Removing acceleration outlier at t={point['t']:.2f}: accel={acceleration:.2f} > {accel_threshold:.2f}")
                        keep_point = False

                # Check distance outlier
                if i-1 < len(distances):
                    distance = distances[i-1]
                    if distance > distance_threshold:
                        logger.debug(f"Removing distance outlier at t={point['t']:.2f}: distance={distance:.2f} > {distance_threshold:.2f}")
                        keep_point = False

                if keep_point:
                    filtered_trajectory.append(point)

            logger.info(f"Outlier removal: {len(trajectory)} -> {len(filtered_trajectory)} points")
            return filtered_trajectory

        except Exception as e:
            logger.error(f"Error in outlier removal: {e}")
            return trajectory  # Return original if filtering fails

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
