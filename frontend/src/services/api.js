import { API_ENDPOINTS } from '../config';

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Something went wrong');
  }
  return response.json();
};

export const apiService = {
  // Fetch leads data
  getLeads: async () => {
    const response = await fetch(API_ENDPOINTS.LEADS);
    return handleResponse(response);
  },

  // Get available tools
  getTools: async () => {
    const response = await fetch(API_ENDPOINTS.TOOLS);
    return handleResponse(response);
  },

  // Convert files
  convertFile: async (file, targetFormat) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_format', targetFormat);

    const response = await fetch(API_ENDPOINTS.CONVERT, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(response);
  },

  // Check system status
  getStatus: async () => {
    const response = await fetch(API_ENDPOINTS.STATUS);
    return handleResponse(response);
  },

  // Health check
  checkHealth: async () => {
    const response = await fetch(API_ENDPOINTS.HEALTH);
    return handleResponse(response);
  }
};

export default apiService;
