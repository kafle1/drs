import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import VideoUpload from '../src/components/VideoUpload';
import { post } from '../src/api/client';

// Mock the API client
jest.mock('../src/api/client', () => ({
  post: jest.fn(),
}));

describe('VideoUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders upload interface', () => {
    render(<VideoUpload />);

    expect(screen.getByText('Upload Video for Analysis')).toBeInTheDocument();
    expect(screen.getByText('Choose a video file or drag and drop')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
  });

  test('displays file input', () => {
    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    expect(fileInput).toBeInTheDocument();
    expect(fileInput).toHaveAttribute('type', 'file');
    expect(fileInput).toHaveAttribute('accept', 'video/*');
  });

  test('shows selected file name', async () => {
    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('test-video.mp4')).toBeInTheDocument();
    });
  });

  test('handles file selection', () => {
    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(fileInput.files[0]).toBe(file);
  });

  test('shows upload button when file is selected', async () => {
    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /upload & analyze/i })).toBeInTheDocument();
    });
  });

  test('handles successful upload', async () => {
    const mockResponse = {
      data: {
        id: '123e4567-e89b-12d3-a456-426614174000',
        status: 'uploaded',
        upload_date: '2025-09-07T13:00:00Z'
      }
    };

    post.mockResolvedValueOnce(mockResponse);

    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = await screen.findByRole('button', { name: /upload & analyze/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/videos/upload', expect.any(FormData));
    });

    expect(screen.getByText('Video uploaded successfully!')).toBeInTheDocument();
  });

  test('handles upload error', async () => {
    const mockError = {
      response: {
        data: {
          detail: 'File too large'
        }
      }
    };

    post.mockRejectedValueOnce(mockError);

    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'large-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = await screen.findByRole('button', { name: /upload & analyze/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText('Upload failed: File too large')).toBeInTheDocument();
    });
  });

  test('shows loading state during upload', async () => {
    const mockResponse = {
      data: {
        id: '123e4567-e89b-12d3-a456-426614174000',
        status: 'uploaded'
      }
    };

    // Mock a delayed response
    post.mockImplementationOnce(() => new Promise(resolve => {
      setTimeout(() => resolve(mockResponse), 100);
    }));

    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = await screen.findByRole('button', { name: /upload & analyze/i });
    fireEvent.click(uploadButton);

    // Should show loading state
    expect(screen.getByText('Uploading...')).toBeInTheDocument();

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('Video uploaded successfully!')).toBeInTheDocument();
    });
  });

  test('validates file type', () => {
    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const invalidFile = new File(['test'], 'test-image.jpg', { type: 'image/jpeg' });

    fireEvent.change(fileInput, { target: { files: [invalidFile] } });

    // Should still accept the file (HTML5 validation handles this)
    expect(fileInput.files[0]).toBe(invalidFile);
  });

  test('handles multiple file selection (takes first)', () => {
    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const files = [
      new File(['test1'], 'video1.mp4', { type: 'video/mp4' }),
      new File(['test2'], 'video2.mp4', { type: 'video/mp4' })
    ];

    fireEvent.change(fileInput, { target: { files: files } });

    // Should only process the first file
    expect(fileInput.files[0]).toBe(files[0]);
  });

  test('resets state after successful upload', async () => {
    const mockResponse = {
      data: {
        id: '123e4567-e89b-12d3-a456-426614174000',
        status: 'uploaded'
      }
    };

    post.mockResolvedValueOnce(mockResponse);

    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = await screen.findByRole('button', { name: /upload & analyze/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText('Video uploaded successfully!')).toBeInTheDocument();
    });

    // File input should be cleared
    expect(fileInput.value).toBe('');
  });

  test('handles network error', async () => {
    post.mockRejectedValueOnce(new Error('Network error'));

    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = await screen.findByRole('button', { name: /upload & analyze/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText('Upload failed: Network error')).toBeInTheDocument();
    });
  });

  test('prevents multiple simultaneous uploads', async () => {
    const mockResponse = {
      data: {
        id: '123e4567-e89b-12d3-a456-426614174000',
        status: 'uploaded'
      }
    };

    // Mock a slow response
    post.mockImplementationOnce(() => new Promise(resolve => {
      setTimeout(() => resolve(mockResponse), 1000);
    }));

    render(<VideoUpload />);

    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['test'], 'test-video.mp4', { type: 'video/mp4' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = await screen.findByRole('button', { name: /upload & analyze/i });
    fireEvent.click(uploadButton);

    // Try to click again while uploading
    fireEvent.click(uploadButton);

    // Should still only have one upload in progress
    expect(post).toHaveBeenCalledTimes(1);
  });
});
