import React, { useState, useEffect } from 'react';
import {
  Box, Button, Typography, Paper, List, ListItem, ListItemText,
  TextField, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import axios from 'axios';

const DECISION_TYPES = ['lbw', 'run_out', 'caught', 'other'];
const OUTCOMES = ['out', 'not_out', 'no_ball', 'wide'];

const ReviewInterface = ({ videoId, onReviewComplete }) => {
  const [decisions, setDecisions] = useState([]);
  const [notes, setNotes] = useState('');
  const [currentDecision, setCurrentDecision] = useState({
    type: '',
    outcome: '',
    timestamp: 0,
    confidence: 0.5
  });
  const [trajectoryData, setTrajectoryData] = useState(null);

  useEffect(() => {
    if (videoId) {
      fetchTrajectory();
    }
  }, [videoId]);

  const fetchTrajectory = async () => {
    try {
      const response = await axios.get(`/videos/${videoId}/trajectory`);
      setTrajectoryData(response.data);
    } catch (error) {
      console.error('Failed to fetch trajectory:', error);
    }
  };

  const addDecision = () => {
    if (currentDecision.type && currentDecision.outcome) {
      setDecisions([...decisions, { ...currentDecision }]);
      setCurrentDecision({
        type: '',
        outcome: '',
        timestamp: 0,
        confidence: 0.5
      });
    }
  };

  const removeDecision = (index) => {
    setDecisions(decisions.filter((_, i) => i !== index));
  };

  const submitReview = async () => {
    try {
      const response = await axios.post('/reviews', {
        video_id: videoId,
        decisions,
        notes
      });
      onReviewComplete(response.data);
      alert('Review submitted successfully!');
    } catch (error) {
      console.error('Failed to submit review:', error);
      alert('Failed to submit review. Please try again.');
    }
  };

  return (
    <Paper sx={{ p: 3, mt: 2 }}>
      <Typography variant="h6" gutterBottom>
        Review Decisions
      </Typography>

      {/* Add Decision Form */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Add Decision
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={currentDecision.type}
              label="Type"
              onChange={(e) => setCurrentDecision({ ...currentDecision, type: e.target.value })}
            >
              {DECISION_TYPES.map(type => (
                <MenuItem key={type} value={type}>{type.toUpperCase()}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Outcome</InputLabel>
            <Select
              value={currentDecision.outcome}
              label="Outcome"
              onChange={(e) => setCurrentDecision({ ...currentDecision, outcome: e.target.value })}
            >
              {OUTCOMES.map(outcome => (
                <MenuItem key={outcome} value={outcome}>{outcome.replace('_', ' ').toUpperCase()}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Timestamp (s)"
            type="number"
            value={currentDecision.timestamp}
            onChange={(e) => setCurrentDecision({ ...currentDecision, timestamp: parseFloat(e.target.value) || 0 })}
            sx={{ minWidth: 120 }}
          />

          <TextField
            label="Confidence"
            type="number"
            inputProps={{ min: 0, max: 1, step: 0.1 }}
            value={currentDecision.confidence}
            onChange={(e) => setCurrentDecision({ ...currentDecision, confidence: parseFloat(e.target.value) || 0.5 })}
            sx={{ minWidth: 120 }}
          />

          <Button variant="outlined" onClick={addDecision}>
            Add Decision
          </Button>
        </Box>
      </Box>

      {/* Decisions List */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Decisions ({decisions.length})
        </Typography>
        <List>
          {decisions.map((decision, index) => (
            <ListItem key={index} secondaryAction={
              <Button size="small" color="error" onClick={() => removeDecision(index)}>
                Remove
              </Button>
            }>
              <ListItemText
                primary={`${decision.type.toUpperCase()} - ${decision.outcome.toUpperCase()}`}
                secondary={`Time: ${decision.timestamp}s, Confidence: ${(decision.confidence * 100).toFixed(0)}%`}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Notes */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Review Notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add any additional notes about the review..."
        />
      </Box>

      {/* Submit */}
      <Box sx={{ textAlign: 'right' }}>
        <Button
          variant="contained"
          onClick={submitReview}
          disabled={decisions.length === 0}
        >
          Submit Review
        </Button>
      </Box>
    </Paper>
  );
};

export default ReviewInterface;
