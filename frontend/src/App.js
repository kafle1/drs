import React, { useState } from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';
import VideoUpload from './components/VideoUpload';
import TrajectoryViewer from './components/TrajectoryViewer';
import ReviewInterface from './components/ReviewInterface';

function App() {
  const [uploadedVideo, setUploadedVideo] = useState(null);
  const [trajectoryData, setTrajectoryData] = useState(null);
  const [tracking, setTracking] = useState(false);

  const handleVideoUploaded = async (videoData) => {
    setUploadedVideo(videoData);

    // Start tracking automatically
    setTracking(true);
    try {
      const response = await fetch(`/videos/${videoData.id}/track`, {
        method: 'POST',
      });

      if (response.ok) {
        // Wait a bit then fetch trajectory
        setTimeout(async () => {
          const trajectoryResponse = await fetch(`/videos/${videoData.id}/trajectory`);
          if (trajectoryResponse.ok) {
            const data = await trajectoryResponse.json();
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

  const handleReviewComplete = (reviewData) => {
    console.log('Review completed:', reviewData);
    // Could show success message or redirect
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        DRS Ball Tracking System
      </Typography>
      <Typography variant="subtitle1" align="center" color="textSecondary" sx={{ mb: 4 }}>
        Upload videos, track ball trajectories, and make accurate decisions
      </Typography>

      {/* Video Upload Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <VideoUpload onVideoUploaded={handleVideoUploaded} />
      </Paper>

      {/* Trajectory Viewer */}
      {uploadedVideo && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Ball Trajectory Analysis
          </Typography>
          {tracking ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography>Processing video and tracking ball...</Typography>
            </Box>
          ) : (
            <TrajectoryViewer trajectoryData={trajectoryData} />
          )}
        </Paper>
      )}

      {/* Review Interface */}
      {uploadedVideo && trajectoryData && (
        <ReviewInterface
          videoId={uploadedVideo.id}
          onReviewComplete={handleReviewComplete}
        />
      )}
    </Container>
  );
}

export default App;
