import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const MAX_UPLOAD_SIZE_MB = parseInt(process.env.REACT_APP_MAX_UPLOAD_SIZE_MB || '500');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes for video processing
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Don't set Content-Type for FormData (let browser set it with boundary)
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only redirect to login if we have auth routes
      // localStorage.removeItem('token');
      // window.location.href = '/login';
      console.warn('Authentication required');
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (email, name, password) => api.post('/auth/register', { email, name, password }),
  getMe: () => api.get('/auth/me'),
};

export const videosAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  track: (videoId) => api.post(`/videos/${videoId}/track`),
  getTrajectory: (videoId) => api.get(`/videos/${videoId}/trajectory`),
};

export const reviewsAPI = {
  create: (reviewData) => api.post('/reviews', reviewData),
  get: (reviewId) => api.get(`/reviews/${reviewId}`),
};

export { API_BASE_URL, MAX_UPLOAD_SIZE_MB };
export default api;
