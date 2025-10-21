/**
 * Utils Module - Utility functions and helpers
 */

import Cookies from 'js-cookie';

export class Utils {
  constructor() {
    this.debounceTimers = new Map();
    this.throttleTimers = new Map();
  }

  init() {
    // Initialize utility functions
    this.setupGlobalHelpers();
  }

  setupGlobalHelpers() {
    // Add utility functions to window for easy access
    window.utils = {
      formatCurrency: this.formatCurrency.bind(this),
      formatDate: this.formatDate.bind(this),
      debounce: this.debounce.bind(this),
      throttle: this.throttle.bind(this),
      validateEmail: this.validateEmail.bind(this),
      validatePhone: this.validatePhone.bind(this),
      copyToClipboard: this.copyToClipboard.bind(this),
      downloadFile: this.downloadFile.bind(this)
    };
  }

  // Formatting functions
  formatCurrency(amount, currency = 'VND') {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: currency
    }).format(amount);
  }

  formatDate(date, options = {}) {
    const defaultOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };

    return new Intl.DateTimeFormat('vi-VN', { ...defaultOptions, ...options }).format(new Date(date));
  }

  // Debounce function
  debounce(func, wait, immediate = false) {
    const funcName = func.name || 'anonymous';

    return (...args) => {
      const callNow = immediate && !this.debounceTimers.has(funcName);

      clearTimeout(this.debounceTimers.get(funcName));

      this.debounceTimers.set(funcName, setTimeout(() => {
        this.debounceTimers.delete(funcName);
        if (!immediate) func.apply(this, args);
      }, wait));

      if (callNow) func.apply(this, args);
    };
  }

  // Throttle function
  throttle(func, limit) {
    const funcName = func.name || 'anonymous';

    return (...args) => {
      if (!this.throttleTimers.has(funcName)) {
        func.apply(this, args);
        this.throttleTimers.set(funcName, true);
        setTimeout(() => this.throttleTimers.delete(funcName), limit);
      }
    };
  }

  // Validation functions
  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  validatePhone(phone) {
    // Vietnamese phone number validation
    const phoneRegex = /^(0|\+84)[3|5|7|8|9][0-9]{8}$/;
    return phoneRegex.test(phone.replace(/\s+/g, ''));
  }

  validatePassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
  }

  // DOM manipulation helpers
  showElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
      element.style.display = 'block';
    }
  }

  hideElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
      element.style.display = 'none';
    }
  }

  toggleElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
      element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
  }

  // Clipboard operations
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        return true;
      } catch (fallbackErr) {
        console.error('Failed to copy to clipboard:', fallbackErr);
        return false;
      } finally {
        document.body.removeChild(textArea);
      }
    }
  }

  // File operations
  downloadFile(data, filename, mimeType = 'text/plain') {
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }

  // Cookie helpers
  setCookie(name, value, options = {}) {
    Cookies.set(name, value, options);
  }

  getCookie(name) {
    return Cookies.get(name);
  }

  removeCookie(name, options = {}) {
    Cookies.remove(name, options);
  }

  // Local storage helpers with error handling
  setLocalStorage(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
      return false;
    }
  }

  getLocalStorage(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return defaultValue;
    }
  }

  removeLocalStorage(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
      return false;
    }
  }

  // URL helpers
  getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
  }

  setQueryParam(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
  }

  removeQueryParam(name) {
    const url = new URL(window.location);
    url.searchParams.delete(name);
    window.history.pushState({}, '', url);
  }

  // Device detection
  isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
  }

  isAndroid() {
    return /Android/.test(navigator.userAgent);
  }

  // Generate unique IDs
  generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  // Deep clone object
  deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => this.deepClone(item));
    if (typeof obj === 'object') {
      const clonedObj = {};
      for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
          clonedObj[key] = this.deepClone(obj[key]);
        }
      }
      return clonedObj;
    }
  }
}