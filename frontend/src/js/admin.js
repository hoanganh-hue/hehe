/**
 * Admin Page JavaScript
 * Handles admin dashboard and management functionality
 */

import { API } from './api.js';
import { Utils } from './utils.js';

class AdminApp {
  constructor() {
    this.api = new API();
    this.utils = new Utils();
    this.currentPage = window.location.pathname.split('/').pop() || 'dashboard';
    this.currentView = 'overview'; // overview, campaigns, victims, analytics, settings

    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.initCurrentPage();
    this.startRealTimeUpdates();
  }

  setupEventListeners() {
    // Navigation
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => this.handleNavigation(e));
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.addEventListener('input', this.utils.debounce(() => this.handleSearch(), 300));
    }

    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
      btn.addEventListener('click', (e) => this.handleFilter(e));
    });

    // Action buttons
    const actionButtons = document.querySelectorAll('.action-btn');
    actionButtons.forEach(btn => {
      btn.addEventListener('click', (e) => this.handleAction(e));
    });

    // Modal close buttons
    const closeButtons = document.querySelectorAll('.modal-close');
    closeButtons.forEach(btn => {
      btn.addEventListener('click', () => this.closeModal());
    });

    // Form submissions
    const forms = document.querySelectorAll('.admin-form');
    forms.forEach(form => {
      form.addEventListener('submit', (e) => this.handleFormSubmit(e));
    });
  }

  initCurrentPage() {
    switch (this.currentPage) {
      case 'dashboard':
        this.initDashboard();
        break;
      case 'campaigns':
        this.initCampaigns();
        break;
      case 'victims':
        this.initVictims();
        break;
      case 'analytics':
        this.initAnalytics();
        break;
      case 'settings':
        this.initSettings();
        break;
      default:
        this.initDashboard();
    }
  }

  async initDashboard() {
    this.currentView = 'overview';
    await this.loadDashboardData();
    this.renderDashboard();
  }

  async initCampaigns() {
    this.currentView = 'campaigns';
    await this.loadCampaignsData();
    this.renderCampaigns();
  }

  async initVictims() {
    this.currentView = 'victims';
    await this.loadVictimsData();
    this.renderVictims();
  }

  async initAnalytics() {
    this.currentView = 'analytics';
    await this.loadAnalyticsData();
    this.renderAnalytics();
  }

  async initSettings() {
    this.currentView = 'settings';
    await this.loadSettingsData();
    this.renderSettings();
  }

  handleNavigation(event) {
    event.preventDefault();
    const target = event.target.closest('.nav-link').dataset.target;

    // Update active navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    event.target.closest('.nav-link').classList.add('active');

    // Navigate to target
    this.navigateTo(target);
  }

  navigateTo(target) {
    this.currentView = target;
    window.history.pushState({}, '', `/admin/${target}`);

    switch (target) {
      case 'overview':
        this.initDashboard();
        break;
      case 'campaigns':
        this.initCampaigns();
        break;
      case 'victims':
        this.initVictims();
        break;
      case 'analytics':
        this.initAnalytics();
        break;
      case 'settings':
        this.initSettings();
        break;
    }
  }

  async handleSearch() {
    const query = document.getElementById('searchInput').value.trim();

    if (!query) {
      // Reload current view data
      await this.reloadCurrentView();
      return;
    }

    try {
      const results = await this.api.search(this.currentView, query);
      this.renderSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
      this.showNotification('Tìm kiếm thất bại', 'error');
    }
  }

  handleFilter(event) {
    const filterType = event.target.dataset.filter;
    const filterValue = event.target.dataset.value;

    // Update active filter
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    event.target.classList.add('active');

    this.applyFilter(filterType, filterValue);
  }

  async handleAction(event) {
    const action = event.target.dataset.action;
    const targetId = event.target.dataset.id;

    switch (action) {
      case 'edit':
        this.showEditModal(targetId);
        break;
      case 'delete':
        this.confirmDelete(targetId);
        break;
      case 'view':
        this.showDetailsModal(targetId);
        break;
      case 'start':
        await this.startCampaign(targetId);
        break;
      case 'stop':
        await this.stopCampaign(targetId);
        break;
      case 'export':
        await this.exportData(targetId);
        break;
    }
  }

  async handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const action = form.dataset.action;

    try {
      let response;

      switch (action) {
        case 'create-campaign':
          response = await this.api.createCampaign(Object.fromEntries(formData));
          break;
        case 'update-campaign':
          response = await this.api.updateCampaign(form.dataset.id, Object.fromEntries(formData));
          break;
        case 'update-settings':
          response = await this.api.updateSettings(Object.fromEntries(formData));
          break;
      }

      if (response.success) {
        this.showNotification('Cập nhật thành công', 'success');
        this.closeModal();
        await this.reloadCurrentView();
      } else {
        this.showFormError(form, response.message);
      }
    } catch (error) {
      console.error('Form submit error:', error);
      this.showFormError(form, 'Có lỗi xảy ra');
    }
  }

  async loadDashboardData() {
    try {
      const [stats, recentActivity, alerts] = await Promise.all([
        this.api.get('/admin/stats'),
        this.api.get('/admin/recent-activity'),
        this.api.get('/admin/alerts')
      ]);

      this.dashboardData = { stats, recentActivity, alerts };
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      this.showNotification('Không thể tải dữ liệu dashboard', 'error');
    }
  }

  async loadCampaignsData() {
    try {
      this.campaignsData = await this.api.get('/admin/campaigns');
    } catch (error) {
      console.error('Failed to load campaigns data:', error);
    }
  }

  async loadVictimsData() {
    try {
      this.victimsData = await this.api.get('/admin/victims');
    } catch (error) {
      console.error('Failed to load victims data:', error);
    }
  }

  async loadAnalyticsData() {
    try {
      this.analyticsData = await this.api.get('/admin/analytics');
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    }
  }

  async loadSettingsData() {
    try {
      this.settingsData = await this.api.get('/admin/settings');
    } catch (error) {
      console.error('Failed to load settings data:', error);
    }
  }

  renderDashboard() {
    if (!this.dashboardData) return;

    const { stats, recentActivity, alerts } = this.dashboardData;

    // Update stats cards
    this.updateStatsCards(stats);

    // Update recent activity
    this.renderRecentActivity(recentActivity);

    // Update alerts
    this.renderAlerts(alerts);

    // Update charts
    this.renderCharts(stats);
  }

  renderCampaigns() {
    const container = document.getElementById('campaignsContainer');
    if (!container || !this.campaignsData) return;

    const html = this.campaignsData.map(campaign => `
      <div class="campaign-card" data-id="${campaign.id}">
        <div class="campaign-header">
          <h3>${campaign.name}</h3>
          <span class="status status-${campaign.status}">${campaign.status}</span>
        </div>
        <div class="campaign-stats">
          <div class="stat">
            <span class="label">Victims:</span>
            <span class="value">${campaign.victimCount}</span>
          </div>
          <div class="stat">
            <span class="label">Success Rate:</span>
            <span class="value">${campaign.successRate}%</span>
          </div>
        </div>
        <div class="campaign-actions">
          <button class="action-btn" data-action="view" data-id="${campaign.id}">View</button>
          <button class="action-btn" data-action="edit" data-id="${campaign.id}">Edit</button>
          <button class="action-btn" data-action="start" data-id="${campaign.id}" ${campaign.status === 'active' ? 'disabled' : ''}>Start</button>
          <button class="action-btn" data-action="stop" data-id="${campaign.id}" ${campaign.status !== 'active' ? 'disabled' : ''}>Stop</button>
        </div>
      </div>
    `).join('');

    container.innerHTML = html;
  }

  renderVictims() {
    const container = document.getElementById('victimsContainer');
    if (!container || !this.victimsData) return;

    const html = this.victimsData.map(victim => `
      <tr data-id="${victim.id}">
        <td>${victim.email}</td>
        <td>${victim.ip}</td>
        <td>${victim.device}</td>
        <td>${victim.capturedAt}</td>
        <td><span class="status status-${victim.status}">${victim.status}</span></td>
        <td>
          <button class="action-btn" data-action="view" data-id="${victim.id}">View</button>
          <button class="action-btn" data-action="delete" data-id="${victim.id}">Delete</button>
        </td>
      </tr>
    `).join('');

    container.innerHTML = html;
  }

  renderAnalytics() {
    if (!this.analyticsData) return;

    // Render charts and metrics
    this.renderAnalyticsCharts(this.analyticsData);
    this.renderAnalyticsMetrics(this.analyticsData);
  }

  renderSettings() {
    const container = document.getElementById('settingsContainer');
    if (!container || !this.settingsData) return;

    // Render settings form
    container.innerHTML = this.generateSettingsForm(this.settingsData);
  }

  updateStatsCards(stats) {
    Object.keys(stats).forEach(key => {
      const element = document.getElementById(`${key}Stat`);
      if (element) {
        element.textContent = stats[key];
      }
    });
  }

  renderRecentActivity(activities) {
    const container = document.getElementById('recentActivity');
    if (!container) return;

    const html = activities.map(activity => `
      <div class="activity-item">
        <div class="activity-icon ${activity.type}"></div>
        <div class="activity-content">
          <p>${activity.description}</p>
          <span class="activity-time">${activity.timestamp}</span>
        </div>
      </div>
    `).join('');

    container.innerHTML = html;
  }

  renderAlerts(alerts) {
    const container = document.getElementById('alertsContainer');
    if (!container) return;

    const html = alerts.map(alert => `
      <div class="alert alert-${alert.severity}">
        <span class="alert-icon"></span>
        <div class="alert-content">
          <h4>${alert.title}</h4>
          <p>${alert.message}</p>
        </div>
        <button class="alert-close" onclick="this.parentElement.remove()">&times;</button>
      </div>
    `).join('');

    container.innerHTML = html;
  }

  renderCharts(data) {
    // Initialize charts using a charting library
    if (typeof Chart !== 'undefined') {
      this.initCharts(data);
    }
  }

  renderSearchResults(results) {
    // Render search results based on current view
    switch (this.currentView) {
      case 'campaigns':
        this.renderCampaigns(results);
        break;
      case 'victims':
        this.renderVictims(results);
        break;
      // Add other views as needed
    }
  }

  applyFilter(filterType, filterValue) {
    // Apply filters to current view data
    this.currentFilters = this.currentFilters || {};
    this.currentFilters[filterType] = filterValue;

    this.reloadCurrentView();
  }

  async reloadCurrentView() {
    switch (this.currentView) {
      case 'overview':
        await this.loadDashboardData();
        this.renderDashboard();
        break;
      case 'campaigns':
        await this.loadCampaignsData();
        this.renderCampaigns();
        break;
      case 'victims':
        await this.loadVictimsData();
        this.renderVictims();
        break;
      case 'analytics':
        await this.loadAnalyticsData();
        this.renderAnalytics();
        break;
      case 'settings':
        await this.loadSettingsData();
        this.renderSettings();
        break;
    }
  }

  showEditModal(id) {
    // Show edit modal for the specified item
    const modal = document.getElementById('editModal');
    if (modal) {
      modal.style.display = 'block';
      // Populate modal with data
      this.populateEditModal(id);
    }
  }

  showDetailsModal(id) {
    // Show details modal for the specified item
    const modal = document.getElementById('detailsModal');
    if (modal) {
      modal.style.display = 'block';
      // Populate modal with data
      this.populateDetailsModal(id);
    }
  }

  confirmDelete(id) {
    if (confirm('Bạn có chắc chắn muốn xóa mục này?')) {
      this.deleteItem(id);
    }
  }

  async deleteItem(id) {
    try {
      const response = await this.api.delete(`/${this.currentView}/${id}`);
      if (response.success) {
        this.showNotification('Xóa thành công', 'success');
        await this.reloadCurrentView();
      } else {
        this.showNotification('Xóa thất bại', 'error');
      }
    } catch (error) {
      console.error('Delete error:', error);
      this.showNotification('Có lỗi xảy ra khi xóa', 'error');
    }
  }

  async startCampaign(id) {
    try {
      const response = await this.api.post(`/campaigns/${id}/start`);
      if (response.success) {
        this.showNotification('Chiến dịch đã được khởi động', 'success');
        await this.reloadCurrentView();
      }
    } catch (error) {
      this.showNotification('Không thể khởi động chiến dịch', 'error');
    }
  }

  async stopCampaign(id) {
    try {
      const response = await this.api.post(`/campaigns/${id}/stop`);
      if (response.success) {
        this.showNotification('Chiến dịch đã được dừng', 'success');
        await this.reloadCurrentView();
      }
    } catch (error) {
      this.showNotification('Không thể dừng chiến dịch', 'error');
    }
  }

  async exportData(type) {
    try {
      const response = await this.api.get(`/export/${type}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      this.showNotification('Xuất dữ liệu thất bại', 'error');
    }
  }

  closeModal() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
      modal.style.display = 'none';
    });
  }

  showFormError(form, message) {
    const errorElement = form.querySelector('.form-error');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
    }
  }

  showNotification(message, type = 'info') {
    // Use global notification system
    if (window.zaloPayApp && window.zaloPayApp.showNotification) {
      window.zaloPayApp.showNotification(message, type);
    } else {
      // Fallback notification
      alert(message);
    }
  }

  startRealTimeUpdates() {
    // Update dashboard data every 30 seconds
    setInterval(async () => {
      if (this.currentView === 'overview') {
        await this.loadDashboardData();
        this.renderDashboard();
      }
    }, 30000);

    // Check for new alerts every minute
    setInterval(async () => {
      try {
        const alerts = await this.api.get('/admin/alerts');
        this.renderAlerts(alerts);
      } catch (error) {
        console.error('Failed to fetch alerts:', error);
      }
    }, 60000);
  }

  // Placeholder methods for modal population
  populateEditModal(id) {
    // Implementation would populate the edit modal with data for the specified item
    console.log('Populating edit modal for item:', id);
  }

  populateDetailsModal(id) {
    // Implementation would populate the details modal with data for the specified item
    console.log('Populating details modal for item:', id);
  }

  generateSettingsForm(settings) {
    // Generate HTML for settings form
    return `
      <form class="admin-form" data-action="update-settings">
        <!-- Settings form fields would be generated here -->
        <button type="submit">Lưu thay đổi</button>
      </form>
    `;
  }

  // Remove unused variable
  unusedVariable() {
    // This method is not used
  }

  renderAnalyticsCharts(data) {
    // Implementation for rendering analytics charts
    console.log('Rendering analytics charts:', data);
  }

  renderAnalyticsMetrics(data) {
    // Implementation for rendering analytics metrics
    console.log('Rendering analytics metrics:', data);
  }

  initCharts(data) {
    // Implementation for initializing charts
    console.log('Initializing charts with data:', data);
  }
}

// Initialize admin app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.adminApp = new AdminApp();
});

// Export for testing
export default AdminApp;