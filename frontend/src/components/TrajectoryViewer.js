import React, { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import { Box, Typography, Paper, Grid, Button, ButtonGroup } from '@mui/material';
import { SportsCricket, ViewInAr, Fullscreen, FullscreenExit } from '@mui/icons-material';
import * as THREE from 'three';

// Cricket pitch dimensions (in meters)
const PITCH_LENGTH = 22; // 22 yards
const PITCH_WIDTH = 3;   // 10 feet
const WICKET_WIDTH = 0.23; // 9 inches
const BOUNDARY_RADIUS = 50; // 50 meters
const STUMP_HEIGHT = 0.71; // 28 inches
const STUMP_RADIUS = 0.018; // 3/4 inch
const BAIL_HEIGHT = 0.03; // 1.2 inches above stumps

// Camera positions for different views
const CAMERA_VIEWS = {
  umpire: { position: [0, -15, 10], target: [0, 0, 0] },
  side: { position: [15, 0, 8], target: [0, 0, 0] },
  end: { position: [0, 15, 8], target: [0, 0, 0] },
  aerial: { position: [0, 0, 25], target: [0, 0, 0] },
  bowler: { position: [0, -25, 5], target: [0, 0, 0] }
};

const Wicket = ({ position }) => {
  return (
    <group position={position}>
      {/* Base/wooden block */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[WICKET_WIDTH, 0.05, 0.05]} />
        <meshBasicMaterial color="#654321" />
      </mesh>

      {/* Three stumps */}
      <mesh position={[-0.08, STUMP_HEIGHT/2, 0]}>
        <cylinderGeometry args={[STUMP_RADIUS, STUMP_RADIUS, STUMP_HEIGHT]} />
        <meshBasicMaterial color="#8B4513" />
      </mesh>
      <mesh position={[0, STUMP_HEIGHT/2, 0]}>
        <cylinderGeometry args={[STUMP_RADIUS, STUMP_RADIUS, STUMP_HEIGHT]} />
        <meshBasicMaterial color="#8B4513" />
      </mesh>
      <mesh position={[0.08, STUMP_HEIGHT/2, 0]}>
        <cylinderGeometry args={[STUMP_RADIUS, STUMP_RADIUS, STUMP_HEIGHT]} />
        <meshBasicMaterial color="#8B4513" />
      </mesh>

      {/* Bails */}
      <mesh position={[-0.08, STUMP_HEIGHT + BAIL_HEIGHT/2, 0]}>
        <cylinderGeometry args={[STUMP_RADIUS * 1.5, STUMP_RADIUS * 1.5, BAIL_HEIGHT]} />
        <meshBasicMaterial color="#DAA520" />
      </mesh>
      <mesh position={[0.08, STUMP_HEIGHT + BAIL_HEIGHT/2, 0]}>
        <cylinderGeometry args={[STUMP_RADIUS * 1.5, STUMP_RADIUS * 1.5, BAIL_HEIGHT]} />
        <meshBasicMaterial color="#DAA520" />
      </mesh>
    </group>
  );
};

const WicketZone = ({ position }) => {
  return (
    <group position={position}>
      {/* Wicket zone visualization - area where ball must hit */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0.03]}>
        <ringGeometry args={[0.1, 0.3, 32]} />
        <meshBasicMaterial color="#ff0000" opacity={0.3} transparent />
      </mesh>
      {/* Wicket zone boundary */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0.04]}>
        <circleGeometry args={[0.3, 32]} />
        <meshBasicMaterial color="#ff0000" opacity={0.1} transparent />
      </mesh>
    </group>
  );
};

const ImpactZone = ({ position, isHit = false }) => {
  return (
    <group position={position}>
      {/* Impact point marker */}
      <mesh position={[0, 0, 0.05]}>
        <cylinderGeometry args={[0.1, 0.1, 0.02]} />
        <meshBasicMaterial color={isHit ? "#ff0000" : "#ffff00"} />
      </mesh>
      {/* Impact zone circle */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0.06]}>
        <circleGeometry args={[0.2, 16]} />
        <meshBasicMaterial color={isHit ? "#ff0000" : "#ffff00"} opacity={0.3} transparent />
      </mesh>
    </group>
  );
};

