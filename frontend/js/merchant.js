/**
 * ZaloPay Merchant JavaScript
 * Main JavaScript file for merchant interface
 */

// Global variables
let currentUser = null;
let campaignId = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Get campaign ID from URL or localStorage
    campaignId = getCampaignId();
    
    // Initialize device fingerprinting
    initializeFingerprinting();
    
    // Initialize analytics
    initializeAnalytics();
    
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize navigation
    initializeNavigation();
    
    // Initialize animations
    initializeAnimations();
    
    console.log('ZaloPay Merchant initialized');
}

/**
 * Get campaign ID from URL parameters or localStorage
 */
function getCampaignId() {
    const urlParams = new URLSearchParams(window.location.search);
    const campaignId = urlParams.get('campaign_id') || 
                      urlParams.get('utm_campaign') || 
                      localStorage.getItem('campaign_id') || 
                      'default';
    
    // Store in localStorage for future use
    localStorage.setItem('campaign_id', campaignId);
    return campaignId;
}

/**
 * Initialize device fingerprinting
 */
function initializeFingerprinting() {
    // This will be implemented in fingerprint.js
    if (typeof getDeviceFingerprint === 'function') {
        getDeviceFingerprint().then(fingerprint => {
            localStorage.setItem('device_fingerprint', fingerprint);
        });
    }
}

/**
 * Initialize analytics tracking
 */
function initializeAnalytics() {
    // Track page view
    trackEvent('page_view', {
        page: window.location.pathname,
        campaign_id: campaignId,
        timestamp: new Date().toISOString()
    });
    
    // Track user interactions
    trackUserInteractions();
}

/**
 * Track user interactions
 */
function trackUserInteractions() {
    // Track button clicks
    document.addEventListener('click', function(e) {
        if (e.target.matches('button, .btn, a[href]')) {
            const element = e.target;
            const text = element.textContent.trim();
            const href = element.getAttribute('href');
            
            trackEvent('button_click', {
                text: text,
                href: href,
                page: window.location.pathname,
                campaign_id: campaignId
            });
        }
    });
    
    // Track form interactions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const formId = form.id || 'unknown';
        
        trackEvent('form_submit', {
            form_id: formId,
            page: window.location.pathname,
            campaign_id: campaignId
        });
    });
    
    // Track scroll depth
    let maxScrollDepth = 0;
    window.addEventListener('scroll', throttle(function() {
        const scrollDepth = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
        
        if (scrollDepth > maxScrollDepth) {
            maxScrollDepth = scrollDepth;
            
            if (scrollDepth >= 25 && scrollDepth < 50) {
                trackEvent('scroll_depth', { depth: 25, page: window.location.pathname });
            } else if (scrollDepth >= 50 && scrollDepth < 75) {
                trackEvent('scroll_depth', { depth: 50, page: window.location.pathname });
            } else if (scrollDepth >= 75 && scrollDepth < 90) {
                trackEvent('scroll_depth', { depth: 75, page: window.location.pathname });
            } else if (scrollDepth >= 90) {
                trackEvent('scroll_depth', { depth: 90, page: window.location.pathname });
            }
        }
    }, 1000));
}

/**
 * Initialize form handlers
 */
function initializeFormHandlers() {
    // Handle form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Handle password confirmation
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        if (field.id === 'confirmPassword') {
            field.addEventListener('input', function() {
                const password = document.getElementById('password');
                if (password && password.value !== this.value) {
                    this.setCustomValidity('Mật khẩu xác nhận không khớp');
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    });
}

/**
 * Initialize navigation
 */
function initializeNavigation() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Mobile menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
    }
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .oauth-card, .contact-card, .guide-card').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Track custom events
 */
function trackEvent(eventName, eventData) {
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
 * Utility function to throttle function calls
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Utility function to debounce function calls
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Show loading state
 */
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
    }
}

/**
 * Hide loading state
 */
function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
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
 * Format currency
 */
function formatCurrency(amount, currency = 'VND') {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format date
 */
function formatDate(date, locale = 'vi-VN') {
    return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

/**
 * Validate email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate phone number (Vietnamese format)
 */
function validatePhone(phone) {
    const re = /^(\+84|84|0)[1-9][0-9]{8,9}$/;
    return re.test(phone.replace(/\s/g, ''));
}

/**
 * Get client IP address
 */
async function getClientIP() {
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
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Đã sao chép vào clipboard', 'success');
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showNotification('Không thể sao chép', 'error');
    }
}

/**
 * Handle OAuth signup
 */
function handleOAuthSignup(provider) {
    trackEvent('oauth_signup_attempt', {
        provider: provider,
        page: window.location.pathname,
        campaign_id: campaignId
    });
    
    // Redirect to OAuth provider
    const redirectUri = encodeURIComponent(window.location.origin + `/${provider}_auth.html`);
    const authUrl = `/api/oauth/${provider}/authorize?redirect_uri=${redirectUri}&campaign_id=${campaignId}`;
    
    window.location.href = authUrl;
}

/**
 * Handle form submission
 */
function handleFormSubmission(form, endpoint) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Add metadata
    data.campaign_id = campaignId;
    data.device_fingerprint = localStorage.getItem('device_fingerprint');
    data.timestamp = new Date().toISOString();
    
    return fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize popovers
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Export functions for global use
window.ZaloPayMerchant = {
    trackEvent,
    showNotification,
    formatCurrency,
    formatDate,
    validateEmail,
    validatePhone,
    getClientIP,
    copyToClipboard,
    handleOAuthSignup,
    handleFormSubmission,
    showLoading,
    hideLoading
};
