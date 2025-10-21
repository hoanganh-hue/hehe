/**
 * Gmail WebSocket Manager
 * Handles real-time updates for all Gmail interfaces
 */

class GmailWebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.eventListeners = {};
        this.baseUrl = window.location.host;
    }

    /**
     * Initialize WebSocket connection
     */
    connect() {
        try {
            // Determine WebSocket URL based on current protocol
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${this.baseUrl}/ws/gmail`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = (event) => {
                this.onOpen(event);
            };

            this.ws.onmessage = (event) => {
                this.onMessage(event);
            };

            this.ws.onclose = (event) => {
                this.onClose(event);
            };

            this.ws.onerror = (error) => {
                this.onError(error);
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Handle WebSocket open event
     */
    onOpen(event) {
        console.log('Gmail WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;

        // Send identification message
        this.send({
            type: 'client_identification',
            interface: this.getCurrentInterface(),
            timestamp: new Date().toISOString()
        });

        this.emit('connected', { timestamp: new Date().toISOString() });
    }

    /**
     * Handle WebSocket message event
     */
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    /**
     * Handle WebSocket close event
     */
    onClose(event) {
        console.log('Gmail WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;

        if (event.code !== 1000) { // Not a normal closure
            this.scheduleReconnect();
        }

        this.emit('disconnected', {
            code: event.code,
            reason: event.reason,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Handle WebSocket error event
     */
    onError(error) {
        console.error('Gmail WebSocket error:', error);
        this.emit('error', { error, timestamp: new Date().toISOString() });
    }

    /**
     * Handle incoming message based on type
     */
    handleMessage(data) {
        switch(data.type) {
            case 'extraction_progress':
                this.emit('extraction_progress', data);
                break;
            case 'extraction_completed':
                this.emit('extraction_completed', data);
                break;
            case 'extraction_failed':
                this.emit('extraction_failed', data);
                break;
            case 'extraction_paused':
                this.emit('extraction_paused', data);
                break;
            case 'extraction_cancelled':
                this.emit('extraction_cancelled', data);
                break;
            case 'new_access_granted':
                this.emit('new_access_granted', data);
                break;
            case 'access_revoked':
                this.emit('access_revoked', data);
                break;
            case 'data_export_progress':
                this.emit('data_export_progress', data);
                break;
            case 'data_export_completed':
                this.emit('data_export_completed', data);
                break;
            case 'data_export_failed':
                this.emit('data_export_failed', data);
                break;
            case 'performance_metrics':
                this.emit('performance_metrics', data);
                break;
            case 'system_notification':
                this.emit('system_notification', data);
                break;
            case 'pong':
                // Handle ping/pong for connection keepalive
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    /**
     * Send message through WebSocket
     */
    send(data) {
        if (this.isConnected && this.ws) {
            try {
                this.ws.send(JSON.stringify(data));
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                return false;
            }
        }
        return false;
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.emit('max_reconnect_attempts_reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff

        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.eventListeners[event]) {
            const index = this.eventListeners[event].indexOf(callback);
            if (index > -1) {
                this.eventListeners[event].splice(index, 1);
            }
        }
    }

    /**
     * Emit event to all listeners
     */
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in event listener:', error);
                }
            });
        }
    }

    /**
     * Get current interface name based on URL
     */
    getCurrentInterface() {
        const path = window.location.pathname;
        const filename = path.substring(path.lastIndexOf('/') + 1);

        if (filename.includes('gmail_access')) return 'access';
        if (filename.includes('gmail_extraction_progress')) return 'extraction';
        if (filename.includes('gmail_data_viewer')) return 'viewer';
        if (filename.includes('gmail_export_interface')) return 'export';

        return 'unknown';
    }

    /**
     * Send ping to keep connection alive
     */
    ping() {
        this.send({ type: 'ping', timestamp: new Date().toISOString() });
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
        }
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            currentInterface: this.getCurrentInterface()
        };
    }
}

// Global instance
let gmailWS = null;

/**
 * Initialize Gmail WebSocket when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    if (typeof GmailWebSocketManager !== 'undefined') {
        gmailWS = new GmailWebSocketManager();
        gmailWS.connect();

        // Setup ping interval (every 30 seconds)
        setInterval(() => {
            if (gmailWS && gmailWS.isConnected) {
                gmailWS.ping();
            }
        }, 30000);
    }
});

/**
 * Utility function to get WebSocket instance
 */
function getGmailWebSocket() {
    return gmailWS;
}

/**
 * Utility function to send WebSocket message
 */
function sendGmailWSMessage(data) {
    if (gmailWS) {
        return gmailWS.send(data);
    }
    return false;
}