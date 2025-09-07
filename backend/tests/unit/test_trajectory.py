import pytest
import numpy as np
from unittest.mock import Mock
import math

# Import the service to test
from services.ball_tracking_service import BallTrackingService


class TestTrajectoryCalculation:
    """Unit tests for trajectory calculation methods"""

    def setup_method(self):
        """Setup before each test"""
        self.service = BallTrackingService()

    def test_calculate_trajectory_confidence_perfect_line(self):
        """Test confidence calculation for perfect linear trajectory"""
        points = []
        for i in range(10):
            points.append({
                "x": 100 + i * 10,
                "y": 200 + i * 5,
                "t": i * 0.1
            })

        confidence = self.service._calculate_trajectory_confidence(points)

        # Perfect linear trajectory should have high confidence
        assert confidence > 0.8

    def test_calculate_trajectory_confidence_random_points(self):
        """Test confidence calculation for random/noisy points"""
        np.random.seed(42)  # For reproducible results
        points = []
        for i in range(10):
            points.append({
                "x": 100 + np.random.normal(0, 20),
                "y": 200 + np.random.normal(0, 20),
                "t": i * 0.1
            })

        confidence = self.service._calculate_trajectory_confidence(points)

        # Random points should have low confidence
        assert confidence < 0.5

    def test_calculate_trajectory_confidence_empty_points(self):
        """Test confidence calculation with empty points list"""
        confidence = self.service._calculate_trajectory_confidence([])

        assert confidence == 0.0

    def test_calculate_trajectory_confidence_single_point(self):
        """Test confidence calculation with single point"""
        points = [{"x": 100, "y": 200, "t": 0.0}]

        confidence = self.service._calculate_trajectory_confidence(points)

        assert confidence == 0.0  # Can't calculate confidence with single point

    def test_calculate_trajectory_confidence_two_points(self):
        """Test confidence calculation with two points"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 205, "t": 0.1}
        ]

        confidence = self.service._calculate_trajectory_confidence(points)

        assert confidence == 1.0  # Two points always have perfect confidence

    def test_calculate_velocity_constant_speed(self):
        """Test velocity calculation for constant speed motion"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 120, "y": 220, "t": 0.2},
            {"x": 130, "y": 230, "t": 0.3}
        ]

        velocities = self.service._calculate_velocities(points)

        assert len(velocities) == len(points) - 1
        # All velocities should be approximately equal
        for i in range(len(velocities) - 1):
            assert abs(velocities[i] - velocities[i + 1]) < 1.0

    def test_calculate_velocity_accelerating_motion(self):
        """Test velocity calculation for accelerating motion"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 105, "y": 205, "t": 0.1},  # Slow
            {"x": 115, "y": 215, "t": 0.2},  # Faster
            {"x": 130, "y": 230, "t": 0.3}   # Even faster
        ]

        velocities = self.service._calculate_velocities(points)

        assert len(velocities) == len(points) - 1
        # Velocities should be increasing
        assert velocities[0] < velocities[1] < velocities[2]

    def test_calculate_acceleration(self):
        """Test acceleration calculation"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 125, "y": 225, "t": 0.2},
            {"x": 145, "y": 245, "t": 0.3}
        ]

        accelerations = self.service._calculate_accelerations(points)

        assert len(accelerations) == len(points) - 2
        # Should have some acceleration values
        assert all(isinstance(acc, (int, float)) for acc in accelerations)

    def test_estimate_ball_position_linear_interpolation(self):
        """Test position estimation with linear interpolation"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 120, "y": 220, "t": 0.2}
        ]

        # Estimate at t=0.1 (midpoint)
        position = self.service._estimate_ball_position(points, 0.1)

        assert position is not None
        assert position["x"] == 110  # Linear interpolation
        assert position["y"] == 210
        assert position["t"] == 0.1

    def test_estimate_ball_position_before_first_point(self):
        """Test position estimation before first point"""
        points = [
            {"x": 100, "y": 200, "t": 0.2},
            {"x": 120, "y": 220, "t": 0.4}
        ]

        # Estimate at t=0.0 (before first point)
        position = self.service._estimate_ball_position(points, 0.0)

        assert position is not None
        assert position["t"] == 0.0
        # Should extrapolate backwards
        assert position["x"] < 100

    def test_estimate_ball_position_after_last_point(self):
        """Test position estimation after last point"""
        points = [
            {"x": 100, "y": 200, "t": 0.2},
            {"x": 120, "y": 220, "t": 0.4}
        ]

        # Estimate at t=0.6 (after last point)
        position = self.service._estimate_ball_position(points, 0.6)

        assert position is not None
        assert position["t"] == 0.6
        # Should extrapolate forwards
        assert position["x"] > 120

    def test_estimate_ball_position_exact_match(self):
        """Test position estimation at exact point time"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 120, "y": 220, "t": 0.2}
        ]

        # Estimate at exact point t=0.1
        position = self.service._estimate_ball_position(points, 0.1)

        assert position is not None
        assert position["x"] == 110
        assert position["y"] == 210
        assert position["t"] == 0.1

    def test_filter_trajectory_points_remove_duplicates(self):
        """Test filtering duplicate points"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 100, "y": 200, "t": 0.0},  # Duplicate
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 110, "y": 210, "t": 0.1},  # Another duplicate
            {"x": 120, "y": 220, "t": 0.2}
        ]

        filtered = self.service._filter_trajectory_points(points)

        assert len(filtered) == 3  # Should remove duplicates
        assert filtered[0]["t"] == 0.0
        assert filtered[1]["t"] == 0.1
        assert filtered[2]["t"] == 0.2

    def test_filter_trajectory_points_remove_outliers(self):
        """Test filtering outlier points"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 200, "y": 300, "t": 0.2},  # Outlier
            {"x": 120, "y": 220, "t": 0.3}
        ]

        filtered = self.service._filter_trajectory_points(points)

        # Should remove or adjust the outlier
        assert len(filtered) <= len(points)
        assert all(isinstance(p, dict) for p in filtered)

    def test_calculate_trajectory_length(self):
        """Test trajectory length calculation"""
        points = [
            {"x": 0, "y": 0, "t": 0.0},
            {"x": 3, "y": 4, "t": 0.1},  # Distance = 5
            {"x": 6, "y": 8, "t": 0.2}   # Distance = 5 more
        ]

        length = self.service._calculate_trajectory_length(points)

        assert abs(length - 10.0) < 0.1  # Should be approximately 10

    def test_calculate_trajectory_smoothness(self):
        """Test trajectory smoothness calculation"""
        # Smooth trajectory
        smooth_points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 102, "y": 202, "t": 0.1},
            {"x": 104, "y": 204, "t": 0.2},
            {"x": 106, "y": 206, "t": 0.3}
        ]

        smooth_score = self.service._calculate_trajectory_smoothness(smooth_points)

        # Jagged trajectory
        jagged_points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 105, "y": 205, "t": 0.2},
            {"x": 115, "y": 215, "t": 0.3}
        ]

        jagged_score = self.service._calculate_trajectory_smoothness(jagged_points)

        # Smooth trajectory should have higher smoothness score
        assert smooth_score > jagged_score

    def test_validate_trajectory_data_valid(self):
        """Test validation of valid trajectory data"""
        valid_points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 120, "y": 220, "t": 0.2}
        ]

        assert self.service._validate_trajectory_data(valid_points) == True

    def test_validate_trajectory_data_missing_fields(self):
        """Test validation with missing required fields"""
        invalid_points = [
            {"x": 100, "t": 0.0},  # Missing y
            {"x": 110, "y": 210, "t": 0.1},
            {"y": 220, "t": 0.2}   # Missing x
        ]

        assert self.service._validate_trajectory_data(invalid_points) == False

    def test_validate_trajectory_data_invalid_types(self):
        """Test validation with invalid data types"""
        invalid_points = [
            {"x": "100", "y": 200, "t": 0.0},  # x should be number
            {"x": 110, "y": 210, "t": 0.1}
        ]

        assert self.service._validate_trajectory_data(invalid_points) == False

    def test_calculate_parabolic_trajectory_fit(self):
        """Test fitting trajectory to parabolic curve"""
        # Generate points following a parabola: y = x^2
        points = []
        for i in range(-5, 6):
            x = i
            y = x * x
            points.append({"x": x, "y": y, "t": i * 0.1})

        fit_quality = self.service._calculate_parabolic_trajectory_fit(points)

        # Should have good fit for parabolic data
        assert fit_quality > 0.8

    def test_detect_trajectory_anomalies(self):
        """Test detection of anomalous points in trajectory"""
        points = [
            {"x": 100, "y": 200, "t": 0.0},
            {"x": 110, "y": 210, "t": 0.1},
            {"x": 120, "y": 220, "t": 0.2},
            {"x": 200, "y": 300, "t": 0.3},  # Anomaly
            {"x": 130, "y": 230, "t": 0.4}
        ]

        anomalies = self.service._detect_trajectory_anomalies(points)

        assert isinstance(anomalies, list)
        assert len(anomalies) > 0  # Should detect the anomaly at index 3
