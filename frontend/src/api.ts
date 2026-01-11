const API_BASE = "https://universar-bussinesss-automation.onrender.com/api";

// Helper function to handle API requests
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Something went wrong');
  }

  return response.json();
}

// Health Check
export async function getHealth() {
  return apiRequest('/health');
}

// Auth
export async function login(email: string, password: string) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

// Leads
export async function scrapeLeads(keyword: string, location: string) {
  return apiRequest('/leads/scrape', {
    method: 'POST',
    body: JSON.stringify({ keyword, location }),
  });
}

// File Operations
export async function convertFile(endpoint: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/files/${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'File conversion failed');
  }

  return response.blob();
}

// User
export async function getUserProfile() {
  return apiRequest('/users/me');
}

// Admin
export async function getUsers() {
  return apiRequest('/admin/users');
}

export async function getPayments() {
  return apiRequest('/admin/payments');
}

export async function getJobs() {
  return apiRequest('/admin/jobs');
}

// Billing
export async function createCheckoutSession(priceId: string) {
  return apiRequest('/billing/create-checkout-session', {
    method: 'POST',
    body: JSON.stringify({ priceId }),
  });
}
