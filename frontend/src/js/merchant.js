/**
 * Merchant Page JavaScript
 * Handles merchant login and registration functionality
 */

import { API } from './api.js';
import { Utils } from './utils.js';

class MerchantApp {
  constructor() {
    this.api = new API();
    this.utils = new Utils();
    this.currentPage = window.location.pathname.split('/').pop() || 'login';

    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.initCurrentPage();
  }

  setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => this.handleLogin(e));
    }

    // OAuth buttons
    const googleBtn = document.getElementById('googleLogin');
    const appleBtn = document.getElementById('appleLogin');
    const facebookBtn = document.getElementById('facebookLogin');

    if (googleBtn) googleBtn.addEventListener('click', () => this.handleOAuthLogin('google'));
    if (appleBtn) appleBtn.addEventListener('click', () => this.handleOAuthLogin('apple'));
    if (facebookBtn) facebookBtn.addEventListener('click', () => this.handleOAuthLogin('facebook'));

    // Form validation
    this.setupFormValidation();
  }

  initCurrentPage() {
    switch (this.currentPage) {
      case 'login':
        this.initLoginPage();
        break;
      case 'register':
        this.initRegisterPage();
        break;
      case 'dashboard':
        this.initDashboardPage();
        break;
      default:
        this.initLoginPage();
    }
  }

  initLoginPage() {
    // Pre-fill email if remembered
    const rememberedEmail = this.utils.getCookie('remembered_email');
    if (rememberedEmail) {
      const emailInput = document.getElementById('email');
      if (emailInput) {
        emailInput.value = rememberedEmail;
        document.getElementById('remember').checked = true;
      }
    }

    // Auto-focus email field
    const emailInput = document.getElementById('email');
    if (emailInput) emailInput.focus();
  }

  initRegisterPage() {
    // Initialize registration form if it exists
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => this.handleRegistration(e));
    }
  }

  initDashboardPage() {
    // Initialize dashboard if user is logged in
    this.loadDashboardData();
  }

  setupFormValidation() {
    // Real-time email validation
    const emailInput = document.getElementById('email');
    if (emailInput) {
      emailInput.addEventListener('blur', () => {
        this.validateEmail(emailInput);
      });
    }

    // Password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
      passwordInput.addEventListener('input', () => {
        this.updatePasswordStrength(passwordInput.value);
      });
    }
  }

  async handleLogin(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const loginData = {
      email: formData.get('email'),
      password: formData.get('password'),
      remember: formData.get('remember') === 'on'
    };

    // Validate form
    if (!this.validateLoginForm(loginData)) {
      return;
    }

    // Show loading state
    this.setLoadingState(true);

    try {
      const response = await this.api.login(loginData);

      if (response.success) {
        // Handle successful login
        if (loginData.remember) {
          this.utils.setCookie('remembered_email', loginData.email, { expires: 30 });
        }

        // Store auth token
        this.utils.setLocalStorage('auth_token', response.token);

        // Redirect to dashboard
        window.location.href = '/merchant/dashboard';
      } else {
        this.showFormError('loginForm', response.message || 'Đăng nhập thất bại');
      }
    } catch (error) {
      console.error('Login error:', error);
      this.showFormError('loginForm', 'Có lỗi xảy ra. Vui lòng thử lại.');
    } finally {
      this.setLoadingState(false);
    }
  }

  async handleOAuthLogin(provider) {
    try {
      let authUrl;

      switch (provider) {
        case 'google':
          authUrl = await this.api.getGoogleAuthUrl();
          break;
        case 'apple':
          authUrl = await this.api.getAppleAuthUrl();
          break;
        case 'facebook':
          authUrl = await this.api.getFacebookAuthUrl();
          break;
        default:
          throw new Error('Unsupported OAuth provider');
      }

      if (authUrl) {
        window.location.href = authUrl;
      }
    } catch (error) {
      console.error('OAuth login error:', error);
      this.showNotification('Không thể kết nối với dịch vụ đăng nhập. Vui lòng thử lại.', 'error');
    }
  }

  async handleRegistration(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const registerData = {
      email: formData.get('email'),
      password: formData.get('password'),
      confirmPassword: formData.get('confirmPassword'),
      companyName: formData.get('companyName'),
      phone: formData.get('phone'),
      agreeToTerms: formData.get('agreeToTerms') === 'on'
    };

    // Validate form
    if (!this.validateRegistrationForm(registerData)) {
      return;
    }

    // Show loading state
    this.setLoadingState(true, 'registerBtn');

    try {
      const response = await this.api.register(registerData);

      if (response.success) {
        this.showNotification('Đăng ký thành công! Vui lòng kiểm tra email để xác nhận.', 'success');

        // Redirect to login after 3 seconds
        setTimeout(() => {
          window.location.href = '/merchant/login';
        }, 3000);
      } else {
        this.showFormError('registerForm', response.message || 'Đăng ký thất bại');
      }
    } catch (error) {
      console.error('Registration error:', error);
      this.showFormError('registerForm', 'Có lỗi xảy ra. Vui lòng thử lại.');
    } finally {
      this.setLoadingState(false, 'registerBtn');
    }
  }

  validateLoginForm(data) {
    let isValid = true;

    // Email validation
    if (!this.utils.validateEmail(data.email)) {
      this.showFieldError('email', 'Email không hợp lệ');
      isValid = false;
    } else {
      this.clearFieldError('email');
    }

    // Password validation
    if (!data.password || data.password.length < 6) {
      this.showFieldError('password', 'Mật khẩu phải có ít nhất 6 ký tự');
      isValid = false;
    } else {
      this.clearFieldError('password');
    }

    return isValid;
  }

  validateRegistrationForm(data) {
    let isValid = true;

    // Email validation
    if (!this.utils.validateEmail(data.email)) {
      this.showFieldError('email', 'Email không hợp lệ');
      isValid = false;
    } else {
      this.clearFieldError('email');
    }

    // Password validation
    if (!data.password || data.password.length < 8) {
      this.showFieldError('password', 'Mật khẩu phải có ít nhất 8 ký tự');
      isValid = false;
    } else {
      this.clearFieldError('password');
    }

    // Confirm password
    if (data.password !== data.confirmPassword) {
      this.showFieldError('confirmPassword', 'Mật khẩu xác nhận không khớp');
      isValid = false;
    } else {
      this.clearFieldError('confirmPassword');
    }

    // Company name
    if (!data.companyName || data.companyName.trim().length < 2) {
      this.showFieldError('companyName', 'Tên công ty phải có ít nhất 2 ký tự');
      isValid = false;
    } else {
      this.clearFieldError('companyName');
    }

    // Phone validation
    if (!this.utils.validatePhone(data.phone)) {
      this.showFieldError('phone', 'Số điện thoại không hợp lệ');
      isValid = false;
    } else {
      this.clearFieldError('phone');
    }

    // Terms agreement
    if (!data.agreeToTerms) {
      this.showFieldError('agreeToTerms', 'Bạn phải đồng ý với điều khoản sử dụng');
      isValid = false;
    } else {
      this.clearFieldError('agreeToTerms');
    }

    return isValid;
  }

  validateEmail(input) {
    const email = input.value.trim();
    if (!email) return;

    if (!this.utils.validateEmail(email)) {
      this.showFieldError('email', 'Email không hợp lệ');
    } else {
      this.clearFieldError('email');
    }
  }

  updatePasswordStrength(password) {
    const strengthIndicator = document.getElementById('passwordStrength');
    if (!strengthIndicator) return;

    let strength = 0;
    let feedback = [];

    if (password.length >= 8) strength++;
    else feedback.push('Ít nhất 8 ký tự');

    if (/[a-z]/.test(password)) strength++;
    else feedback.push('Chữ thường');

    if (/[A-Z]/.test(password)) strength++;
    else feedback.push('Chữ hoa');

    if (/\d/.test(password)) strength++;
    else feedback.push('Số');

    if (/[^A-Za-z\d]/.test(password)) strength++;
    else feedback.push('Ký tự đặc biệt');

    const strengthTexts = ['Rất yếu', 'Yếu', 'Trung bình', 'Mạnh', 'Rất mạnh'];
    const strengthClasses = ['very-weak', 'weak', 'medium', 'strong', 'very-strong'];

    strengthIndicator.textContent = strengthTexts[strength] || 'Rất yếu';
    strengthIndicator.className = `password-strength ${strengthClasses[strength] || 'very-weak'}`;
  }

  showFieldError(fieldId, message) {
    const errorElement = document.getElementById(`${fieldId}Error`);
    const inputElement = document.getElementById(fieldId);

    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
    }

    if (inputElement) {
      inputElement.classList.add('error');
    }
  }

  clearFieldError(fieldId) {
    const errorElement = document.getElementById(`${fieldId}Error`);
    const inputElement = document.getElementById(fieldId);

    if (errorElement) {
      errorElement.textContent = '';
      errorElement.style.display = 'none';
    }

    if (inputElement) {
      inputElement.classList.remove('error');
    }
  }

  showFormError(formId, message) {
    const form = document.getElementById(formId);
    if (form) {
      // Remove existing error messages
      const existingErrors = form.querySelectorAll('.form-error:not([id$="Error"])');
      existingErrors.forEach(error => error.remove());

      // Add new error message
      const errorDiv = document.createElement('div');
      errorDiv.className = 'form-error';
      errorDiv.textContent = message;
      errorDiv.style.cssText = 'color: var(--error); text-align: center; margin-bottom: var(--spacing-md);';

      form.insertBefore(errorDiv, form.firstChild);
    }
  }

  setLoadingState(isLoading, buttonId = 'loginBtn') {
    const button = document.getElementById(buttonId);
    const buttonText = document.getElementById(buttonId.replace('Btn', 'Text'));
    const loadingSpinner = document.getElementById(buttonId.replace('Btn', 'Loading'));

    if (button) {
      button.disabled = isLoading;
    }

    if (buttonText) {
      buttonText.style.display = isLoading ? 'none' : 'inline';
    }

    if (loadingSpinner) {
      loadingSpinner.style.display = isLoading ? 'inline-block' : 'none';
    }
  }

  showNotification(message, type = 'info') {
    // Use global notification system if available
    if (window.zaloPayApp && window.zaloPayApp.showNotification) {
      window.zaloPayApp.showNotification(message, type);
    } else {
      // Fallback notification
      alert(message);
    }
  }

  async loadDashboardData() {
    try {
      // Load merchant dashboard data
      const dashboardData = await this.api.get('/merchant/dashboard');

      // Update UI with dashboard data
      this.updateDashboardUI(dashboardData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      this.showNotification('Không thể tải dữ liệu dashboard', 'error');
    }
  }

  updateDashboardUI(data) {
    // Update dashboard elements with data
    Object.keys(data).forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        element.textContent = data[key];
      }
    });
  }
}

// Initialize merchant app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.merchantApp = new MerchantApp();
});

// Export for testing
export default MerchantApp;