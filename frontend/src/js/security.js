/**
 * Security Module - Handles security features and anti-detection
 */

import CryptoJS from 'crypto-js';

export class Security {
  constructor() {
    this.fingerprint = null;
    this.sessionId = null;
    this.csrfToken = null;
  }

  async init() {
    try {
      // Generate session ID
      this.sessionId = this.generateSessionId();

      // Generate CSRF token
      this.csrfToken = this.generateCSRFToken();

      // Collect device fingerprint
      this.fingerprint = await this.collectFingerprint();

      // Setup security event listeners
      this.setupSecurityListeners();

      // Initialize anti-detection measures
      this.initAntiDetection();

      console.log('Security module initialized');
    } catch (error) {
      console.error('Failed to initialize security module:', error);
    }
  }

  generateSessionId() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 9);
    return CryptoJS.SHA256(timestamp + random).toString();
  }

  generateCSRFToken() {
    const timestamp = Date.now().toString();
    const random = Math.random().toString(36);
    return CryptoJS.SHA256(timestamp + random + this.sessionId).toString();
  }

  async collectFingerprint() {
    const fingerprint = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      doNotTrack: navigator.doNotTrack,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      screenResolution: `${screen.width}x${screen.height}`,
      colorDepth: screen.colorDepth,
      pixelRatio: window.devicePixelRatio || 1,
      touchSupport: 'ontouchstart' in window,
      plugins: this.getPluginsInfo(),
      canvasFingerprint: await this.getCanvasFingerprint(),
      webglFingerprint: this.getWebGLFingerprint(),
      fonts: this.getFontsList(),
      timestamp: Date.now()
    };

    // Hash the fingerprint for privacy
    const fingerprintString = JSON.stringify(fingerprint);
    fingerprint.hash = CryptoJS.SHA256(fingerprintString).toString();

    return fingerprint;
  }

  getPluginsInfo() {
    const plugins = [];
    for (let i = 0; i < navigator.plugins.length; i++) {
      const plugin = navigator.plugins[i];
      plugins.push({
        name: plugin.name,
        description: plugin.description,
        filename: plugin.filename
      });
    }
    return plugins;
  }

  async getCanvasFingerprint() {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('Canvas fingerprint test', 2, 2);
      return canvas.toDataURL();
    } catch (error) {
      return null;
    }
  }

  getWebGLFingerprint() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return null;

      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      return {
        vendor: gl.getParameter(gl.VENDOR),
        renderer: gl.getParameter(gl.RENDERER),
        debugVendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : null,
        debugRenderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : null
      };
    } catch (error) {
      return null;
    }
  }

  getFontsList() {
    const fonts = [
      'Arial', 'Arial Black', 'Arial Narrow', 'Arial Rounded MT Bold',
      'Calibri', 'Cambria', 'Cambria Math', 'Candara', 'Comic Sans MS',
      'Consolas', 'Constantia', 'Corbel', 'Courier New', 'Ebrima',
      'Franklin Gothic Medium', 'Gabriola', 'Gadugi', 'Georgia',
      'Impact', 'Lucida Console', 'Lucida Sans Unicode', 'Microsoft Himalaya',
      'Microsoft JhengHei', 'Microsoft YaHei', 'MingLiU-ExtB', 'Mongolian Baiti',
      'MS Gothic', 'MS PGothic', 'MS UI Gothic', 'MV Boli', 'Myanmar Text',
      'Nirmala UI', 'Palatino Linotype', 'Segoe Print', 'Segoe Script',
      'Segoe UI', 'Segoe UI Light', 'Segoe UI Semibold', 'Segoe UI Semilight',
      'Segoe UI Symbol', 'SimSun', 'Sitka', 'Sylfaen', 'Symbol', 'Tahoma',
      'Times New Roman', 'Trebuchet MS', 'Verdana', 'Webdings', 'Wingdings',
      'Yu Gothic'
    ];

    const availableFonts = [];
    const testString = 'mmmmmmmmmmlli';
    const testSize = '72px';

    fonts.forEach(font => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.font = testSize + ' ' + font;
      const baselineWidth = ctx.measureText(testString).width;

      ctx.font = testSize + ' monospace';
      const monospaceWidth = ctx.measureText(testString).width;

      if (baselineWidth !== monospaceWidth) {
        availableFonts.push(font);
      }
    });

    return availableFonts;
  }

  setupSecurityListeners() {
    // Detect developer tools
    let devtoolsOpen = false;
    const threshold = 160;

    const detectDevTools = () => {
      if (window.outerHeight - window.innerHeight > threshold || window.outerWidth - window.innerWidth > threshold) {
        if (!devtoolsOpen) {
          devtoolsOpen = true;
          this.handleDevToolsOpen();
        }
      } else {
        devtoolsOpen = false;
      }
    };

    setInterval(detectDevTools, 500);

    // Detect copy/paste operations
    document.addEventListener('copy', (e) => {
      this.logSecurityEvent('copy', { target: e.target.tagName });
    });

    document.addEventListener('paste', (e) => {
      this.logSecurityEvent('paste', { target: e.target.tagName });
    });

    // Detect right-click
    document.addEventListener('contextmenu', (e) => {
      this.logSecurityEvent('contextmenu', { x: e.clientX, y: e.clientY });
      // Allow right-click for now, but log it
    });

    // Detect keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey || e.metaKey) {
        const key = e.key.toLowerCase();
        if (['u', 's', 'a', 'c', 'v', 'i', 'j', 'k'].includes(key)) {
          this.logSecurityEvent('keyboard_shortcut', { key: key, ctrl: e.ctrlKey });
        }
      }
    });
  }

  initAntiDetection() {
    // Randomize timing to avoid detection patterns
    this.randomizeTimings();

    // Spoof navigator properties if needed
    this.spoofNavigator();

    // Add random mouse movements
    this.addRandomMouseMovements();
  }

  randomizeTimings() {
    // Add random delays to form submissions and other actions
    const originalSubmit = HTMLFormElement.prototype.submit;
    HTMLFormElement.prototype.submit = function() {
      setTimeout(() => {
        originalSubmit.call(this);
      }, Math.random() * 1000 + 500); // 500-1500ms delay
    };
  }

  spoofNavigator() {
    // Add some randomization to navigator properties
    const originalUserAgent = navigator.userAgent;
    Object.defineProperty(navigator, 'userAgent', {
      get: () => {
        // Occasionally return slightly modified user agent
        if (Math.random() < 0.1) {
          return originalUserAgent + ' (Modified)';
        }
        return originalUserAgent;
      }
    });
  }

  addRandomMouseMovements() {
    // Add subtle random mouse movements to simulate human behavior
    let lastMouseMove = Date.now();

    document.addEventListener('mousemove', () => {
      lastMouseMove = Date.now();
    });

    // Simulate micro-movements when mouse is still
    setInterval(() => {
      if (Date.now() - lastMouseMove > 5000) { // If no mouse movement for 5 seconds
        const event = new MouseEvent('mousemove', {
          clientX: Math.random() * window.innerWidth,
          clientY: Math.random() * window.innerHeight,
          bubbles: true
        });
        document.dispatchEvent(event);
      }
    }, 10000);
  }

  handleDevToolsOpen() {
    this.logSecurityEvent('devtools_opened');
    // Could implement additional security measures here
  }

  logSecurityEvent(eventType, details = {}) {
    const event = {
      type: eventType,
      timestamp: Date.now(),
      sessionId: this.sessionId,
      url: window.location.href,
      userAgent: navigator.userAgent,
      details: details
    };

    // Send to server for analysis
    if (window.zaloPayApp?.api) {
      window.zaloPayApp.api.post('/capture/security-event', event).catch(err => {
        console.warn('Failed to log security event:', err);
      });
    }

    console.log('Security event logged:', eventType, details);
  }

  // Encryption utilities
  encryptData(data, key) {
    return CryptoJS.AES.encrypt(JSON.stringify(data), key).toString();
  }

  decryptData(encryptedData, key) {
    try {
      const bytes = CryptoJS.AES.decrypt(encryptedData, key);
      return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
    } catch (error) {
      console.error('Failed to decrypt data:', error);
      return null;
    }
  }

  // Hash utilities
  hashData(data) {
    return CryptoJS.SHA256(JSON.stringify(data)).toString();
  }

  // Generate secure random string
  generateSecureToken(length = 32) {
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  // Validate input data
  sanitizeInput(input) {
    if (typeof input !== 'string') return input;

    // Remove potentially dangerous characters
    return input
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<[^>]*>/g, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '');
  }

  // Check if running in secure context
  isSecureContext() {
    return window.location.protocol === 'https:' || window.location.hostname === 'localhost';
  }

  // Get security headers
  getSecurityHeaders() {
    return {
      'X-Session-ID': this.sessionId,
      'X-CSRF-Token': this.csrfToken,
      'X-Fingerprint': this.fingerprint?.hash,
      'X-Requested-With': 'XMLHttpRequest'
    };
  }
}