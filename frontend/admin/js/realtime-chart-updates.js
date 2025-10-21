/**
 * Real-time Chart Updates System
 * Handles WebSocket integration, performance optimization, and smooth
 * transitions for real-time chart updates in the security dashboard
 */

class RealTimeChartUpdates {
    constructor(options = {}) {
        this.options = {
            updateInterval: 5000,
            maxDataPoints: 100,
            enableWebSocket: true,
            enablePerformanceOptimization: true,
            enableSmoothTransitions: true,
            reconnectInterval: 5000,
            maxReconnectAttempts: 10,
            ...options
        };

        this.webSocket = null;
        this.updateIntervals = new Map();
        this.dataBuffers = new Map();
        this.performanceMetrics = new Map();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.eventListeners = new Map();

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupPerformanceMonitoring();
        this.setupVisibilityChangeHandler();
        this.setupNetworkStatusHandler();
    }

    /**
     * Setup WebSocket connection for real-time data
     */
    setupWebSocket() {
        if (!this.options.enableWebSocket) return;

        try {
            this.webSocket = new WebSocketClient({
                url: this.getWebSocketUrl(),
                onMessage: this.handleWebSocketMessage.bind(this),
                onOpen: this.handleWebSocketOpen.bind(this),
                onClose: this.handleWebSocketClose.bind(this),
                onError: this.handleWebSocketError.bind(this),
                reconnectInterval: this.options.reconnectInterval,
                maxReconnectAttempts: this.options.maxReconnectAttempts
            });

            this.webSocket.connect();
        } catch (error) {
            console.warn('Không thể khởi tạo WebSocket:', error);
            this.setupPollingFallback();
        }
    }

