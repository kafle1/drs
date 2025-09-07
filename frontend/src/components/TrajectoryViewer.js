import React, { useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const TrajectoryLine = ({ points }) => {
  const lineRef = useRef();

  // Convert points to Three.js Vector3
  const trajectoryPoints = points.map(point =>
    new THREE.Vector3(point.x / 100, point.y / 100, point.z / 100) // Scale down
  );

  useEffect(() => {
    if (lineRef.current && trajectoryPoints.length > 0) {
      const geometry = new THREE.BufferGeometry().setFromPoints(trajectoryPoints);
      const material = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 3 });
      const line = new THREE.Line(geometry, material);
      lineRef.current.add(line);
    }
  }, [trajectoryPoints]);

  return <group ref={lineRef} />;
};

const Ball = ({ position }) => {
  const meshRef = useRef();

  useFrame((state) => {
    if (meshRef.current && position) {
      meshRef.current.position.set(
        position.x / 100,
        position.y / 100,
        position.z / 100
      );
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.1, 16, 16]} />
      <meshStandardMaterial color="white" />
    </mesh>
  );
};

const TrajectoryViewer = ({ trajectoryData, currentTime = 0 }) => {
  if (!trajectoryData || !trajectoryData.points || trajectoryData.points.length === 0) {
    return (
      <div style={{ width: '100%', height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
        <p>No trajectory data available</p>
      </div>
    );
  }

  // Find current ball position based on time
  const currentPoint = trajectoryData.points.find(point => point.t >= currentTime) ||
                      trajectoryData.points[trajectoryData.points.length - 1];

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />

        {/* Trajectory line */}
        <TrajectoryLine points={trajectoryData.points} />

        {/* Current ball position */}
        {currentPoint && <Ball position={currentPoint} />}

        {/* Simple grid */}
        <gridHelper args={[10, 10]} />
      </Canvas>

      <div style={{ padding: '10px', background: '#f5f5f5' }}>
        <p>Confidence: {(trajectoryData.confidence_score * 100).toFixed(1)}%</p>
        <p>Points tracked: {trajectoryData.points.length}</p>
      </div>
    </div>
  );
};

export default TrajectoryViewer;
