import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TrajectoryViewer from '../src/components/TrajectoryViewer';

// Mock @react-three/fiber and @react-three/drei
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }) => <div data-testid="canvas">{children}</div>,
  useFrame: jest.fn(),
}));

jest.mock('three', () => ({
  Vector3: jest.fn(),
  BufferGeometry: jest.fn().mockImplementation(() => ({
    setFromPoints: jest.fn(),
  })),
  LineBasicMaterial: jest.fn(),
  Line: jest.fn(),
  GridHelper: jest.fn(),
}));

describe('TrajectoryViewer', () => {
  const mockTrajectoryData = {
    points: [
      { x: 100, y: 200, z: 0, t: 0.0 },
      { x: 110, y: 210, z: 5, t: 0.1 },
      { x: 120, y: 220, z: 10, t: 0.2 },
    ],
    confidence_score: 0.85,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders without crashing', () => {
    render(<TrajectoryViewer trajectoryData={mockTrajectoryData} />);
    expect(screen.getByTestId('canvas')).toBeInTheDocument();
  });

  test('displays no data message when trajectoryData is null', () => {
    render(<TrajectoryViewer trajectoryData={null} />);
    expect(screen.getByText('No trajectory data available')).toBeInTheDocument();
  });

  test('displays no data message when points array is empty', () => {
    render(<TrajectoryViewer trajectoryData={{ points: [] }} />);
    expect(screen.getByText('No trajectory data available')).toBeInTheDocument();
  });

  test('displays confidence score and points count', () => {
    render(<TrajectoryViewer trajectoryData={mockTrajectoryData} />);

    expect(screen.getByText('Confidence: 85.0%')).toBeInTheDocument();
    expect(screen.getByText('Points tracked: 3')).toBeInTheDocument();
  });

  test('handles currentTime prop correctly', () => {
    const { rerender } = render(
      <TrajectoryViewer trajectoryData={mockTrajectoryData} currentTime={0.1} />
    );

    // Component should render without errors with currentTime prop
    expect(screen.getByTestId('canvas')).toBeInTheDocument();

    // Re-render with different currentTime
    rerender(
      <TrajectoryViewer trajectoryData={mockTrajectoryData} currentTime={0.2} />
    );

    expect(screen.getByTestId('canvas')).toBeInTheDocument();
  });

  test('renders with default currentTime when not provided', () => {
    render(<TrajectoryViewer trajectoryData={mockTrajectoryData} />);

    // Should use default currentTime of 0
    expect(screen.getByTestId('canvas')).toBeInTheDocument();
  });

  test('handles trajectory data with missing z coordinates', () => {
    const incompleteData = {
      points: [
        { x: 100, y: 200, t: 0.0 }, // Missing z
        { x: 110, y: 210, t: 0.1 }, // Missing z
      ],
      confidence_score: 0.75,
    };

    render(<TrajectoryViewer trajectoryData={incompleteData} />);

    expect(screen.getByTestId('canvas')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 75.0%')).toBeInTheDocument();
  });

  test('handles trajectory data with non-numeric confidence', () => {
    const invalidConfidenceData = {
      points: mockTrajectoryData.points,
      confidence_score: 'invalid',
    };

    render(<TrajectoryViewer trajectoryData={invalidConfidenceData} />);

    // Should handle gracefully and display some confidence value
    expect(screen.getByTestId('canvas')).toBeInTheDocument();
  });

  test('maintains component stability with malformed data', () => {
    const malformedData = {
      points: [
        { x: 'invalid', y: 200, z: 0, t: 0.0 },
        { x: 110, y: 'invalid', z: 5, t: 0.1 },
      ],
      confidence_score: 0.5,
    };

    // Should not crash with malformed numeric data
    expect(() => {
      render(<TrajectoryViewer trajectoryData={malformedData} />);
    }).not.toThrow();
  });

  test('renders canvas with correct dimensions', () => {
    render(<TrajectoryViewer trajectoryData={mockTrajectoryData} />);

    const canvas = screen.getByTestId('canvas');
    expect(canvas).toBeInTheDocument();
    // The component sets width and height to 100% and 400px respectively
    expect(canvas).toHaveStyle({ width: '100%', height: '400px' });
  });

  test('handles very large trajectory datasets', () => {
    const largeDataset = {
      points: Array.from({ length: 1000 }, (_, i) => ({
        x: i * 10,
        y: 200 + Math.sin(i * 0.1) * 50,
        z: Math.cos(i * 0.1) * 20,
        t: i * 0.01,
      })),
      confidence_score: 0.92,
    };

    render(<TrajectoryViewer trajectoryData={largeDataset} />);

    expect(screen.getByTestId('canvas')).toBeInTheDocument();
    expect(screen.getByText('Points tracked: 1000')).toBeInTheDocument();
  });

  test('handles trajectory with single point', () => {
    const singlePointData = {
      points: [{ x: 100, y: 200, z: 0, t: 0.0 }],
      confidence_score: 0.3,
    };

    render(<TrajectoryViewer trajectoryData={singlePointData} />);

    expect(screen.getByTestId('canvas')).toBeInTheDocument();
    expect(screen.getByText('Points tracked: 1')).toBeInTheDocument();
  });
});
