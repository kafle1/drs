import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from pathlib import Path

# Import the service to test
from services.ball_tracking_service import BallTrackingService


class TestBallTrackingService:
    """Unit tests for BallTrackingService"""

    def setup_method(self):
        """Setup before each test"""
        self.service = BallTrackingService()

    def test_initialization(self):
        """Test service initialization with default parameters"""
        assert self.service.min_radius == 5
        assert self.service.max_radius == 20

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_track_ball_with_invalid_video_path(self, mock_exists, mock_cap):
        """Test tracking with non-existent video file"""
        mock_exists.return_value = True
        mock_cap.return_value.isOpened.return_value = False

        result = self.service.track_ball("nonexistent.mp4")

        assert "error" in result
        assert "Could not open video file" in result["error"]

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_track_ball_file_not_found(self, mock_exists, mock_cap):
        """Test tracking when video file doesn't exist"""
        mock_exists.return_value = False

        result = self.service.track_ball("nonexistent.mp4")

        assert "error" in result
        assert "Video file does not exist" in result["error"]

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_track_ball_empty_video(self, mock_exists, mock_cap):
        """Test tracking with empty/corrupted video"""
        mock_exists.return_value = True
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.get.return_value = 0  # No frames

        result = self.service.track_ball("empty.mp4")

        assert "error" in result
        assert "Video has no frames" in result["error"]

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_track_ball_successful_tracking(self, mock_exists, mock_cap):
        """Test successful ball tracking with mock video frames"""
        mock_exists.return_value = True

        # Mock video capture
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.get.side_effect = [30, 640, 480]  # fps, width, height
        mock_cap.return_value.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),  # Frame 1
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),  # Frame 2
            (False, None)  # End of video
        ]

        result = self.service.track_ball("test.mp4")

        assert "points" in result
        assert "confidence_score" in result
        assert "processing_time" in result
        assert isinstance(result["points"], list)
        assert result["confidence_score"] >= 0.0
        assert result["confidence_score"] <= 1.0

    def test_detect_ball_in_frame_no_ball(self):
        """Test ball detection in frame with no ball"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        circles = self.service._detect_ball_in_frame(frame)

        assert circles is None or len(circles) == 0

    def test_detect_ball_in_frame_with_ball(self):
        """Test ball detection in frame with simulated ball"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Create a white circle (simulating a ball)
        cv2.circle(frame, (320, 240), 10, (255, 255, 255), -1)

        circles = self.service._detect_ball_in_frame(frame)

        # Should detect at least one circle
        assert circles is not None
        assert len(circles) > 0

    def test_calculate_trajectory_confidence(self):
        """Test trajectory confidence calculation"""
        # Test with consistent points (high confidence)
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 105, "y": 205, "t": 0.1},
            {"x": 110, "y": 210, "t": 0.2},
        ]

        confidence = self.service._calculate_trajectory_confidence(points)

        assert confidence > 0.5  # Should be relatively high

    def test_calculate_trajectory_confidence_noisy(self):
        """Test trajectory confidence with noisy/inconsistent points"""
        # Test with inconsistent points (low confidence)
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 150, "y": 250, "t": 0.1},  # Large jump
            {"x": 50, "y": 150, "t": 0.2},   # Another large jump
        ]

        confidence = self.service._calculate_trajectory_confidence(points)

        assert confidence < 0.5  # Should be relatively low

    def test_filter_trajectory_points(self):
        """Test trajectory point filtering"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 100, "y": 200, "t": 0.0},  # Duplicate
            {"x": 105, "y": 205, "t": 0.1},
            {"x": 110, "y": 210, "t": 0.2},
        ]

        filtered = self.service._filter_trajectory_points(points)

        # Should remove duplicates and maintain order
        assert len(filtered) <= len(points)
        assert all(point in points for point in filtered)

    def test_estimate_ball_position_interpolation(self):
        """Test ball position estimation with interpolation"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.2},
        ]

        # Estimate position at t=0.1
        position = self.service._estimate_ball_position(points, 0.1)

        assert position is not None
        assert "x" in position
        assert "y" in position
        assert "t" in position
        assert position["t"] == 0.1

    def test_estimate_ball_position_extrapolation(self):
        """Test ball position estimation with extrapolation"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 105, "y": 205, "t": 0.1},
        ]

        # Estimate position at t=0.2 (beyond available data)
        position = self.service._estimate_ball_position(points, 0.2)

        assert position is not None
        assert "x" in position
        assert "y" in position
        assert "t" in position
        assert position["t"] == 0.2

    def test_validate_trajectory_data(self):
        """Test trajectory data validation"""
        # Valid trajectory
        valid_points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 105, "y": 205, "t": 0.1},
        ]

        assert self.service._validate_trajectory_data(valid_points) == True

        # Invalid trajectory - missing required fields
        invalid_points = [
            {"x": 100, "t": 0.0},  # Missing y
            {"x": 105, "y": 205, "t": 0.1},
        ]

        assert self.service._validate_trajectory_data(invalid_points) == False

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_track_ball_performance(self, mock_exists, mock_cap):
        """Test that tracking completes within reasonable time"""
        import time

        mock_exists.return_value = True
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.get.side_effect = [30, 640, 480]
        mock_cap.return_value.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (False, None)
        ]

        start_time = time.time()
        result = self.service.track_ball("test.mp4")
        end_time = time.time()

        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should complete in less than 5 seconds for unit test
        assert "processing_time" in result
        assert result["processing_time"] >= 0

    def test_ball_detection_parameters(self):
        """Test ball detection with different radius parameters"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Test with very small ball
        cv2.circle(frame, (320, 240), 3, (255, 255, 255), -1)
        circles = self.service._detect_ball_in_frame(frame)
        # May or may not detect depending on min_radius

        # Test with ball in valid range
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.circle(frame, (320, 240), 10, (255, 255, 255), -1)
        circles = self.service._detect_ball_in_frame(frame)
        # Should detect this ball
        assert circles is not None or len(circles) > 0
