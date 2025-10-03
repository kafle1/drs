import React, { useState } from 'react';
import { Button, Box, Typography, LinearProgress, Alert } from '@mui/material';
import api, { MAX_UPLOAD_SIZE_MB } from '../api/client';

const ALLOWED_FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'webm'];

const VideoUpload = ({ onVideoUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setError(null);

    // Validate file type
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_FORMATS.includes(fileExt)) {
      setError(`Invalid file format. Supported: ${ALLOWED_FORMATS.join(', ').toUpperCase()}`);
      return;
    }

    // Validate file size
    const maxSize = MAX_UPLOAD_SIZE_MB * 1024 * 1024;
    if (file.size > maxSize) {
      setError(`File size must be less than ${MAX_UPLOAD_SIZE_MB}MB`);
      return;
    }

    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/videos/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });

      onVideoUploaded(response.data);
    } catch (error) {
      console.error('Upload failed:', error);
      const errorMsg = error.response?.data?.detail || 'Upload failed. Please try again.';
      setError(errorMsg);
    } finally {
      setUploading(false);
      setProgress(0);
      // Reset file input
      event.target.value = '';
    }
  };

  return (
    <Box sx={{ p: 2, border: '2px dashed #ccc', borderRadius: 2, textAlign: 'center' }}>
      <Typography variant="h6" gutterBottom>
        Upload Video for Ball Tracking
      </Typography>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        Supported formats: {ALLOWED_FORMATS.join(', ').toUpperCase()} (max {MAX_UPLOAD_SIZE_MB}MB)
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

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
