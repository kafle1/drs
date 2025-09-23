import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography, IconButton, Tooltip, Chip, LinearProgress } from '@mui/material';
import { PlayArrow, Pause, Replay, Speed } from '../utils/icons';

const VideoPlayerWithTracking = ({ videoData, trajectoryData, onTimeUpdate }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showControls, setShowControls] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !trajectoryData || !trajectoryData.points) return;

    const ctx = canvas.getContext('2d');

    const drawTracking = () => {
      if (!trajectoryData.points || trajectoryData.points.length === 0) return;

      const videoWidth = video.videoWidth || 640;
      const videoHeight = video.videoHeight || 480;
      const canvasWidth = canvas.width;
      const canvasHeight = canvas.height;

      // Clear canvas
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);

      // Find the closest trajectory point to current time
      const timestamps = trajectoryData.timestamps || trajectoryData.points.map((_, i) => i * 0.1);
      let closestIndex = 0;
      let minDiff = Math.abs(timestamps[0] - currentTime);

      for (let i = 1; i < timestamps.length; i++) {
        const diff = Math.abs(timestamps[i] - currentTime);
        if (diff < minDiff) {
          minDiff = diff;
          closestIndex = i;
        }
      }

      if (closestIndex < trajectoryData.points.length) {
        const point = trajectoryData.points[closestIndex];

        // Convert normalized trajectory coordinates back to video pixel coordinates
        // Backend returns: x (-1 to 1, left to right), y (1 to -1, near to far)
        // For video overlay, we need pixel coordinates
        const videoX = (point.x + 1) * (videoWidth / 2);  // Convert -1,1 to 0,width
        const videoY = (1 - point.y) * (videoHeight / 2);  // Convert 1,-1 to 0,height

        // Draw ball tracking point with enhanced styling
        ctx.beginPath();
        ctx.arc(videoX, videoY, 10, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(255, 0, 0, 0.9)';
        ctx.fill();

        // Add glow effect
        ctx.shadowColor = 'red';
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(videoX, videoY, 8, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.fill();
        ctx.shadowBlur = 0;

        // Draw trajectory trail with gradient
        ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.beginPath();

        for (let i = Math.max(0, closestIndex - 15); i <= closestIndex; i++) {
          if (i >= trajectoryData.points.length) break;

          const trailPoint = trajectoryData.points[i];
          const trailX = (trailPoint.x + 1) * (videoWidth / 2);
          const trailY = (1 - trailPoint.y) * (videoHeight / 2);

          if (i === Math.max(0, closestIndex - 15)) {
            ctx.moveTo(trailX, trailY);
          } else {
            ctx.lineTo(trailX, trailY);
          }
        }
        ctx.stroke();

        // Draw prediction line for next few frames with better styling
        ctx.strokeStyle = 'rgba(255, 0, 0, 0.6)';
        ctx.setLineDash([8, 4]);
        ctx.lineWidth = 3;
        ctx.beginPath();

        const predictionPoints = 20;
        for (let i = 0; i < predictionPoints && (closestIndex + i) < trajectoryData.points.length; i++) {
          const predPoint = trajectoryData.points[closestIndex + i];
          const predX = (predPoint.x + 1) * (videoWidth / 2);
          const predY = (1 - predPoint.y) * (videoHeight / 2);

          if (i === 0) {
            ctx.moveTo(predX, predY);
          } else {
            ctx.lineTo(predX, predY);
          }
        }
        ctx.stroke();
        ctx.setLineDash([]);
      }
    };

    const handleTimeUpdate = () => {
      const newTime = video.currentTime;
      setCurrentTime(newTime);
      if (onTimeUpdate) {
        onTimeUpdate(newTime);
      }
      drawTracking();
    };

    const handleLoadedData = () => {
      setDuration(video.duration);
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
      setIsLoading(false);
      drawTracking();
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleError = () => {
      setError('Failed to load video. Please check the file and try again.');
      setIsLoading(false);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadeddata', handleLoadedData);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('error', handleError);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('error', handleError);
    };
  }, [trajectoryData, currentTime, onTimeUpdate]);

  if (!videoData) {
    return (
      <Box sx={{ textAlign: 'center', py: 4, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            🎥 No Video Loaded
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Upload a video to start ball tracking analysis
          </Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 4, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box>
          <Typography variant="h6" color="error" gutterBottom>
            ⚠️ Video Loading Error
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {error}
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: '100%',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(false)}
    >
      {/* Loading Overlay */}
      {isLoading && (
        <Box sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10
        }}>
          <Box sx={{ textAlign: 'center', color: 'white' }}>
            <Typography variant="h6" gutterBottom>
              🔄 Loading Video...
            </Typography>
            <LinearProgress sx={{ width: 200, mt: 2 }} />
          </Box>
        </Box>
      )}

      {/* Video Element */}
      <video
        ref={videoRef}
        controls={false}
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '12px',
          objectFit: 'contain'
        }}
        src={`http://localhost:8000/uploads/${encodeURIComponent(videoData.filename)}`}
        onError={() => setError('Failed to load video file')}
      >
        Your browser does not support the video tag.
      </video>

      {/* Canvas Overlay */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          pointerEvents: 'none',
          borderRadius: '12px'
        }}
      />

      {/* Enhanced Controls */}
      {showControls && !isLoading && (
        <Box sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'linear-gradient(transparent, rgba(0,0,0,0.8))',
          padding: '20px 16px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}>
          <IconButton
            onClick={() => {
              const video = videoRef.current;
              if (video) {
                if (isPlaying) {
                  video.pause();
                } else {
                  video.play();
                }
              }
            }}
            sx={{ color: 'white' }}
          >
            {isPlaying ? <Pause /> : <PlayArrow />}
          </IconButton>

          <IconButton
            onClick={() => {
              const video = videoRef.current;
              if (video) {
                video.currentTime = 0;
                setCurrentTime(0);
              }
            }}
            sx={{ color: 'white' }}
          >
            <Replay />
          </IconButton>

          <Box sx={{ flex: 1, mx: 2 }}>
            <LinearProgress
              variant="determinate"
              value={(currentTime / duration) * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(255,255,255,0.3)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: '#ff4444',
                  borderRadius: 4
                }
              }}
            />
            {/* Time markers for trajectory points */}
            {trajectoryData && trajectoryData.points && trajectoryData.points.map((point, index) => {
              const pointTime = point.t;
              const position = (pointTime / duration) * 100;
              return (
                <Box
                  key={index}
                  sx={{
                    position: 'absolute',
                    left: `${position}%`,
                    top: -2,
                    width: 4,
                    height: 12,
                    backgroundColor: '#ffff00',
                    borderRadius: 1,
                    transform: 'translateX(-50%)',
                    opacity: 0.8
                  }}
                />
              );
            })}
          </Box>

          <Typography variant="body2" sx={{ color: 'white', minWidth: 80 }}>
            {Math.floor(currentTime / 60)}:{(currentTime % 60).toFixed(0).padStart(2, '0')} / {Math.floor(duration / 60)}:{(duration % 60).toFixed(0).padStart(2, '0')}
          </Typography>

          <Tooltip title="Playback Speed">
            <IconButton
              onClick={() => {
                const video = videoRef.current;
                const newRate = playbackRate >= 2 ? 0.5 : playbackRate + 0.25;
                setPlaybackRate(newRate);
                if (video) video.playbackRate = newRate;
              }}
              sx={{ color: 'white' }}
            >
              <Speed />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      {/* Enhanced Status Overlay */}
      {trajectoryData && (
        <Box sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          background: 'rgba(0,0,0,0.8)',
          backdropFilter: 'blur(10px)',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.1)',
          minWidth: 200
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
              🎯 Ball Tracking Active
            </Typography>
            <Chip
              label={`${(trajectoryData.confidence_score * 100).toFixed(1)}%`}
              size="small"
              sx={{
                backgroundColor: trajectoryData.confidence_score > 0.8 ? 'success.main' : 'warning.main',
                color: 'white',
                fontSize: '0.7rem'
              }}
            />
          </Box>
          <Typography variant="caption" sx={{ display: 'block', opacity: 0.8 }}>
            Time: {currentTime.toFixed(2)}s / {duration.toFixed(2)}s
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', opacity: 0.8 }}>
            Points: {trajectoryData.points?.length || 0} | Speed: {playbackRate}x
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', opacity: 0.8 }}>
            Status: {isPlaying ? 'Playing' : 'Paused'}
          </Typography>
        </Box>
      )}

      {/* Playback Rate Indicator */}
      {playbackRate !== 1 && (
        <Box sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          background: 'rgba(255, 0, 0, 0.9)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '6px',
          fontSize: '0.8rem',
          fontWeight: 'bold'
        }}>
          {playbackRate}x
        </Box>
      )}
    </Box>
  );
};

export default VideoPlayerWithTracking;
