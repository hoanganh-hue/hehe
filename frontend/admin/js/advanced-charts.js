/**
 * Advanced Chart.js Framework for Security Dashboard
 * Provides advanced chart types, real-time updates, and interactive features
 * for phishing campaign visualization and security metrics
 */

class AdvancedChartFramework {
    constructor(options = {}) {
        this.options = {
            enableRealTime: true,
            updateInterval: 5000,
            maxDataPoints: 100,
            enableDrillDown: true,
            enableExport: true,
            locale: 'vi',
            ...options
        };

        this.charts = new Map();
        this.dataCache = new Map();
        this.webSocket = null;
        this.eventListeners = new Map();
        this.themes = this.initializeThemes();
        this.securityMetrics = this.initializeSecurityMetrics();

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.initializeSecurityChartTypes();
        this.setupGlobalEventListeners();
        this.loadUserPreferences();
    }

    /**
     * Initialize custom security-specific chart types
     */
    initializeSecurityChartTypes() {
        this.registerCustomChartTypes();
        this.createSecurityColorSchemes();
        this.setupSecurityMetrics();
    }

    /**
     * Register custom Chart.js chart types for security
     */
    registerCustomChartTypes() {
        Chart.register({
            id: 'threatRadar',
            type: 'radar',
            parsing: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        callback: (value) => `${value}%`
                    }
                }
            }
        });

        Chart.register({
            id: 'riskMatrix',
            type: 'scatter',
            parsing: false,
            scales: {
                x: {
                    title: { display: true, text: 'Khả năng xảy ra' },
                    min: 0,
                    max: 5,
                    ticks: { stepSize: 1 }
                },
                y: {
                    title: { display: true, text: 'Mức độ ảnh hưởng' },
                    min: 0,
                    max: 5,
                    ticks: { stepSize: 1 }
                }
            }
        });

        Chart.register({
            id: 'phishingFunnel',
            type: 'bar',
            parsing: false,
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    /**
     * Create security-specific color schemes
     */
    createSecurityColorSchemes() {
        this.securityColors = {
            threat: {
                critical: '#dc3545',
                high: '#fd7e14',
                medium: '#ffc107',
                low: '#28a745',
                info: '#17a2b8'
            },
            risk: {
                very_high: '#721c24',
                high: '#dc3545',
                medium: '#fd7e14',
                low: '#ffc107',
                very_low: '#28a745'
            },
            status: {
                success: '#28a745',
                warning: '#ffc107',
                danger: '#dc3545',
                info: '#17a2b8',
                secondary: '#6c757d'
            }
        };
    }

    /**
     * Initialize security metrics definitions
     */
    initializeSecurityMetrics() {
        return {
            threatLevel: {
                label: 'Mức độ đe dọa',
                unit: 'điểm',
                thresholds: { low: 25, medium: 50, high: 75, critical: 90 }
            },
            riskScore: {
                label: 'Điểm rủi ro',
                unit: 'điểm',
                thresholds: { low: 20, medium: 40, high: 60, very_high: 80 }
            },
            victimQuality: {
                label: 'Chất lượng nạn nhân',
                unit: 'điểm',
                thresholds: { poor: 30, fair: 50, good: 70, excellent: 90 }
            },
            campaignSuccess: {
                label: 'Thành công chiến dịch',
                unit: '%',
                thresholds: { low: 25, medium: 50, high: 75, excellent: 90 }
            }
        };
    }

    /**
     * Initialize chart themes
     */
    initializeThemes() {
        return {
            security: {
                name: 'Bảo mật',
                colors: {
                    primary: '#0068FF',
                    secondary: '#6c757d',
                    success: '#28a745',
                    danger: '#dc3545',
                    warning: '#ffc107',
                    info: '#17a2b8',
                    threat: '#8b0000',
                    safe: '#006400'
                },
                fonts: {
                    family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                    size: 12
                }
            },
            dark: {
                name: 'Tối',
                colors: {
                    primary: '#4f83cc',
                    secondary: '#adb5bd',
                    success: '#40c057',
                    danger: '#fa5252',
                    warning: '#ffd43b',
                    info: '#339af0',
                    background: '#212529',
                    surface: '#343a40',
                    text: '#ffffff'
                }
            },
            light: {
                name: 'Sáng',
                colors: {
                    primary: '#0068FF',
                    secondary: '#6c757d',
                    success: '#28a745',
                    danger: '#dc3545',
                    warning: '#ffc107',
                    info: '#17a2b8',
                    background: '#ffffff',
                    surface: '#f8f9fa',
                    text: '#212529'
                }
            }
        };
    }

    /**
     * Setup WebSocket connection for real-time updates
     */
    setupWebSocket() {
        if (!this.options.enableRealTime) return;

        try {
            this.webSocket = new WebSocketClient({
                url: this.getWebSocketUrl(),
                onMessage: this.handleWebSocketMessage.bind(this),
                onError: this.handleWebSocketError.bind(this),
                onClose: this.handleWebSocketClose.bind(this),
                reconnectInterval: 5000
            });
        } catch (error) {
            console.warn('WebSocket không khả dụng:', error);
        }
    }

    /**
     * Get WebSocket URL based on current location
     */
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/charts`;
    }

    /**
     * Handle WebSocket messages for real-time chart updates
     */
    handleWebSocketMessage(data) {
        if (data.type === 'chart_update') {
            this.updateChartData(data.chartId, data.data);
        } else if (data.type === 'metric_update') {
            this.updateSecurityMetrics(data.metrics);
        }
    }

    /**
     * Create Threat Level Radar Chart
     */
    createThreatRadarChart(canvasId, data = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultData = {
            labels: ['Phishing', 'Malware', 'Social Engineering', 'Network Attack', 'Data Breach', 'Insider Threat'],
            datasets: [{
                label: 'Mức độ đe dọa hiện tại',
                data: [65, 45, 80, 30, 55, 25],
                borderColor: this.securityColors.threat.high,
                backgroundColor: this.hexToRgba(this.securityColors.threat.high, 0.2),
                pointBackgroundColor: this.securityColors.threat.high,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: this.securityColors.threat.high
            }]
        };

        const chart = new Chart(ctx, {
            type: 'threatRadar',
            data: { ...defaultData, ...data },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { font: { family: this.themes.security.fonts.family } }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.r;
                                const threatLevel = this.getThreatLevel(value);
                                return `${context.label}: ${value}% - ${threatLevel}`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            callback: (value) => `${value}%`,
                            font: { family: this.themes.security.fonts.family }
                        },
                        pointLabels: {
                            font: {
                                family: this.themes.security.fonts.family,
                                size: 11
                            }
                        }
                    }
                },
                onClick: this.options.enableDrillDown ? this.handleDrillDown.bind(this) : null
            }
        });

        this.registerChart(canvasId, chart, 'threatRadar');
        return chart;
    }

    /**
     * Create Risk Assessment Matrix Chart
     */
    createRiskMatrixChart(canvasId, data = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultData = {
            datasets: [{
                label: 'Rủi ro bảo mật',
                data: [
                    { x: 4, y: 4, risk: 'very_high', label: 'Dữ liệu nhạy cảm' },
                    { x: 3, y: 3, risk: 'high', label: 'Thông tin cá nhân' },
                    { x: 2, y: 2, risk: 'medium', label: 'Thông tin nội bộ' },
                    { x: 1, y: 1, risk: 'low', label: 'Thông tin công khai' }
                ],
                backgroundColor: (context) => {
                    const risk = context.raw.risk;
                    return this.securityColors.risk[risk] || this.securityColors.risk.medium;
                },
                borderColor: '#fff',
                borderWidth: 2,
                pointRadius: (context) => {
                    const risk = context.raw.risk;
                    const radiusMap = { very_high: 12, high: 10, medium: 8, low: 6 };
                    return radiusMap[risk] || 8;
                }
            }]
        };

        const chart = new Chart(ctx, {
            type: 'riskMatrix',
            data: { ...defaultData, ...data },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { font: { family: this.themes.security.fonts.family } }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const point = context.raw;
                                return `${point.label}: ${this.getRiskLevel(point.x * point.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Khả năng xảy ra',
                            font: { family: this.themes.security.fonts.family }
                        },
                        ticks: {
                            callback: (value) => this.getLikelihoodLabel(value),
                            font: { family: this.themes.security.fonts.family }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Mức độ ảnh hưởng',
                            font: { family: this.themes.security.fonts.family }
                        },
                        ticks: {
                            callback: (value) => this.getImpactLabel(value),
                            font: { family: this.themes.security.fonts.family }
                        }
                    }
                },
                onClick: this.options.enableDrillDown ? this.handleDrillDown.bind(this) : null
            }
        });

        this.registerChart(canvasId, chart, 'riskMatrix');
        return chart;
    }

    /**
     * Create Phishing Campaign Funnel Chart
     */
    createPhishingFunnelChart(canvasId, data = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultData = {
            labels: [
                'Email đã gửi',
                'Email đã mở',
                'Link đã click',
                'Thông tin đã nhập',
                'Gmail đã truy cập',
                'BeEF đã hook'
            ],
            datasets: [{
                label: 'Quy trình Phishing',
                data: [10000, 7500, 3200, 1800, 450, 120],
                backgroundColor: [
                    this.securityColors.status.info,
                    this.securityColors.status.primary,
                    this.securityColors.status.warning,
                    this.securityColors.status.danger,
                    this.securityColors.threat.high,
                    this.securityColors.threat.critical
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        };

        const chart = new Chart(ctx, {
            type: 'phishingFunnel',
            data: { ...defaultData, ...data },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.x;
                                const previous = context.dataset.data[context.dataIndex - 1] || value;
                                const rate = previous > 0 ? ((value / previous) * 100).toFixed(1) : 0;
                                return `${context.label}: ${value.toLocaleString()} (${rate}% chuyển đổi)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Số lượng',
                            font: { family: this.themes.security.fonts.family }
                        },
                        ticks: {
                            font: { family: this.themes.security.fonts.family }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Giai đoạn',
                            font: { family: this.themes.security.fonts.family }
                        },
                        ticks: {
                            font: { family: this.themes.security.fonts.family }
                        }
                    }
                },
                onClick: this.options.enableDrillDown ? this.handleDrillDown.bind(this) : null
            }
        });

        this.registerChart(canvasId, chart, 'phishingFunnel');
        return chart;
    }

    /**
     * Create Real-time Timeline Chart
     */
    createRealtimeTimelineChart(canvasId, data = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultData = {
            labels: this.generateTimeLabels(60), // Last 60 minutes
            datasets: [
                {
                    label: 'Nạn nhân mới',
                    data: new Array(60).fill(0),
                    borderColor: this.securityColors.threat.high,
                    backgroundColor: this.hexToRgba(this.securityColors.threat.high, 0.1),
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Gmail truy cập',
                    data: new Array(60).fill(0),
                    borderColor: this.securityColors.status.warning,
                    backgroundColor: this.hexToRgba(this.securityColors.status.warning, 0.1),
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'BeEF sessions',
                    data: new Array(60).fill(0),
                    borderColor: this.securityColors.status.success,
                    backgroundColor: this.hexToRgba(this.securityColors.status.success, 0.1),
                    tension: 0.4,
                    fill: true
                }
            ]
        };

        const chart = new Chart(ctx, {
            type: 'line',
            data: { ...defaultData, ...data },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 500,
                    easing: 'easeInOutQuart'
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Thời gian',
                            font: { family: this.themes.security.fonts.family }
                        },
                        ticks: {
                            font: { family: this.themes.security.fonts.family }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Số lượng',
                            font: { family: this.themes.security.fonts.family }
                        },
                        ticks: {
                            font: { family: this.themes.security.fonts.family }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { font: { family: this.themes.security.fonts.family } }
                    }
                },
                onClick: this.options.enableDrillDown ? this.handleDrillDown.bind(this) : null
            }
        });

        this.registerChart(canvasId, chart, 'realtimeTimeline');
        this.startRealTimeUpdates(canvasId);

        return chart;
    }

    /**
     * Create Geographic Heat Map Chart
     */
    createGeographicHeatMapChart(canvasId, data = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultData = {
            labels: ['Việt Nam', 'Hoa Kỳ', 'Anh', 'Canada', 'Úc', 'Singapore', 'Malaysia', 'Khác'],
            datasets: [{
                label: 'Nạn nhân theo quốc gia',
                data: [45, 20, 15, 10, 5, 3, 2, 0],
                backgroundColor: (context) => {
                    const value = context.parsed;
                    const intensity = Math.min(value / 50, 1);
                    return `rgba(220, 53, 69, ${intensity})`;
                },
                borderColor: this.securityColors.threat.medium,
                borderWidth: 2
            }]
        };

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: { ...defaultData, ...data },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { family: this.themes.security.fonts.family }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                onClick: this.options.enableDrillDown ? this.handleDrillDown.bind(this) : null
            }
        });

        this.registerChart(canvasId, chart, 'geographicHeatMap');
        return chart;
    }

    /**
     * Register chart with framework
     */
    registerChart(canvasId, chart, type) {
        this.charts.set(canvasId, {
            chart: chart,
            type: type,
            createdAt: new Date(),
            lastUpdated: new Date(),
            dataPoints: 0
        });

        // Setup chart event listeners
        this.setupChartEventListeners(canvasId, chart);
    }

    /**
     * Setup event listeners for chart interactions
     */
    setupChartEventListeners(canvasId, chart) {
        chart.canvas.addEventListener('click', (event) => {
            if (this.options.enableDrillDown) {
                this.handleDrillDown(event, canvasId, chart);
            }
        });

        // Add hover effects
        chart.canvas.addEventListener('mouseenter', () => {
            chart.canvas.style.cursor = 'pointer';
        });

        chart.canvas.addEventListener('mouseleave', () => {
            chart.canvas.style.cursor = 'default';
        });
    }

    /**
     * Handle drill-down interactions
     */
    handleDrillDown(event, canvasId, chart) {
        const points = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true);

        if (points.length > 0) {
            const point = points[0];
            const dataset = chart.data.datasets[point.datasetIndex];
            const data = dataset.data[point.index];
            const label = chart.data.labels[point.index];

            // Emit drill-down event
            this.emit('drillDown', {
                canvasId,
                chartType: chart.type || 'unknown',
                label,
                value: data,
                dataset: dataset.label,
                rawData: chart.data
            });

            // Show drill-down modal or navigate to detail view
            this.showDrillDownDetails(canvasId, label, data);
        }
    }

    /**
     * Show drill-down details
     */
    showDrillDownDetails(canvasId, label, value) {
        // Implementation would show modal with detailed information
        console.log(`Drill-down: ${label} = ${value}`);

        // You can customize this to show modals, navigate to detail pages, etc.
        this.showToast(`Xem chi tiết: ${label}`, 'info');
    }

    /**
     * Start real-time updates for a chart
     */
    startRealTimeUpdates(canvasId) {
        if (!this.options.enableRealTime) return;

        const updateInterval = setInterval(() => {
            this.updateChartData(canvasId);
        }, this.options.updateInterval);

        // Store interval for cleanup
        if (!this.charts.has(canvasId)) return;
        this.charts.get(canvasId).updateInterval = updateInterval;
    }

    /**
     * Update chart data with new values
     */
    updateChartData(canvasId, newData = null) {
        const chartInfo = this.charts.get(canvasId);
        if (!chartInfo) return;

        const chart = chartInfo.chart;

        if (newData) {
            // Update with provided data
            Object.assign(chart.data, newData);
        } else {
            // Generate mock real-time data
            this.generateRealtimeData(chart);
        }

        // Update chart with smooth animation
        chart.update({
            duration: 750,
            easing: 'easeInOutQuart'
        });

        chartInfo.lastUpdated = new Date();
        chartInfo.dataPoints++;

        // Limit data points to prevent memory issues
        if (chartInfo.dataPoints > this.options.maxDataPoints) {
            this.trimChartData(chart);
        }
    }

    /**
     * Generate real-time data for charts
     */
    generateRealtimeData(chart) {
        if (chart.type === 'line') {
            // Add new data point to line charts
            chart.data.labels.push(new Date().toLocaleTimeString());

            chart.data.datasets.forEach(dataset => {
                const lastValue = dataset.data[dataset.data.length - 1] || 0;
                const newValue = Math.max(0, lastValue + (Math.random() - 0.5) * 10);
                dataset.data.push(Math.round(newValue));
            });

            // Remove old data points
            if (chart.data.labels.length > 60) {
                chart.data.labels.shift();
                chart.data.datasets.forEach(dataset => dataset.data.shift());
            }
        }
    }

    /**
     * Trim chart data to prevent memory issues
     */
    trimChartData(chart) {
        const maxPoints = Math.floor(this.options.maxDataPoints * 0.8);

        if (chart.data.labels && chart.data.labels.length > maxPoints) {
            const trimCount = chart.data.labels.length - maxPoints;
            chart.data.labels.splice(0, trimCount);

            chart.data.datasets.forEach(dataset => {
                if (Array.isArray(dataset.data)) {
                    dataset.data.splice(0, trimCount);
                }
            });
        }
    }

    /**
     * Update security metrics across all charts
     */
    updateSecurityMetrics(metrics) {
        this.securityMetrics = { ...this.securityMetrics, ...metrics };

        // Update all security-related charts
        this.charts.forEach((chartInfo, canvasId) => {
            if (['threatRadar', 'riskMatrix'].includes(chartInfo.type)) {
                this.updateChartData(canvasId);
            }
        });
    }

    /**
     * Setup global event listeners
     */
    setupGlobalEventListeners() {
        // Handle theme changes
        window.addEventListener('themeChange', (event) => {
            this.applyTheme(event.detail.theme);
        });

        // Handle locale changes
        window.addEventListener('localeChange', (event) => {
            this.applyLocale(event.detail.locale);
        });

        // Handle window resize for responsive charts
        window.addEventListener('resize', this.debounce(() => {
            this.resizeAllCharts();
        }, 250));
    }

    /**
     * Apply theme to all charts
     */
    applyTheme(themeName) {
        const theme = this.themes[themeName];
        if (!theme) return;

        this.charts.forEach((chartInfo) => {
            const chart = chartInfo.chart;
            chart.options = this.mergeDeep(chart.options, {
                plugins: {
                    legend: {
                        labels: {
                            font: { family: theme.fonts.family }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            font: { family: theme.fonts.family }
                        },
                        title: {
                            font: { family: theme.fonts.family }
                        }
                    },
                    y: {
                        ticks: {
                            font: { family: theme.fonts.family }
                        },
                        title: {
                            font: { family: theme.fonts.family }
                        }
                    }
                }
            });

            chart.update();
        });
    }

    /**
     * Apply locale to all charts
     */
    applyLocale(locale) {
        this.options.locale = locale;

        // Update chart labels based on locale
        this.charts.forEach((chartInfo) => {
            this.localizeChart(chartInfo.chart);
        });
    }

    /**
     * Localize chart labels
     */
    localizeChart(chart) {
        // Implementation would translate labels based on locale
        // For now, just update the chart
        chart.update();
    }

    /**
     * Resize all charts for responsiveness
     */
    resizeAllCharts() {
        this.charts.forEach((chartInfo) => {
            const chart = chartInfo.chart;
            chart.resize();
        });
    }

    /**
     * Export chart functionality
     */
    exportChart(canvasId, format = 'png', filename = null) {
        const chartInfo = this.charts.get(canvasId);
        if (!chartInfo) return;

        const chart = chartInfo.chart;
        const canvas = chart.canvas;

        if (format === 'png') {
            this.downloadCanvas(canvas, filename || `chart_${canvasId}.png`);
        } else if (format === 'svg') {
            this.exportAsSVG(chart, filename);
        } else if (format === 'pdf') {
            this.exportAsPDF(chart, filename);
        }
    }

    /**
     * Download canvas as image
     */
    downloadCanvas(canvas, filename) {
        const link = document.createElement('a');
        link.download = filename;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }

    /**
     * Export chart as SVG
     */
    exportAsSVG(chart, filename) {
        // Implementation would convert chart to SVG
        console.log(`Exporting ${chart.type} as SVG`);
        this.showToast('Tính năng xuất SVG đang được phát triển', 'info');
    }

    /**
     * Export chart as PDF
     */
    exportAsPDF(chart, filename) {
        // Implementation would convert chart to PDF
        console.log(`Exporting ${chart.type} as PDF`);
        this.showToast('Tính năng xuất PDF đang được phát triển', 'info');
    }

    /**
     * Utility functions
     */
    getThreatLevel(value) {
        if (value >= 90) return 'Nguy hiểm cao';
        if (value >= 75) return 'Cao';
        if (value >= 50) return 'Trung bình';
        if (value >= 25) return 'Thấp';
        return 'Rất thấp';
    }

    getRiskLevel(score) {
        if (score >= 20) return 'Rủi ro rất cao';
        if (score >= 15) return 'Rủi ro cao';
        if (score >= 10) return 'Rủi ro trung bình';
        if (score >= 5) return 'Rủi ro thấp';
        return 'Rủi ro rất thấp';
    }

    getLikelihoodLabel(value) {
        const labels = ['Rất thấp', 'Thấp', 'Trung bình', 'Cao', 'Rất cao'];
        return labels[value - 1] || 'Không xác định';
    }

    getImpactLabel(value) {
        const labels = ['Không đáng kể', 'Nhỏ', 'Trung bình', 'Lớn', 'Thảm họa'];
        return labels[value - 1] || 'Không xác định';
    }

    generateTimeLabels(minutes) {
        const labels = [];
        const now = new Date();

        for (let i = minutes - 1; i >= 0; i--) {
            const time = new Date(now.getTime() - (i * 60 * 1000));
            labels.push(time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        }

        return labels;
    }

    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    mergeDeep(target, source) {
        const result = { ...target };

        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this.mergeDeep(target[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }

        return result;
    }

    showToast(message, type = 'info') {
        // Simple toast implementation - you can replace with your toast system
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    /**
     * Event system for chart interactions
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
     * Load user preferences
     */
    loadUserPreferences() {
        try {
            const preferences = localStorage.getItem('advancedChartPreferences');
            if (preferences) {
                this.options = { ...this.options, ...JSON.parse(preferences) };
            }
        } catch (error) {
            console.warn('Không thể tải tùy chọn người dùng:', error);
        }
    }

    /**
     * Save user preferences
     */
    saveUserPreferences() {
        try {
            localStorage.setItem('advancedChartPreferences', JSON.stringify(this.options));
        } catch (error) {
            console.warn('Không thể lưu tùy chọn người dùng:', error);
        }
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        // Clear all intervals
        this.charts.forEach((chartInfo) => {
            if (chartInfo.updateInterval) {
                clearInterval(chartInfo.updateInterval);
            }
        });

        // Destroy all charts
        this.charts.forEach((chartInfo) => {
            if (chartInfo.chart && typeof chartInfo.chart.destroy === 'function') {
                chartInfo.chart.destroy();
            }
        });

        // Close WebSocket
        if (this.webSocket) {
            this.webSocket.close();
        }

        this.charts.clear();
        this.dataCache.clear();
        this.eventListeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedChartFramework;
}

// Make available globally
window.AdvancedChartFramework = AdvancedChartFramework;