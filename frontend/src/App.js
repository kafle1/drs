import React, { useState } from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';
import VideoUpload from './components/VideoUpload';
import VideoPlayerWithTracking from './components/VideoPlayerWithTracking';
import TrajectoryViewer from './components/TrajectoryViewer';
import api from './api/client';

function App() {
  const [uploadedVideo, setUploadedVideo] = useState(null);
  const [trajectoryData, setTrajectoryData] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const handleVideoUploaded = async (videoData) => {
    setUploadedVideo(videoData);

    // Start tracking automatically
    setTracking(true);
    try {
      const response = await api.post(`/videos/${videoData.id}/track`);

      if (response.status === 200) {
        // Wait a bit then fetch trajectory
        setTimeout(async () => {
          const trajectoryResponse = await api.get(`/videos/${videoData.id}/trajectory`);
          if (trajectoryResponse.status === 200) {
            const data = trajectoryResponse.data;
            setTrajectoryData(data);
          }
          setTracking(false);
        }, 2000); // Simulate processing time
      }
    } catch (error) {
      console.error('Tracking failed:', error);
      setTracking(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 2, md: 4 }, px: { xs: 2, md: 3 } }}>
      <Typography variant="h3" component="h1" gutterBottom align="center" sx={{ fontSize: { xs: '1.75rem', md: '3rem' } }}>
        DRS Ball Tracking System
      </Typography>
      <Typography variant="subtitle1" align="center" color="textSecondary" sx={{ mb: 4, fontSize: { xs: '0.9rem', md: '1rem' } }}>
        Upload videos, track ball trajectories, and make accurate decisions
      </Typography>

      {/* Video Upload Section */}
      <Paper sx={{ p: { xs: 2, md: 3 }, mb: 3 }}>
        <VideoUpload onVideoUploaded={handleVideoUploaded} />
      </Paper>

      {/* Video and Trajectory Section */}
      {uploadedVideo && (
        <Box sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: 2,
          mb: 3,
          minHeight: { xs: 'auto', md: '600px' },
          height: { xs: 'auto', md: '600px' }
        }}>
          {/* Left side: Video with ball tracking overlay */}
          <Paper sx={{
            flex: 1,
            p: { xs: 1, md: 2 },
            display: 'flex',
            flexDirection: 'column',
            minHeight: { xs: '400px', md: 'auto' },
            height: { xs: '400px', md: 'auto' }
          }}>
            <Typography variant="h6" gutterBottom sx={{ textAlign: 'center', mb: 2, fontSize: { xs: '1rem', md: '1.25rem' } }}>
              🎥 Video with Ball Tracking
            </Typography>
            <Box sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden'
            }}>
              {tracking ? (
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ mb: 2, fontSize: { xs: '1.25rem', md: '1.5rem' } }}>🔄 Processing video...</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Analyzing ball trajectory and detecting wickets
                  </Typography>
                </Box>
              ) : (
                <VideoPlayerWithTracking
                  videoData={uploadedVideo}
                  trajectoryData={trajectoryData}
                  onTimeUpdate={setCurrentTime}
                />
              )}
            </Box>
          </Paper>

          {/* Right side: 3D Cricket pitch visualization */}
          <Paper sx={{
            flex: 1,
            p: { xs: 1, md: 2 },
            display: 'flex',
            flexDirection: 'column',
            minHeight: { xs: '500px', md: 'auto' },
            height: { xs: '500px', md: 'auto' }
          }}>
            <Typography variant="h6" gutterBottom sx={{ textAlign: 'center', mb: 2, fontSize: { xs: '1rem', md: '1.25rem' } }}>
              🏏 3D Cricket Pitch Analysis
            </Typography>
            <Box sx={{
              flex: 1,
              overflow: 'hidden',
              borderRadius: '8px'
            }}>
              {tracking ? (
                <Box sx={{
                  textAlign: 'center',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Typography>🔄 Generating 3D visualization...</Typography>
                </Box>
              ) : (
                <TrajectoryViewer
                  trajectoryData={trajectoryData}
                  videoData={uploadedVideo}
                  currentTime={currentTime}
                />
              )}
            </Box>
          </Paper>
        </Box>
      )}

      {/* Review Interface */}
      {/* Removed Review Decisions section as requested */}
    </Container>
  );
}

export default App;
