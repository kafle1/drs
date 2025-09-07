import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch
import numpy as np
import cv2

from services.ball_tracking_service import BallTrackingService


class TestVideoProcessingPerformance:
    """Performance tests for video processing operations"""

    def setup_method(self):
        """Setup before each test"""
        self.service = BallTrackingService()

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_video_processing_under_60_seconds(self, mock_exists, mock_cap):
        """Test that video processing completes within 60 seconds"""
        mock_exists.return_value = True

        # Mock a video with 300 frames (10 seconds at 30fps)
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.get.side_effect = [30, 640, 480]  # fps, width, height

        # Create mock frames
        frames = []
        for i in range(300):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add some motion to simulate ball movement
            ball_x = 320 + int(50 * np.sin(i * 0.1))
            ball_y = 240 + int(30 * np.cos(i * 0.1))
            cv2.circle(frame, (ball_x, ball_y), 8, (255, 255, 255), -1)
            frames.append((True, frame))

        frames.append((False, None))  # End of video
        mock_cap.return_value.read.side_effect = frames

        start_time = time.time()
        result = self.service.track_ball("performance_test.mp4")
        end_time = time.time()

        processing_time = end_time - start_time

        # Assert processing completes within 60 seconds
        assert processing_time < 60.0, f"Processing took {processing_time:.2f}s, exceeds 60s limit"

        # Verify result structure
        assert "points" in result
        assert "confidence_score" in result
        assert "processing_time" in result
        assert len(result["points"]) > 0

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_large_video_processing_performance(self, mock_exists, mock_cap):
        """Test performance with larger video (more frames)"""
        mock_exists.return_value = True

        # Mock a longer video with 900 frames (30 seconds at 30fps)
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.get.side_effect = [30, 1280, 720]  # Higher resolution

        # Create mock frames with more complex motion
        frames = []
        for i in range(900):
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            # More complex ball trajectory
            ball_x = 640 + int(100 * np.sin(i * 0.05) + 50 * np.cos(i * 0.1))
            ball_y = 360 + int(80 * np.sin(i * 0.08) + 40 * np.sin(i * 0.15))
            cv2.circle(frame, (ball_x, ball_y), 12, (255, 255, 255), -1)
            frames.append((True, frame))

        frames.append((False, None))
        mock_cap.return_value.read.side_effect = frames

        start_time = time.time()
        result = self.service.track_ball("large_performance_test.mp4")
        end_time = time.time()

        processing_time = end_time - start_time

        # Should still complete within reasonable time (allowing more time for larger video)
        assert processing_time < 120.0, f"Large video processing took {processing_time:.2f}s, exceeds 120s limit"

        # Verify result quality
        assert len(result["points"]) > 100  # Should track many points
        assert result["confidence_score"] > 0.1

    def test_memory_usage_during_processing(self):
        """Test that memory usage remains reasonable during processing"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create a large mock video processing scenario
        with patch('cv2.VideoCapture') as mock_cap, \
             patch('os.path.exists', return_value=True):

            mock_cap.return_value.isOpened.return_value = True
            mock_cap.return_value.get.side_effect = [30, 1920, 1080]  # 1080p

            # Create many frames
            frames = []
            for i in range(600):  # 20 seconds
                frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                cv2.circle(frame, (960 + i % 100, 540 + i % 50), 15, (255, 255, 255), -1)
                frames.append((True, frame))
            frames.append((False, None))
            mock_cap.return_value.read.side_effect = frames

            result = self.service.track_ball("memory_test.mp4")

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (< 500MB)
            assert memory_increase < 500, f"Memory increased by {memory_increase:.1f}MB, exceeds 500MB limit"

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_concurrent_video_processing_performance(self, mock_exists, mock_cap):
        """Test performance when processing multiple videos concurrently"""
        import threading

        mock_exists.return_value = True

        def create_mock_video(name):
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            mock_cap_instance.get.side_effect = [30, 640, 480]

            frames = []
            for i in range(150):  # 5 seconds
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.circle(frame, (320 + i % 50, 240 + i % 30), 8, (255, 255, 255), -1)
                frames.append((True, frame))
            frames.append((False, None))
            mock_cap_instance.read.side_effect = frames
            return mock_cap_instance

        # Process 3 videos concurrently
        results = []
        threads = []

        def process_video(video_name):
            with patch('cv2.VideoCapture', return_value=create_mock_video(video_name)):
                result = self.service.track_ball(video_name)
                results.append(result)

        start_time = time.time()

        for i in range(3):
            thread = threading.Thread(target=process_video, args=[f"concurrent_test_{i}.mp4"])
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Concurrent processing should complete faster than sequential
        # (allowing some overhead for thread management)
        assert total_time < 30.0, f"Concurrent processing took {total_time:.2f}s, exceeds 30s limit"
        assert len(results) == 3
        assert all("points" in result for result in results)

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_processing_time_scalability(self, mock_exists, mock_cap):
        """Test that processing time scales reasonably with video length"""
        mock_exists.return_value = True

        def test_video_length(num_frames):
            mock_cap_instance = Mock()
            mock_cap_instance.isOpened.return_value = True
            mock_cap_instance.get.side_effect = [30, 640, 480]

            frames = []
            for i in range(num_frames):
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.circle(frame, (320 + i % 50, 240 + i % 30), 8, (255, 255, 255), -1)
                frames.append((True, frame))
            frames.append((False, None))
            mock_cap_instance.read.side_effect = frames

            with patch('cv2.VideoCapture', return_value=mock_cap_instance):
                start_time = time.time()
                result = self.service.track_ball(f"scalability_test_{num_frames}.mp4")
                end_time = time.time()

                return end_time - start_time, result

        # Test different video lengths
        lengths_and_times = []
        for num_frames in [30, 90, 150, 300]:  # 1, 3, 5, 10 seconds
            processing_time, result = test_video_length(num_frames)
            lengths_and_times.append((num_frames, processing_time))

            # Each video should be processed
            assert "points" in result
            assert len(result["points"]) > 0

        # Check scalability - processing time should roughly scale with video length
        for i in range(1, len(lengths_and_times)):
            prev_frames, prev_time = lengths_and_times[i-1]
            curr_frames, curr_time = lengths_and_times[i]

            scaling_factor = curr_frames / prev_frames
            time_ratio = curr_time / prev_time

            # Time scaling should be roughly proportional to frame count
            # Allow some variance due to algorithm complexity
            assert time_ratio < scaling_factor * 2, \
                f"Processing time scaled poorly: {time_ratio:.2f}x vs {scaling_factor:.2f}x expected"

    def test_cpu_usage_during_processing(self):
        """Test that CPU usage remains reasonable during processing"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Get initial CPU usage
        initial_cpu = process.cpu_percent(interval=1.0)

        # Process a video
        with patch('cv2.VideoCapture') as mock_cap, \
             patch('os.path.exists', return_value=True):

            mock_cap.return_value.isOpened.return_value = True
            mock_cap.return_value.get.side_effect = [30, 640, 480]

            frames = []
            for i in range(300):
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.circle(frame, (320 + i % 50, 240 + i % 30), 8, (255, 255, 255), -1)
                frames.append((True, frame))
            frames.append((False, None))
            mock_cap.return_value.read.side_effect = frames

            start_time = time.time()
            result = self.service.track_ball("cpu_test.mp4")
            end_time = time.time()

            # Get CPU usage during processing
            final_cpu = process.cpu_percent(interval=1.0)

            processing_time = end_time - start_time

            # CPU usage should be reasonable (< 90%)
            assert final_cpu < 90.0, f"CPU usage was {final_cpu:.1f}%, exceeds 90% limit"

            # Processing should complete
            assert processing_time > 0
            assert "points" in result

    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_error_recovery_performance(self, mock_exists, mock_cap):
        """Test performance of error recovery mechanisms"""
        mock_exists.return_value = True

        # Test various error scenarios and their recovery time
        error_scenarios = [
            ("corrupted_frame", lambda: (True, None)),  # Corrupted frame
            ("empty_frame", lambda: (True, np.zeros((0, 0, 3), dtype=np.uint8))),  # Empty frame
            ("wrong_dimensions", lambda: (True, np.zeros((100, 100), dtype=np.uint8))),  # Wrong dimensions
        ]

        for scenario_name, frame_generator in error_scenarios:
            mock_cap.return_value.isOpened.return_value = True
            mock_cap.return_value.get.side_effect = [30, 640, 480]

            frames = [(True, np.zeros((480, 640, 3), dtype=np.uint8))]  # Good frame first
            frames.append(frame_generator())  # Error frame
            frames.extend([(True, np.zeros((480, 640, 3), dtype=np.uint8)) for _ in range(10)])  # More good frames
            frames.append((False, None))
            mock_cap.return_value.read.side_effect = frames

            start_time = time.time()
            result = self.service.track_ball(f"error_recovery_{scenario_name}.mp4")
            end_time = time.time()

            processing_time = end_time - start_time

            # Error recovery should be fast (< 5 seconds)
            assert processing_time < 5.0, \
                f"Error recovery for {scenario_name} took {processing_time:.2f}s, exceeds 5s limit"

            # Should still produce a result
            assert "points" in result
            assert isinstance(result["points"], list)
