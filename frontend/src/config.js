const API_BASE_URL = 'http://localhost:5000/api';

export const API_ENDPOINTS = {
  LEADS: `${API_BASE_URL}/leads`,
  TOOLS: `${API_BASE_URL}/tools`,
  CONVERT: `${API_BASE_URL}/convert`,
  STATUS: `${API_BASE_URL}/status`,
  HEALTH: `${API_BASE_URL}/health`
};

export default {
  API_BASE_URL,
  ...API_ENDPOINTS
};