const Bowler = ({ position, visible }) => {
  if (!position || !visible) return null;

  return (
    <group position={[position.x, position.y, position.z + 1]}>
      {/* Bowler representation - simple cylinder */}
      <mesh position={[0, 0, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 1.8]} />
        <meshBasicMaterial color="#ff6600" />
      </mesh>
      {/* Head */}
      <mesh position={[0, 0, 1.2]}>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshBasicMaterial color="#ffdbac" />
      </mesh>
      <Text position={[0, 0, 2]} fontSize={0.3} color="#ffffff" anchorX="center" anchorY="middle">
        Bowler
      </Text>
    </group>
  );
};

const Batter = ({ position, visible }) => {
  if (!position || !visible) return null;

  return (
    <group position={[position.x, position.y, position.z + 1]}>
      {/* Batter representation */}
      <mesh position={[0, 0, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 1.8]} />
        <meshBasicMaterial color="#0066ff" />
      </mesh>
      {/* Head */}
      <mesh position={[0, 0, 1.2]}>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshBasicMaterial color="#ffdbac" />
      </mesh>
      {/* Bat (simplified) */}
      <mesh position={[0.5, 0, 0.5]} rotation={[0, 0, Math.PI / 4]}>
        <cylinderGeometry args={[0.05, 0.05, 1.2]} />
        <meshBasicMaterial color="#8B4513" />
      </mesh>
      <Text position={[0, 0, 2]} fontSize={0.3} color="#ffffff" anchorX="center" anchorY="middle">
        Batter
      </Text>
    </group>
  );
};

const CricketPitch = ({ showDRS = true }) => {
  return (
    <group>
      {/* Main pitch surface */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[PITCH_WIDTH, PITCH_LENGTH]} />
        <meshLambertMaterial color="#4a7c59" />
      </mesh>

      {/* Pitch markings */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0.01]}>
        <planeGeometry args={[PITCH_WIDTH, PITCH_LENGTH]} />
        <meshBasicMaterial color="#ffffff" opacity={0.2} transparent />
      </mesh>

      {/* Center line */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0.02]}>
        <planeGeometry args={[0.05, PITCH_LENGTH]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>

      {/* Popping crease lines */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, PITCH_LENGTH/4, 0.02]}>
        <planeGeometry args={[PITCH_WIDTH + 0.5, 0.05]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -PITCH_LENGTH/4, 0.02]}>
        <planeGeometry args={[PITCH_WIDTH + 0.5, 0.05]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>

      {/* Return crease lines */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-PITCH_WIDTH/2 - 0.15, PITCH_LENGTH/4, 0.02]}>
        <planeGeometry args={[0.05, 1.5]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[PITCH_WIDTH/2 + 0.15, PITCH_LENGTH/4, 0.02]}>
        <planeGeometry args={[0.05, 1.5]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-PITCH_WIDTH/2 - 0.15, -PITCH_LENGTH/4, 0.02]}>
        <planeGeometry args={[0.05, 1.5]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[PITCH_WIDTH/2 + 0.15, -PITCH_LENGTH/4, 0.02]}>
        <planeGeometry args={[0.05, 1.5]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>

      {/* Wickets */}
      <Wicket position={[0, PITCH_LENGTH/4, 0.1]} />
      <Wicket position={[0, -PITCH_LENGTH/4, 0.1]} />

      {/* DRS-specific elements */}
      {showDRS && (
        <>
          {/* Wicket zones */}
          <WicketZone position={[0, PITCH_LENGTH/4, 0]} />
          <WicketZone position={[0, -PITCH_LENGTH/4, 0]} />
        </>
      )}

      {/* Boundary circle */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -0.05]}>
        <ringGeometry args={[BOUNDARY_RADIUS - 0.5, BOUNDARY_RADIUS, 64]} />
        <meshBasicMaterial color="#ffffff" opacity={0.5} transparent />
      </mesh>

      {/* Ground texture */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -0.1]}>
        <circleGeometry args={[BOUNDARY_RADIUS * 1.5, 64]} />
        <meshLambertMaterial color="#90EE90" />
      </mesh>

      {/* Umpire position markers */}
      <mesh position={[-2, -8, 0.05]}>
        <cylinderGeometry args={[0.1, 0.1, 0.02]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
      <Text position={[-2, -8, 0.1]} fontSize={0.3} color="#ffffff" anchorX="center" anchorY="middle">
        Umpire
      </Text>
    </group>
  );
};

