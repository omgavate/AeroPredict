// AeroPredict API Client Configuration
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Response Interceptor for uniform data unpacking & structured error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Preserve response error details from Flask
    if (error.response && error.response.data) {
      const serverError = new Error(error.response.data.message || error.response.data.error || 'Server error');
      serverError.status = error.response.status;
      serverError.details = error.response.data.details || {};
      return Promise.reject(serverError);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
