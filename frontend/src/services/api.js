import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Create axios instance without default Content-Type
const api = axios.create({
  baseURL: API_BASE_URL,
});

const clearAuthStorage = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('userId');
};

const persistAuthTokens = (payload) => {
  if (payload?.access_token) {
    localStorage.setItem('accessToken', payload.access_token);
  }
  if (payload?.refresh_token) {
    localStorage.setItem('refreshToken', payload.refresh_token);
  }
  if (payload?.user_id) {
    localStorage.setItem('userId', String(payload.user_id));
  }
};

const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
    refresh_token: refreshToken,
  });

  persistAuthTokens(response.data);
  return response.data.access_token;
};

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use((response) => response, async (error) => {
  const originalRequest = error?.config;
  const status = error?.response?.status;

  if (status !== 401 || !originalRequest || originalRequest._retry) {
    return Promise.reject(error);
  }

  if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/auth/logout')) {
    clearAuthStorage();
    return Promise.reject(error);
  }

  try {
    originalRequest._retry = true;
    const newAccessToken = await refreshAccessToken();
    originalRequest.headers = originalRequest.headers || {};
    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
    return api(originalRequest);
  } catch (refreshError) {
    clearAuthStorage();
    return Promise.reject(refreshError);
  }
});

// User APIs
export const createUser = async (name, email, password) => {
  return api.post('/auth/register', { name, email, password });
};

export const confirmEmailVerification = async (verificationToken) => {
  return api.post('/auth/verify-email', {
    verification_token: verificationToken,
  });
};

export const resendEmailVerification = async (email) => {
  return api.post('/auth/resend-verification', { email });
};

export const loginUser = async (email, password) => {
  const formData = new FormData();
  formData.append('email', email);
  formData.append('password', password);
  const response = await api.post('/auth/login', formData);
  persistAuthTokens(response.data);
  return response;
};

export const requestPasswordReset = async (email) => {
  return api.post('/auth/password-reset/request', { email });
};

export const confirmPasswordReset = async (resetToken, newPassword) => {
  return api.post('/auth/password-reset/confirm', {
    reset_token: resetToken,
    new_password: newPassword,
  });
};

export const logoutUser = async () => {
  const refreshToken = localStorage.getItem('refreshToken');
  try {
    if (refreshToken) {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    }
  } finally {
    clearAuthStorage();
  }
};

export const getAuthSessions = async () => {
  return api.get('/auth/sessions');
};

export const revokeAuthSession = async (jti) => {
  return api.delete(`/auth/sessions/${jti}`);
};

export const logoutAllDevices = async () => {
  try {
    const response = await api.post('/auth/logout-all');
    return response;
  } finally {
    clearAuthStorage();
  }
};

export const analyzeUser = async (userId, image, height, weight) => {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('height', height);
  formData.append('weight', weight);
  return api.post(`/users/${userId}/analyze`, formData);
};

export const getUser = async (userId) => {
  return api.get(`/users/${userId}`);
};

// Wardrobe APIs
export const addWardrobeItem = async (userId, image, category, season) => {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('category', category);
  formData.append('season', season || 'all');
  return api.post(`/users/${userId}/wardrobe/add`, formData);
};

export const getWardrobe = async (userId) => {
  return api.get(`/users/${userId}/wardrobe`);
};

export const deleteWardrobeItem = async (userId, itemId) => {
  return api.delete(`/users/${userId}/wardrobe/${itemId}`);
};

// Outfit APIs
export const getOutfitRecommendations = async (userId, limit = 10) => {
  return api.get(`/users/${userId}/outfits/recommend?limit=${limit}`);
};

// Discard APIs
export const getDiscardRecommendations = async (userId) => {
  return api.get(`/users/${userId}/wardrobe/discard-recommendations`);
};

// Shopping APIs
export const analyzeShoppingItem = async (userId, image) => {
  const formData = new FormData();
  formData.append('image', image);
  return api.post(`/users/${userId}/shopping/analyze`, formData);
};

// Feedback & Learning APIs
export const rateOutfit = async (userId, outfitId, rating, comment = null) => {
  return api.post(`/users/${userId}/outfits/${outfitId}/rate`, {
    rating,
    comment
  });
};

export const feedbackRecommendation = async (userId, recType, recId, helpful) => {
  return api.post(`/users/${userId}/recommendations/${recType}/${recId}/feedback`, {
    helpful
  });
};

export const trackItemUsage = async (userId, itemId, action, wearCount = 1) => {
  return api.post(`/users/${userId}/wardrobe/${itemId}/usage`, {
    action,
    wear_count: wearCount
  });
};

export default api;