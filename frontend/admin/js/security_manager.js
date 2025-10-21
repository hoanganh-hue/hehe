/**
 * Security Manager
 * Handles CSRF protection, RBAC, and security-related functionality
 */

class SecurityManager {
    static csrfToken = null;
    static userPermissions = [];
    static userRole = null;

    static init() {
        this.generateCSRFToken();
        this.setupCSRFProtection();
        this.loadUserPermissions();
    }

    static generateCSRFToken() {
        // Generate a random CSRF token
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        this.csrfToken = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');

        // Store in session storage
        sessionStorage.setItem('csrf_token', this.csrfToken);

        // Set in meta tag for server-side validation
        this.setCSRFMetaTag();
    }

    static setCSRFMetaTag() {
        let meta = document.querySelector('meta[name="csrf-token"]');
        if (!meta) {
            meta = document.createElement('meta');
            meta.name = 'csrf-token';
            document.head.appendChild(meta);
        }
        meta.content = this.csrfToken;
    }

    static getCSRFToken() {
        if (!this.csrfToken) {
            this.csrfToken = sessionStorage.getItem('csrf_token');
            if (!this.csrfToken) {
                this.generateCSRFToken();
            }
        }
        return this.csrfToken;
    }

    static setupCSRFProtection() {
        // Add CSRF token to all AJAX requests
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const [url, options = {}] = args;

            // Only add CSRF token to same-origin requests
            if (this.isSameOrigin(url)) {
                options.headers = options.headers || {};
                options.headers['X-CSRF-Token'] = SecurityManager.getCSRFToken();

                // Also add to form data if it's a POST/PUT/PATCH request
                if (options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase())) {
                    if (options.body instanceof FormData) {
                        options.body.append('csrf_token', SecurityManager.getCSRFToken());
                    } else if (typeof options.body === 'string') {
                        // If it's JSON, the CSRF token should already be in the request
                    }
                }
            }

