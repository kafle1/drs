import React, { useState } from 'react';
import { Button, Box, Typography, LinearProgress } from '@mui/material';
import axios from 'axios';

const VideoUpload = ({ onVideoUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.name.match(/\.(mp4|mov|avi)$/i)) {
      alert('Please select a valid video file (MP4, MOV, AVI)');
      return;
    }

    // Validate file size (500MB)
    if (file.size > 500 * 1024 * 1024) {
      alert('File size must be less than 500MB');
      return;
    }

    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/videos/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });

      onVideoUploaded(response.data);
      alert('Video uploaded successfully!');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <Box sx={{ p: 2, border: '2px dashed #ccc', borderRadius: 2, textAlign: 'center' }}>
      <Typography variant="h6" gutterBottom>
        Upload Video for Ball Tracking
      </Typography>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        Supported formats: MP4, MOV, AVI (max 500MB)
      </Typography>

      <input
        accept="video/*"
        style={{ display: 'none' }}
        id="video-upload"
        type="file"
        onChange={handleFileSelect}
        disabled={uploading}
      />
      <label htmlFor="video-upload">
        <Button
          variant="contained"
          component="span"
          disabled={uploading}
          sx={{ mt: 2 }}
        >
          {uploading ? 'Uploading...' : 'Choose Video File'}
        </Button>
      </label>

      {uploading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Typography variant="body2" sx={{ mt: 1 }}>
            {progress}% uploaded
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default VideoUpload;