const TrajectoryLine = ({ points, showPrediction = true }) => {
  const lineRef = useRef();

  useEffect(() => {
    if (lineRef.current && points && points.length > 0) {
      // Clear previous lines
      while (lineRef.current.children.length > 0) {
        lineRef.current.remove(lineRef.current.children[0]);
      }

      // Create trajectory points (convert from normalized coordinates to cricket pitch)
      const trajectoryPoints = points.map(point => {
        const pitchX = point.x * (PITCH_WIDTH / 2);
        const pitchY = point.y * (PITCH_LENGTH / 2);
        const pitchZ = point.z * 2;
        return new THREE.Vector3(pitchX, pitchY, pitchZ);
      });

      if (trajectoryPoints.length > 1) {
        // Actual trajectory (solid line)
        const geometry = new THREE.BufferGeometry().setFromPoints(trajectoryPoints);
        const material = new THREE.LineBasicMaterial({
          color: 0xff4444,
          linewidth: 4,
          transparent: true,
          opacity: 0.9
        });
        const line = new THREE.Line(geometry, material);
        lineRef.current.add(line);

        // Prediction line (dashed)
        if (showPrediction && trajectoryPoints.length > 2) {
          const lastPoint = trajectoryPoints[trajectoryPoints.length - 1];
          const secondLastPoint = trajectoryPoints[trajectoryPoints.length - 2];
          const direction = new THREE.Vector3()
            .subVectors(lastPoint, secondLastPoint)
            .normalize()
            .multiplyScalar(5); // Extend prediction line

          const predictionPoints = [
            lastPoint.clone(),
            new THREE.Vector3().addVectors(lastPoint, direction)
          ];

          const predGeometry = new THREE.BufferGeometry().setFromPoints(predictionPoints);
          const predMaterial = new THREE.LineDashedMaterial({
            color: 0xffff00,
            linewidth: 2,
            dashSize: 0.5,
            gapSize: 0.3,
            transparent: true,
            opacity: 0.7
          });
          const predLine = new THREE.Line(predGeometry, predMaterial);
          predLine.computeLineDistances();
          lineRef.current.add(predLine);
        }
      }
    }
  }, [points, showPrediction]);

  return <group ref={lineRef} />;
};

const Ball = ({ trajectoryData, currentTime, showTrail = true }) => {
  const meshRef = useRef();
  const trailRef = useRef();

  useFrame((state, delta) => {
    if (meshRef.current && trajectoryData && trajectoryData.points && trajectoryData.points.length > 0) {
      const points = trajectoryData.points;
      const timestamps = trajectoryData.timestamps || points.map((_, i) => i * 0.1);

      // Use currentTime from video instead of animation clock
      let targetIndex = 0;
      let minDiff = Math.abs(timestamps[0] - currentTime);

      for (let i = 1; i < timestamps.length; i++) {
        const diff = Math.abs(timestamps[i] - currentTime);
        if (diff < minDiff) {
          minDiff = diff;
          targetIndex = i;
        }
      }

      // Don't loop, just stay at the last point if we've reached the end
      if (targetIndex >= points.length) {
        targetIndex = points.length - 1;
      }

      const point = points[targetIndex];

      if (point) {
        // Convert normalized coordinates to cricket pitch coordinates
        const pitchX = point.x * (PITCH_WIDTH / 2);
        const pitchY = point.y * (PITCH_LENGTH / 2);
        const pitchZ = point.z * 2 + 0.2; // Ball height above ground

        meshRef.current.position.set(pitchX, pitchY, pitchZ);

        // Update ball trail
        if (showTrail && trailRef.current) {
          const trailPoints = [];
          const trailLength = Math.min(10, targetIndex + 1); // Show last 10 points

          for (let i = Math.max(0, targetIndex - trailLength + 1); i <= targetIndex; i++) {
            const trailPoint = points[i];
            const trailX = trailPoint.x * (PITCH_WIDTH / 2);
            const trailY = trailPoint.y * (PITCH_LENGTH / 2);
            const trailZ = trailPoint.z * 2 + 0.2;
            trailPoints.push(new THREE.Vector3(trailX, trailY, trailZ));
          }

          if (trailPoints.length > 1) {
            const geometry = new THREE.BufferGeometry().setFromPoints(trailPoints);
            const material = new THREE.LineBasicMaterial({
              color: 0xffaa00,
              transparent: true,
              opacity: 0.6
            });
            const trail = new THREE.Line(geometry, material);

            // Clear previous trail
            while (trailRef.current.children.length > 0) {
              trailRef.current.remove(trailRef.current.children[0]);
            }
            trailRef.current.add(trail);
          }
        }
      }
    }
  });

  return (
    <group>
      <mesh ref={meshRef}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshStandardMaterial
          color="#ff4444"
          emissive="#220000"
          emissiveIntensity={0.3}
          metalness={0.1}
          roughness={0.4}
        />
      </mesh>
      <group ref={trailRef} />
    </group>
  );
};