    /**
     * Get WebSocket URL based on current location
     */
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/charts/realtime`;
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(data) {
        try {
            const message = typeof data === 'string' ? JSON.parse(data) : data;

            switch (message.type) {
                case 'chart_data_update':
                    this.handleChartDataUpdate(message);
                    break;
                case 'security_metrics_update':
                    this.handleSecurityMetricsUpdate(message);
                    break;
                case 'system_status_update':
                    this.handleSystemStatusUpdate(message);
                    break;
                case 'bulk_update':
                    this.handleBulkUpdate(message);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Lỗi xử lý tin nhắn WebSocket:', error);
        }
    }

    /**
     * Handle chart data updates
     */
    handleChartDataUpdate(message) {
        const { chartId, data, timestamp } = message;

        // Buffer data for smooth updates
        if (!this.dataBuffers.has(chartId)) {
            this.dataBuffers.set(chartId, []);
        }

        this.dataBuffers.get(chartId).push({
            data,
            timestamp,
            receivedAt: Date.now()
        });

        // Process buffer if it gets too large
        if (this.dataBuffers.get(chartId).length > 10) {
            this.processDataBuffer(chartId);
        }

        this.emit('chartDataReceived', { chartId, data, timestamp });
    }

    /**
     * Handle security metrics updates
     */
    handleSecurityMetricsUpdate(message) {
        const { metrics, timestamp } = message;

        // Update all security-related charts
        this.emit('securityMetricsUpdated', { metrics, timestamp });

        // Update performance metrics
        this.updatePerformanceMetrics('security_metrics', {
            processedAt: Date.now(),
            dataSize: JSON.stringify(metrics).length
        });
    }

    /**
     * Handle system status updates
     */
    handleSystemStatusUpdate(message) {
        const { status, serverTime, uptime } = message;

        this.isConnected = status === 'connected';
        this.serverTimeOffset = serverTime - Date.now();

        this.emit('systemStatusUpdated', { status, serverTime, uptime });
    }

    /**
     * Handle bulk updates for multiple charts
     */
    handleBulkUpdate(message) {
        const { updates, timestamp } = message;

        updates.forEach(update => {
            this.handleChartDataUpdate({
                chartId: update.chartId,
                data: update.data,
                timestamp
            });
        });
    }

    /**
     * Setup polling fallback when WebSocket is not available
     */
    setupPollingFallback() {
        console.log('Sử dụng polling fallback cho real-time updates');

        // Poll for updates every 10 seconds
        setInterval(() => {
            this.pollForUpdates();
        }, 10000);
    }

    /**
     * Poll for updates from REST API
     */
    async pollForUpdates() {
        try {
            const response = await fetch('/api/admin/dashboard/realtime-data');
            const data = await response.json();

            if (data.charts) {
                Object.entries(data.charts).forEach(([chartId, chartData]) => {
                    this.handleChartDataUpdate({
                        chartId,
                        data: chartData,
                        timestamp: data.timestamp
                    });
                });
            }
        } catch (error) {
            console.error('Lỗi polling dữ liệu:', error);
        }
    }

    /**
     * Start real-time updates for specific chart
     */
    startChartUpdates(chartId, updateInterval = null) {
        const interval = updateInterval || this.options.updateInterval;

        // Clear existing interval if any
        if (this.updateIntervals.has(chartId)) {
            clearInterval(this.updateIntervals.get(chartId));
        }

        // Create new update interval
        const updateFunction = () => {
            this.updateChart(chartId);
        };

        const intervalId = setInterval(updateFunction, interval);
        this.updateIntervals.set(chartId, intervalId);

        console.log(`Đã bắt đầu cập nhật thời gian thực cho chart: ${chartId}`);
    }

    /**
     * Stop real-time updates for specific chart
     */
    stopChartUpdates(chartId) {
        if (this.updateIntervals.has(chartId)) {
            clearInterval(this.updateIntervals.get(chartId));
            this.updateIntervals.delete(chartId);
            console.log(`Đã dừng cập nhật thời gian thực cho chart: ${chartId}`);
        }
    }

    /**
     * Update chart with new data
     */
    updateChart(chartId) {
        // Process any buffered data first
        this.processDataBuffer(chartId);

        // Get chart instance from either framework
        const chart = this.getChartInstance(chartId);
        if (!chart) return;

        // Generate or fetch new data
        const newData = this.generateChartUpdateData(chartId, chart);

        if (newData) {
            this.applyChartUpdate(chart, newData);
        }
    }

    /**
     * Process buffered data for smooth updates
     */
    processDataBuffer(chartId) {
        const buffer = this.dataBuffers.get(chartId);
        if (!buffer || buffer.length === 0) return;

        // Sort by timestamp to ensure correct order
        buffer.sort((a, b) => a.timestamp - b.timestamp);

        // Process all buffered updates
        buffer.forEach(item => {
            this.applyBufferedUpdate(chartId, item);
        });

        // Clear buffer
        this.dataBuffers.set(chartId, []);
    }

    /**
     * Apply buffered update to chart
     */
    applyBufferedUpdate(chartId, bufferedItem) {
        const chart = this.getChartInstance(chartId);
        if (!chart) return;

        const { data, timestamp } = bufferedItem;

        // Apply the update based on chart type
        if (chart.type === 'line') {
            this.updateLineChart(chart, data, timestamp);
        } else if (chart.type === 'radar') {
            this.updateRadarChart(chart, data, timestamp);
        } else if (chart.type === 'doughnut' || chart.type === 'pie') {
            this.updatePieChart(chart, data, timestamp);
        } else if (chart.type === 'bar') {
            this.updateBarChart(chart, data, timestamp);
        }

        // Update performance metrics
        this.updatePerformanceMetrics(chartId, {
            updatedAt: Date.now(),
            dataAge: Date.now() - timestamp
        });
    }

    /**
     * Update line chart with smooth animation
     */
    updateLineChart(chart, data, timestamp) {
        if (!data.labels || !data.datasets) return;

        // Add new data point with timestamp
        const timeLabel = new Date(timestamp).toLocaleTimeString();

        if (this.options.enableSmoothTransitions) {
            // Animate the addition of new data
            chart.data.labels.push(timeLabel);
            data.datasets.forEach((newDataset, index) => {
                if (chart.data.datasets[index]) {
                    chart.data.datasets[index].data.push(newDataset.data[newDataset.data.length - 1]);
                }
            });

            // Animate the update
            chart.update({
                duration: 750,
                easing: 'easeInOutQuart'
            });
        } else {
            // Direct update without animation
            chart.data.labels = data.labels;
            chart.data.datasets = data.datasets;
            chart.update('none');
        }

        // Trim old data points
        this.trimChartData(chart);
    }

    /**
     * Update radar chart
     */
    updateRadarChart(chart, data, timestamp) {
        if (data.datasets && data.datasets[0]) {
            chart.data.datasets[0].data = data.datasets[0].data;

            chart.update({
                duration: 500,
                easing: 'easeInOutCubic'
            });
        }
    }

    /**
     * Update pie/doughnut chart
     */
    updatePieChart(chart, data, timestamp) {
        if (data.labels && data.datasets && data.datasets[0]) {
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.datasets[0].data;

            chart.update({
                duration: 800,
                easing: 'easeInOutQuart'
            });
        }
    }

    /**
     * Update bar chart
     */
    updateBarChart(chart, data, timestamp) {
        if (data.labels && data.datasets) {
            chart.data.labels = data.labels;
            chart.data.datasets = data.datasets;

            chart.update({
                duration: 600,
                easing: 'easeInOutCubic'
            });
        }
    }

    /**
     * Apply chart update with animation
     */
    applyChartUpdate(chart, newData) {
        if (this.options.enableSmoothTransitions) {
            // Animate the update
            Object.assign(chart.data, newData);

            chart.update({
                duration: 750,
                easing: 'easeInOutQuart'
            });
        } else {
            // Direct update
            Object.assign(chart.data, newData);
            chart.update('none');
        }

        // Trim data if necessary
        this.trimChartData(chart);
    }

    /**
     * Trim chart data to prevent memory issues
     */
    trimChartData(chart) {
        if (!chart.data.labels) return;

        const maxPoints = this.options.maxDataPoints;

        if (chart.data.labels.length > maxPoints) {
            const trimCount = chart.data.labels.length - maxPoints;

            // Remove old data points
            chart.data.labels.splice(0, trimCount);
            chart.data.datasets.forEach(dataset => {
                if (dataset.data) {
                    dataset.data.splice(0, trimCount);
                }
            });
        }
    }

    /**
     * Generate mock update data for testing
     */
    generateChartUpdateData(chartId, chart) {
        // This would normally fetch real data from API
        // For now, generating mock data for demonstration

        if (chart.type === 'line') {
            return {
                labels: chart.data.labels.slice(-20), // Keep last 20 points
                datasets: chart.data.datasets.map(dataset => ({
                    ...dataset,
                    data: [
                        ...dataset.data.slice(-19), // Keep last 19 points
                        Math.max(0, (dataset.data[dataset.data.length - 1] || 0) + (Math.random() - 0.5) * 5)
                    ]
                }))
            };
        }

        return null;
    }

    /**
     * Get chart instance from frameworks
     */
    getChartInstance(chartId) {
        // Try to get from Advanced Chart Framework first
        if (window.advancedChartFramework && window.advancedChartFramework.charts.has(chartId)) {
            return window.advancedChartFramework.charts.get(chartId).chart;
        }

        // Try to get from Dashboard Charts
        if (window.dashboardCharts && window.dashboardCharts.charts[chartId]) {
            return window.dashboardCharts.charts[chartId];
        }

        // Try to get by ID from DOM
        const canvas = document.getElementById(chartId);
        if (canvas && canvas.chart) {
            return canvas.chart;
        }

        return null;
    }

    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        if (!this.options.enablePerformanceOptimization) return;

        // Monitor frame rate
        this.monitorFrameRate();

        // Monitor memory usage
        this.monitorMemoryUsage();

        // Monitor update frequency
        setInterval(() => {
            this.analyzePerformance();
        }, 30000); // Every 30 seconds
    }

    /**
     * Monitor frame rate for smooth animations
     */
    monitorFrameRate() {
        let frameCount = 0;
        let lastTime = performance.now();
        let fps = 0;

        const measureFPS = () => {
            frameCount++;
            const currentTime = performance.now();

            if (currentTime - lastTime >= 1000) {
                fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                frameCount = 0;
                lastTime = currentTime;

                this.updatePerformanceMetrics('fps', {
                    value: fps,
                    timestamp: Date.now()
                });

                // Adjust update intervals based on performance
                this.adjustUpdateIntervals(fps);
            }

            requestAnimationFrame(measureFPS);
        };

        requestAnimationFrame(measureFPS);
    }

    /**
     * Monitor memory usage
     */
    monitorMemoryUsage() {
        if ('memory' in performance) {
            setInterval(() => {
                const memoryInfo = performance.memory;

                this.updatePerformanceMetrics('memory', {
                    used: memoryInfo.usedJSHeapSize,
                    total: memoryInfo.totalJSHeapSize,
                    limit: memoryInfo.jsHeapSizeLimit,
                    usagePercent: (memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit) * 100,
                    timestamp: Date.now()
                });
            }, 10000); // Every 10 seconds
        }
    }

    /**
     * Analyze performance and optimize
     */
    analyzePerformance() {
        const fpsMetrics = this.performanceMetrics.get('fps') || [];
        const memoryMetrics = this.performanceMetrics.get('memory') || [];

        const recentFPS = fpsMetrics.slice(-10); // Last 10 measurements
        const recentMemory = memoryMetrics.slice(-5); // Last 5 measurements

        const avgFPS = recentFPS.reduce((sum, m) => sum + m.value, 0) / recentFPS.length;
        const avgMemoryUsage = recentMemory.reduce((sum, m) => sum + m.usagePercent, 0) / recentMemory.length;

        // Adjust performance based on metrics
        if (avgFPS < 30) {
            this.reduceUpdateFrequency();
        } else if (avgFPS > 50 && avgMemoryUsage < 70) {
            this.increaseUpdateFrequency();
        }

        this.emit('performanceAnalyzed', {
            avgFPS,
            avgMemoryUsage,
            recommendations: this.generatePerformanceRecommendations(avgFPS, avgMemoryUsage)
        });
    }

    /**
     * Adjust update intervals based on FPS
     */
    adjustUpdateIntervals(fps) {
        this.updateIntervals.forEach((intervalId, chartId) => {
            let newInterval = this.options.updateInterval;

            if (fps < 30) {
                newInterval = this.options.updateInterval * 2; // Slow down
            } else if (fps > 50) {
                newInterval = Math.max(this.options.updateInterval * 0.8, 1000); // Speed up but not too fast
            }

            // Restart interval with new timing
            this.stopChartUpdates(chartId);
            this.startChartUpdates(chartId, newInterval);
        });
    }

    /**
     * Reduce update frequency for better performance
     */
    reduceUpdateFrequency() {
        const newInterval = this.options.updateInterval * 1.5;

        this.updateIntervals.forEach((intervalId, chartId) => {
            this.stopChartUpdates(chartId);
            this.startChartUpdates(chartId, newInterval);
        });

        console.log('Giảm tần suất cập nhật để tối ưu hiệu suất');
    }

    /**
     * Increase update frequency for better responsiveness
     */
    increaseUpdateFrequency() {
        const newInterval = this.options.updateInterval * 0.9;

        this.updateIntervals.forEach((intervalId, chartId) => {
            this.stopChartUpdates(chartId);
            this.startChartUpdates(chartId, newInterval);
        });

        console.log('Tăng tần suất cập nhật để cải thiện khả năng phản hồi');
    }

    /**
     * Generate performance recommendations
     */
    generatePerformanceRecommendations(avgFPS, avgMemoryUsage) {
        const recommendations = [];

        if (avgFPS < 30) {
            recommendations.push('FPS thấp - hãy giảm số lượng biểu đồ hoặc tần suất cập nhật');
        }

        if (avgMemoryUsage > 80) {
            recommendations.push('Bộ nhớ sử dụng cao - hãy giảm số điểm dữ liệu hoặc tăng khoảng thời gian cập nhật');
        }

        if (recommendations.length === 0) {
            recommendations.push('Hiệu suất tốt - không cần tối ưu thêm');
        }

        return recommendations;
    }

    /**
     * Update performance metrics
     */
    updatePerformanceMetrics(metricType, data) {
        if (!this.performanceMetrics.has(metricType)) {
            this.performanceMetrics.set(metricType, []);
        }

        const metrics = this.performanceMetrics.get(metricType);
        metrics.push(data);

        // Keep only last 100 measurements
        if (metrics.length > 100) {
            metrics.splice(0, metrics.length - 100);
        }
    }

    /**
     * Setup visibility change handler for performance optimization
     */
    setupVisibilityChangeHandler() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page is hidden - reduce update frequency
                this.pauseUpdates();
            } else {
                // Page is visible - resume normal updates
                this.resumeUpdates();
            }
        });
    }

    /**
     * Setup network status handler
     */
    setupNetworkStatusHandler() {
        window.addEventListener('online', () => {
            this.handleNetworkStatusChange(true);
        });

        window.addEventListener('offline', () => {
            this.handleNetworkStatusChange(false);
        });
    }

    /**
     * Handle network status changes
     */
    handleNetworkStatusChange(isOnline) {
        if (isOnline) {
            // Network back online - resume WebSocket connection
            if (this.webSocket) {
                this.webSocket.connect();
            }
            this.resumeUpdates();
        } else {
            // Network offline - pause updates and switch to cached data
            this.pauseUpdates();
            this.useCachedData();
        }

        this.emit('networkStatusChanged', { isOnline });
    }

    /**
     * Pause all chart updates
     */
    pauseUpdates() {
        this.updateIntervals.forEach((intervalId, chartId) => {
            clearInterval(intervalId);
        });

        this.updateIntervals.clear();
        console.log('Đã tạm dừng tất cả cập nhật biểu đồ');
    }

    /**
     * Resume all chart updates
     */
    resumeUpdates() {
        // Get all active charts and restart their updates
        const activeCharts = new Set([
            ...Array.from(this.updateIntervals.keys()),
            ...Array.from(this.dataBuffers.keys())
        ]);

        activeCharts.forEach(chartId => {
            this.startChartUpdates(chartId);
        });

        console.log('Đã tiếp tục cập nhật biểu đồ');
    }

    /**
     * Use cached data when offline
     */
    useCachedData() {
        console.log('Chuyển sang sử dụng dữ liệu cache khi offline');

        // Implementation would use previously cached data
        // For now, just log the action
    }

    /**
     * WebSocket event handlers
     */
    handleWebSocketOpen() {
        this.isConnected = true;
        this.reconnectAttempts = 0;

        // Send initial subscription message
        this.sendWebSocketMessage({
            type: 'subscribe',
            charts: Array.from(this.updateIntervals.keys()),
            timestamp: Date.now()
        });

        this.emit('connected', { timestamp: Date.now() });
    }

    handleWebSocketClose() {
        this.isConnected = false;
        this.emit('disconnected', { timestamp: Date.now() });
    }

    handleWebSocketError(error) {
        console.error('Lỗi WebSocket:', error);
        this.emit('error', { error, timestamp: Date.now() });
    }

    /**
     * Send message via WebSocket
     */
    sendWebSocketMessage(message) {
        if (this.webSocket && this.isConnected) {
            this.webSocket.send(JSON.stringify(message));
        }
    }

    /**
     * Subscribe to chart updates
     */
    subscribeToChart(chartId) {
        this.sendWebSocketMessage({
            type: 'subscribe_chart',
            chartId,
            timestamp: Date.now()
        });

        this.startChartUpdates(chartId);
    }

    /**
     * Unsubscribe from chart updates
     */
    unsubscribeFromChart(chartId) {
        this.sendWebSocketMessage({
            type: 'unsubscribe_chart',
            chartId,
            timestamp: Date.now()
        });

        this.stopChartUpdates(chartId);
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            lastUpdate: this.lastUpdateTime,
            performance: this.getPerformanceSummary()
        };
    }

    /**
     * Get performance summary
     */
    getPerformanceSummary() {
        const fpsMetrics = this.performanceMetrics.get('fps') || [];
        const memoryMetrics = this.performanceMetrics.get('memory') || [];

        const recentFPS = fpsMetrics.slice(-10);
        const recentMemory = memoryMetrics.slice(-5);

        return {
            averageFPS: recentFPS.length > 0 ? recentFPS.reduce((sum, m) => sum + m.value, 0) / recentFPS.length : 0,
            averageMemoryUsage: recentMemory.length > 0 ? recentMemory.reduce((sum, m) => sum + m.usagePercent, 0) / recentMemory.length : 0,
            dataBuffersSize: Array.from(this.dataBuffers.values()).reduce((sum, buffer) => sum + buffer.length, 0),
            activeIntervals: this.updateIntervals.size
        };
    }

    /**
     * Event system
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => callback(data));
        }
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        // Stop all intervals
        this.updateIntervals.forEach((intervalId) => {
            clearInterval(intervalId);
        });

        // Close WebSocket
        if (this.webSocket) {
            this.webSocket.close();
        }

        // Clear all data
        this.updateIntervals.clear();
        this.dataBuffers.clear();
        this.performanceMetrics.clear();
        this.eventListeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealTimeChartUpdates;
}

// Make available globally
window.RealTimeChartUpdates = RealTimeChartUpdates;