import React, { useState } from 'react';
import { Container, Typography, Box, Paper, Alert, CircularProgress } from '@mui/material';
import VideoUpload from './components/VideoUpload';
import VideoPlayerWithTracking from './components/VideoPlayerWithTracking';
import TrajectoryViewer from './components/TrajectoryViewer';
import api from './api/client';

function App() {
  const [uploadedVideo, setUploadedVideo] = useState(null);
  const [trajectoryData, setTrajectoryData] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [error, setError] = useState(null);
  const [processingStatus, setProcessingStatus] = useState('');

  const handleVideoUploaded = async (videoData) => {
    setUploadedVideo(videoData);
    setTrajectoryData(null);
    setError(null);
    setTracking(true);
    setProcessingStatus('Starting ball tracking analysis...');

    try {
      // Start tracking
      const trackResponse = await api.post(`/videos/${videoData.id}/track`);
      
      if (trackResponse.status === 200) {
        const trackData = trackResponse.data;
        
        // Check if already processed or still processing
        if (trackData.status === 'processed' || trackData.ball_detected !== undefined) {
          setProcessingStatus('Fetching trajectory data...');
          
          // Fetch trajectory immediately if already processed
          try {
            const trajectoryResponse = await api.get(`/videos/${videoData.id}/trajectory`);
            if (trajectoryResponse.status === 200) {
              setTrajectoryData(trajectoryResponse.data);
              setProcessingStatus('');
            }
          } catch (trajError) {
            console.error('Failed to fetch trajectory:', trajError);
            setError('Failed to fetch trajectory data. Please try again.');
          }
          setTracking(false);
        } else {
          // Still processing - poll for results
          setProcessingStatus('Processing video... This may take a minute.');
          pollForTrajectory(videoData.id);
        }
      }
    } catch (error) {
      console.error('Tracking failed:', error);
      const errorMsg = error.response?.data?.detail || 'Tracking failed. Please try again.';
      setError(errorMsg);
      setTracking(false);
      setProcessingStatus('');
    }
  };

  const pollForTrajectory = async (videoId, attempts = 0) => {
    const maxAttempts = 30; // Poll for up to 30 seconds
    
    if (attempts >= maxAttempts) {
      setError('Processing timeout. Please refresh and try again.');
      setTracking(false);
      setProcessingStatus('');
      return;
    }

    try {
      const trajectoryResponse = await api.get(`/videos/${videoId}/trajectory`);
      if (trajectoryResponse.status === 200) {
        setTrajectoryData(trajectoryResponse.data);
        setTracking(false);
        setProcessingStatus('');
      }
    } catch (error) {
      // If trajectory not ready yet, try again
      if (error.response?.status === 404) {
        setTimeout(() => pollForTrajectory(videoId, attempts + 1), 1000);
      } else {
        setError('Failed to retrieve trajectory data.');
        setTracking(false);
        setProcessingStatus('');
      }
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

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Video Upload Section */}
      <Paper sx={{ p: { xs: 2, md: 3 }, mb: 3 }}>
        <VideoUpload onVideoUploaded={handleVideoUploaded} />
      </Paper>

      {/* Processing Status */}
      {tracking && processingStatus && (
        <Alert severity="info" sx={{ mb: 3 }} icon={<CircularProgress size={20} />}>
          {processingStatus}
        </Alert>
      )}

      {/* Video and Trajectory Section */}
      {uploadedVideo && (
        <Box sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: 2,
          mb: 3,
          minHeight: { xs: 'auto', md: '600px' }
        }}>
          {/* Left side: Video with ball tracking overlay */}
          <Paper sx={{
            flex: 1,
            p: { xs: 1, md: 2 },
            display: 'flex',
            flexDirection: 'column',
            minHeight: { xs: '400px', md: 'auto' }
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
              {!tracking && uploadedVideo ? (
                <VideoPlayerWithTracking
                  videoData={uploadedVideo}
                  trajectoryData={trajectoryData}
                  onTimeUpdate={setCurrentTime}
                />
              ) : (
                <Box sx={{ textAlign: 'center' }}>
                  <CircularProgress size={60} sx={{ mb: 2 }} />
                  <Typography variant="body1" color="textSecondary">
                    Processing video...
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>

          {/* Right side: 3D Cricket pitch visualization */}
          <Paper sx={{
            flex: 1,
            p: { xs: 1, md: 2 },
            display: 'flex',
            flexDirection: 'column',
            minHeight: { xs: '500px', md: 'auto' }
          }}>
            <Typography variant="h6" gutterBottom sx={{ textAlign: 'center', mb: 2, fontSize: { xs: '1rem', md: '1.25rem' } }}>
              🏏 3D Cricket Pitch Analysis
            </Typography>
            <Box sx={{
              flex: 1,
              overflow: 'hidden',
              borderRadius: '8px'
            }}>
              {!tracking && trajectoryData ? (
                <TrajectoryViewer
                  trajectoryData={trajectoryData}
                  videoData={uploadedVideo}
                  currentTime={currentTime}
                />
              ) : (
                <Box sx={{
                  textAlign: 'center',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column'
                }}>
                  <CircularProgress size={40} sx={{ mb: 2 }} />
                  <Typography variant="body2" color="textSecondary">
                    Generating 3D visualization...
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Box>
      )}
    </Container>
  );
}

export default App;
