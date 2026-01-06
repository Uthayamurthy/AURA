import axios from 'axios';

const STORAGE_KEY_URL = 'aura_server_url';

// Helper to get the full API URL
export const getBaseUrl = () => {
    let url = localStorage.getItem(STORAGE_KEY_URL);
    
    // If no URL is set, default to local dev URL or relative path
    if (!url) return 'http://localhost:8000/api/v1';

    // Remove trailing slash if user added it
    url = url.replace(/\/$/, '');

    // Append /api/v1 if not present (prevents duplication if user typed it)
    if (!url.endsWith('/api/v1')) {
        url += '/api/v1';
    }
    return url;
};

// Named export (for imports like: import { api } from ...)
export const api = axios.create({
    baseURL: getBaseUrl(),
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('aura_prof_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Update baseURL dynamically in case it changed in localStorage
    config.baseURL = getBaseUrl();
    
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('aura_prof_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Default export (for imports like: import api from ...)
export default api;