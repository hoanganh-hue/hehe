/**
 * ZaloPay Frontend - Main Entry Point
 * Production-ready frontend application
 */

import '../css/main.css';
import { API } from './api.js';
import { Utils } from './utils.js';
import { Security } from './security.js';

class ZaloPayApp {
  constructor() {
    this.api = new API();
    this.utils = new Utils();
    this.security = new Security();
    this.currentPage = null;

    this.init();
  }

  async init() {
    try {
      // Initialize security features
      await this.security.init();

      // Initialize utilities
      this.utils.init();

      // Setup event listeners
      this.setupEventListeners();

      // Check authentication status
      await this.checkAuthStatus();

      // Initialize page-specific functionality
      this.initCurrentPage();

      console.log('ZaloPay Frontend initialized successfully');
    } catch (error) {
      console.error('Failed to initialize ZaloPay Frontend:', error);
      this.showError('Failed to initialize application');
    }
  }

  setupEventListeners() {
    // Global error handling
    window.addEventListener('error', (event) => {
      console.error('Global error:', event.error);
      this.handleError(event.error);
    });

    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      this.handleError(event.reason);
    });

    // Network status monitoring
    window.addEventListener('online', () => {
      this.showNotification('Connection restored', 'success');
    });

    window.addEventListener('offline', () => {
      this.showNotification('Connection lost', 'warning');
    });
  }

  async checkAuthStatus() {
    try {
      const response = await this.api.get('/auth/status');
      if (response.authenticated) {
        this.handleAuthenticatedUser(response.user);
      } else {
        this.handleUnauthenticatedUser();
      }
    } catch (error) {
      console.warn('Auth check failed:', error);
      this.handleUnauthenticatedUser();
    }
  }

  handleAuthenticatedUser(user) {
    // Update UI for authenticated user
    const userElements = document.querySelectorAll('[data-user-info]');
    userElements.forEach(element => {
      element.textContent = user.name || user.email;
    });

    // Show authenticated content
    document.querySelectorAll('[data-requires-auth]').forEach(element => {
      element.style.display = 'block';
    });

    // Hide unauthenticated content
    document.querySelectorAll('[data-requires-no-auth]').forEach(element => {
      element.style.display = 'none';
    });
  }

  handleUnauthenticatedUser() {
    // Show unauthenticated content
    document.querySelectorAll('[data-requires-no-auth]').forEach(element => {
      element.style.display = 'block';
    });

    // Hide authenticated content
    document.querySelectorAll('[data-requires-auth]').forEach(element => {
      element.style.display = 'none';
    });
  }

  initCurrentPage() {
    const path = window.location.pathname;

    if (path.includes('/merchant')) {
      this.currentPage = 'merchant';
      this.initMerchantPage();
    } else if (path.includes('/admin')) {
      this.currentPage = 'admin';
      this.initAdminPage();
    } else {
      this.currentPage = 'home';
      this.initHomePage();
    }
  }

  initHomePage() {
    // Initialize home page specific functionality
    console.log('Initializing home page');
  }

  initMerchantPage() {
    // Initialize merchant page specific functionality
    console.log('Initializing merchant page');
  }

  initAdminPage() {
    // Initialize admin page specific functionality
    console.log('Initializing admin page');
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Add to page
    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }

  showError(message) {
    this.showNotification(message, 'error');
  }

  handleError(error) {
    console.error('Application error:', error);
    this.showError('An unexpected error occurred. Please try again.');
  }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.zaloPayApp = new ZaloPayApp();
});

// Export for testing
export default ZaloPayApp;