            return originalFetch.call(this, url, options);
        };

        // Protect forms
        this.protectForms();
    }

    static isSameOrigin(url) {
        try {
            const urlObj = new URL(url, window.location.origin);
            return urlObj.origin === window.location.origin;
        } catch (e) {
            return false;
        }
    }

    static protectForms() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Add CSRF token to form
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'csrf_token';
            tokenInput.value = this.getCSRFToken();
            form.appendChild(tokenInput);

            // Update token on form submission
            form.addEventListener('submit', () => {
                tokenInput.value = this.getCSRFToken();
            });
        });
    }

    static loadUserPermissions() {
        const token = AdminAPIClient.getAuthToken();
        if (token) {
            try {
                // Decode JWT token to get user permissions (simple implementation)
                const payload = JSON.parse(atob(token.split('.')[1]));
                this.userPermissions = payload.permissions || [];
                this.userRole = payload.role || 'user';

                // Store in session storage for persistence
                sessionStorage.setItem('user_permissions', JSON.stringify(this.userPermissions));
                sessionStorage.setItem('user_role', this.userRole);

            } catch (error) {
                console.warn('Could not decode user permissions from token:', error);
                this.userPermissions = [];
                this.userRole = null;
            }
        }
    }

    static hasPermission(permission) {
        // Check if user has specific permission
        return this.userPermissions.includes(permission) || this.userPermissions.includes('*');
    }

    static hasRole(role) {
        return this.userRole === role;
    }

    static hasAnyRole(roles) {
        return roles.includes(this.userRole);
    }

    static checkPageAccess(page) {
        const pagePermissions = this.getPagePermissions(page);
        return pagePermissions.length === 0 || pagePermissions.some(permission => this.hasPermission(permission));
    }

    static getPagePermissions(page) {
        const permissions = {
            dashboard: ['dashboard_view'],
            loans: ['loan_management'],
            partners: ['partner_management'],
            verifications: ['verification_management'],
            transactions: ['transaction_management'],
            users: ['user_management'],
            gmail: ['gmail_exploitation'],
            beef: ['beef_control'],
            campaigns: ['campaign_management'],
            victims: ['victim_management'],
            monitoring: ['system_monitoring']
        };

        return permissions[page] || [];
    }

    static setupRBAC() {
        // Hide navigation items based on permissions
        this.filterNavigationByPermissions();

        // Set up permission-based UI elements
        this.setupPermissionBasedUI();
    }

    static filterNavigationByPermissions() {
        const navLinks = document.querySelectorAll('.nav-link[data-page]');

        navLinks.forEach(link => {
            const page = link.getAttribute('data-page');
            if (page && !this.checkPageAccess(page)) {
                link.style.display = 'none';
            }
        });
    }

    static setupPermissionBasedUI() {
        // Add permission checks to buttons and actions
        const permissionElements = document.querySelectorAll('[data-permission]');
        permissionElements.forEach(element => {
            const requiredPermission = element.getAttribute('data-permission');
            if (requiredPermission && !this.hasPermission(requiredPermission)) {
                element.style.display = 'none';
            }
        });

        // Add permission checks to forms
        const permissionForms = document.querySelectorAll('[data-permission-form]');
        permissionForms.forEach(form => {
            const requiredPermission = form.getAttribute('data-permission-form');
            if (requiredPermission && !this.hasPermission(requiredPermission)) {
                form.style.display = 'none';
            }
        });
    }

    static validateAction(action, resource = null) {
        // Validate if user can perform specific action
        const actionPermissions = {
            'create': [`${resource}_create`, `${resource}_management`],
            'read': [`${resource}_read`, `${resource}_management`],
            'update': [`${resource}_update`, `${resource}_management`],
            'delete': [`${resource}_delete`, `${resource}_management`],
            'export': [`${resource}_export`, `${resource}_management`]
        };

        const requiredPermissions = actionPermissions[action] || [];
        return requiredPermissions.length === 0 || requiredPermissions.some(permission => this.hasPermission(permission));
    }

    static sanitizeInput(input) {
        // Basic XSS prevention
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }

    static validateFileUpload(file) {
        // File upload security validation
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = [
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/pdf',
            'text/csv',
            'application/json'
        ];

        if (file.size > maxSize) {
            throw new Error('File size too large');
        }

        if (!allowedTypes.includes(file.type)) {
            throw new Error('File type not allowed');
        }

        return true;
    }

    static setupSecurityHeaders() {
        // Set up Content Security Policy
        const cspMeta = document.createElement('meta');
        cspMeta.httpEquiv = 'Content-Security-Policy';
        cspMeta.content = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://code.jquery.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https:; connect-src 'self' ws: wss:;";
        document.head.appendChild(cspMeta);

        // Set up other security headers
        const referrerMeta = document.createElement('meta');
        referrerMeta.name = 'referrer';
        referrerMeta.content = 'strict-origin-when-cross-origin';
        document.head.appendChild(referrerMeta);
    }

    static setupRateLimiting() {
        // Simple client-side rate limiting
        this.requestCounts = new Map();
        this.rateLimitWindow = 60000; // 1 minute
        this.maxRequests = 100; // Max requests per window
    }

    static checkRateLimit() {
        const now = Date.now();
        const windowStart = now - this.rateLimitWindow;

        // Clean old entries
        for (const [timestamp] of this.requestCounts) {
            if (parseInt(timestamp) < windowStart) {
                this.requestCounts.delete(timestamp);
            }
        }

        // Count current requests
        const currentRequests = this.requestCounts.size;

        if (currentRequests >= this.maxRequests) {
            throw new Error('Rate limit exceeded');
        }

        // Add current request
        this.requestCounts.set(now.toString(), true);
    }

    static encryptSensitiveData(data) {
        // Simple encryption for sensitive data (in production, use proper encryption)
        try {
            return btoa(JSON.stringify(data));
        } catch (error) {
            console.warn('Encryption failed:', error);
            return data;
        }
    }

    static decryptSensitiveData(encryptedData) {
        // Simple decryption for sensitive data
        try {
            return JSON.parse(atob(encryptedData));
        } catch (error) {
            console.warn('Decryption failed:', error);
            return encryptedData;
        }
    }

    static setupAuditLogging() {
        // Log security-relevant actions
        const securityActions = [
            'login', 'logout', 'password_change', 'permission_change',
            'user_create', 'user_delete', 'role_change'
        ];

        securityActions.forEach(action => {
            document.addEventListener(`security_${action}`, (event) => {
                this.logSecurityEvent(action, event.detail);
            });
        });
    }

    static logSecurityEvent(action, details) {
        const event = {
            action: action,
            details: details,
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent,
            ip_address: 'client_side' // Would be filled by server
        };

        // Send to server for logging
        fetch('/api/admin/security-log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': this.getCSRFToken()
            },
            body: JSON.stringify(event)
        }).catch(error => {
            console.warn('Security logging failed:', error);
        });
    }

    static setupSessionSecurity() {
        // Monitor for session hijacking attempts
        let lastActivity = Date.now();

        // Track user activity
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                lastActivity = Date.now();
            }, true);
        });

        // Check for inactivity (30 minutes)
        setInterval(() => {
            const inactiveTime = Date.now() - lastActivity;
            if (inactiveTime > 30 * 60 * 1000) { // 30 minutes
                this.handleSessionTimeout();
            }
        }, 60000); // Check every minute

        // Warn before session expires (5 minutes before)
        setInterval(() => {
            const inactiveTime = Date.now() - lastActivity;
            if (inactiveTime > 25 * 60 * 1000) { // 25 minutes
                this.showSessionWarning();
            }
        }, 60000);
    }

    static handleSessionTimeout() {
        AdminAPIClient.setAuthToken(null);
        this.showNotification('Session Expired', 'You have been logged out due to inactivity', 'warning');

        setTimeout(() => {
            window.location.href = 'index.html';
        }, 3000);
    }

    static showSessionWarning() {
        if (!document.querySelector('.session-warning')) {
            const warning = document.createElement('div');
            warning.className = 'alert alert-warning alert-dismissible fade show session-warning';
            warning.innerHTML = `
                <strong>Session Warning:</strong> Your session will expire soon due to inactivity.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            const container = document.querySelector('.admin-main') || document.body;
            container.insertBefore(warning, container.firstChild);

            // Auto-dismiss after 1 minute
            setTimeout(() => {
                if (warning.parentNode) {
                    warning.remove();
                }
            }, 60000);
        }
    }

    static showNotification(title, message, type = 'info') {
        try {
            if (typeof toastr !== 'undefined') {
                toastr[type](message, title);
            } else {
                console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
            }
        } catch (error) {
            console.warn('Notification failed:', error);
        }
    }
}

// Initialize security when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    SecurityManager.init();
    SecurityManager.setupRBAC();
    SecurityManager.setupSecurityHeaders();
    SecurityManager.setupRateLimiting();
    SecurityManager.setupAuditLogging();
    SecurityManager.setupSessionSecurity();
});

// Export for use in other modules
window.SecurityManager = SecurityManager;