const CameraController = ({ currentView, onViewChange }) => {
  const { camera } = useThree();

  useEffect(() => {
    if (CAMERA_VIEWS[currentView]) {
      const view = CAMERA_VIEWS[currentView];
      camera.position.set(...view.position);
      camera.lookAt(...view.target);
    }
  }, [currentView, camera]);

  return null;
};

const TrajectoryViewer = ({ trajectoryData, videoData, currentTime = 0 }) => {
  const [currentView, setCurrentView] = useState('umpire');
  const [showDRS, setShowDRS] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (!trajectoryData || !trajectoryData.points || trajectoryData.points.length === 0) {
    return (
      <Box sx={{
        width: '100%',
        height: '600px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #4a7c59 0%, #90EE90 100%)',
        borderRadius: '10px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        position: 'relative'
      }}>
        <Box sx={{ textAlign: 'center', color: 'white' }}>
          <SportsCricket sx={{ fontSize: 60, mb: 2, opacity: 0.7 }} />
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
            DRS Ball Tracking System
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.8 }}>
            Upload a video to see 3D trajectory analysis
          </Typography>
        </Box>
      </Box>
    );
  }

  // Calculate impact point (last point in trajectory)
  const impactPoint = trajectoryData.points[trajectoryData.points.length - 1];
  const impactPosition = impactPoint ? [
    impactPoint.x * (PITCH_WIDTH / 2),
    impactPoint.y * (PITCH_LENGTH / 2),
    0.1
  ] : [0, 0, 0];

  // Determine if ball hits wicket zone
  const isWicketHit = impactPoint && Math.abs(impactPoint.x) < 0.1 && Math.abs(impactPoint.y - 0.5) < 0.1;

  // Get positions from trajectory data
  const stumpsPosition = trajectoryData.stumps_position ? trajectoryData.stumps_position.position_3d : null;
  const bowlerPosition = trajectoryData.bowler_position;
  const batterPosition = trajectoryData.batter_position;

  return (
    <Box sx={{
      width: '100%',
      height: isFullscreen ? '100vh' : { xs: '100%', md: '600px' },
      position: isFullscreen ? 'fixed' : 'relative',
      top: isFullscreen ? 0 : 'auto',
      left: isFullscreen ? 0 : 'auto',
      zIndex: isFullscreen ? 9999 : 'auto',
      background: isFullscreen ? 'black' : 'transparent',
      overflow: 'hidden'
    }}>
      {/* Control Panel */}
      <Paper sx={{
        position: isFullscreen ? 'absolute' : { xs: 'static', md: 'absolute' },
        top: isFullscreen ? 10 : { md: 10 },
        right: isFullscreen ? 10 : { md: 10 },
        left: isFullscreen ? 'auto' : { xs: 0, md: 'auto' },
        zIndex: 1000,
        p: 2,
        background: { xs: 'rgba(255, 255, 255, 0.95)', md: 'rgba(255, 255, 255, 0.9)' },
        borderRadius: 2,
        mb: isFullscreen ? 0 : { xs: 2, md: 0 },
        maxWidth: isFullscreen ? '300px' : { xs: '100%', md: '300px' }
      }}>
        <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', md: '0.9rem' } }}>
          DRS Controls
        </Typography>

        {/* Camera Views */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontSize: { xs: '0.9rem', md: '0.8rem' } }}>
            Camera View:
          </Typography>
          <ButtonGroup
            size="small"
            variant="outlined"
            orientation={window.innerWidth < 600 ? "vertical" : "horizontal"}
            sx={{
              width: '100%',
              '& .MuiButton-root': {
                fontSize: { xs: '0.75rem', md: '0.7rem' },
                px: { xs: 2, md: 1 },
                flex: { xs: 1, md: 'auto' }
              }
            }}
          >
            {Object.keys(CAMERA_VIEWS).map(view => (
              <Button
                key={view}
                variant={currentView === view ? 'contained' : 'outlined'}
                onClick={() => setCurrentView(view)}
              >
                {view.charAt(0).toUpperCase() + view.slice(1)}
              </Button>
            ))}
          </ButtonGroup>
        </Box>

        {/* DRS Options */}
        <Box sx={{ mb: 2 }}>
          <Button
            size="small"
            variant={showDRS ? 'contained' : 'outlined'}
            onClick={() => setShowDRS(!showDRS)}
            startIcon={<ViewInAr />}
            sx={{ fontSize: '0.7rem' }}
          >
            DRS Mode
          </Button>
        </Box>

        {/* Fullscreen Toggle */}
        <Box sx={{ mt: 2 }}>
          <Button
            variant="outlined"
            size="small"
            onClick={toggleFullscreen}
            startIcon={isFullscreen ? <FullscreenExit /> : <Fullscreen />}
            sx={{ fontSize: '0.7rem' }}
          >
            {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          </Button>
        </Box>
      </Paper>

      {/* Stats Panel */}
      <Paper sx={{
        position: isFullscreen ? 'absolute' : { xs: 'static', md: 'absolute' },
        bottom: isFullscreen ? 10 : { md: 10 },
        left: isFullscreen ? 10 : { xs: 0, md: 10 },
        right: isFullscreen ? 'auto' : { xs: 0, md: 'auto' },
        zIndex: 1000,
        p: 2,
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        borderRadius: 2,
        maxWidth: isFullscreen ? '300px' : { xs: '100%', md: '300px' },
        mt: isFullscreen ? 0 : { xs: 2, md: 0 }
      }}>
        <Typography variant="subtitle1" sx={{ fontSize: { xs: '1rem', md: '0.9rem' }, fontWeight: 'bold', mb: 1 }}>
          DRS Analysis Stats
        </Typography>
        <Grid container spacing={1} sx={{ mb: 1 }}>
          <Grid item xs={6} sm={6}>
            <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', md: '0.7rem' } }}>
              Ball Points: {trajectoryData.points.length}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={6}>
            <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', md: '0.7rem' } }}>
              Confidence: {trajectoryData.confidence_score ? (trajectoryData.confidence_score * 100).toFixed(1) : 'N/A'}%
            </Typography>
          </Grid>
          <Grid item xs={6} sm={6}>
            <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', md: '0.7rem' } }}>
              Stumps: {stumpsPosition ? 'Detected' : 'Not Found'}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={6}>
            <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', md: '0.7rem' } }}>
              Players: {bowlerPosition ? 'B' : ''}{batterPosition ? 'R' : ''}{(!bowlerPosition && !batterPosition) ? 'None' : ''}
            </Typography>
          </Grid>
        </Grid>

        {/* Debug Info */}
        {trajectoryData.debug_info && (
          <Box sx={{ borderTop: '1px solid rgba(255,255,255,0.3)', pt: 1, mt: 1 }}>
            <Typography variant="subtitle2" sx={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.7)' }}>
              Processed: {trajectoryData.debug_info.frames_processed} frames
            </Typography>
          </Box>
        )}
      </Paper>

      <Canvas
        camera={{ position: [0, -15, 10], fov: 60 }}
        style={{
          background: 'linear-gradient(135deg, #87CEEB 0%, #98FB98 100%)',
          width: '100%',
          height: isFullscreen ? '100vh' : '100%',
          borderRadius: isFullscreen ? 0 : '8px'
        }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[10, 10, 5]}
          angle={0.3}
          penumbra={1}
          intensity={1.2}
          castShadow
        />
        <pointLight position={[0, 0, 15]} intensity={0.5} />

        {/* Cricket pitch */}
        <CricketPitch showDRS={showDRS} />

        {/* Stumps */}
        {stumpsPosition && (
          <Wicket position={[stumpsPosition[0], stumpsPosition[1], stumpsPosition[2]]} />
        )}

        {/* Trajectory visualization */}
        <TrajectoryLine points={trajectoryData.points} showPrediction={showDRS} />
        <Ball trajectoryData={trajectoryData} currentTime={currentTime} showTrail={showDRS} />

        {/* Players */}
        <Bowler position={bowlerPosition} visible={showDRS} />
        <Batter position={batterPosition} visible={showDRS} />

        {/* DRS-specific elements */}
        {showDRS && (
          <>
            <ImpactZone position={impactPosition} isHit={isWicketHit} />
          </>
        )}

        {/* Camera Controller */}
        <CameraController currentView={currentView} />
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          maxPolarAngle={Math.PI / 2}
          minDistance={5}
          maxDistance={50}
        />
      </Canvas>
    </Box>
  );
};

export default TrajectoryViewer;
