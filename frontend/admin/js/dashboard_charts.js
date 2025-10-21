/**
 * Enhanced Dashboard Charts Module
 * Integrates with Advanced Chart Framework for enhanced security visualization
 */

class DashboardCharts {
    constructor() {
        this.charts = {};
        this.advancedFramework = null;
        this.realTimeEnabled = true;
        this.exportEnabled = true;
        this.chartConfigs = {
            timeline: {
                type: 'line',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Count'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: 'white',
                            bodyColor: 'white',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1
                        }
                    }
                }
            },
            geographic: {
                type: 'doughnut',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            },
            performance: {
                type: 'bar',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Usage (%)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            },
            conversion: {
                type: 'funnel',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            }
        };
        
        this.colorPalette = {
            primary: '#007bff',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#17a2b8',
            secondary: '#6c757d',
            purple: '#6f42c1',
            pink: '#e83e8c',
            orange: '#fd7e14',
            teal: '#20c997'
        };
        
        this.init();
    }

    init() {
        this.initializeAdvancedFramework();
        this.initializeCharts();
        this.setupChartUpdates();
        this.setupInteractiveFeatures();
        this.setupExportFeatures();
    }

    /**
     * Initialize Advanced Chart Framework integration
     */
    initializeAdvancedFramework() {
        try {
            this.advancedFramework = new AdvancedChartFramework({
                enableRealTime: this.realTimeEnabled,
                updateInterval: 5000,
                enableDrillDown: true,
                enableExport: this.exportEnabled,
                locale: 'vi'
            });

            // Setup event listeners for advanced features
            this.setupAdvancedEventListeners();

        } catch (error) {
            console.warn('Không thể khởi tạo Advanced Chart Framework:', error);
        }
    }

    /**
     * Setup event listeners for advanced chart features
     */
    setupAdvancedEventListeners() {
        if (!this.advancedFramework) return;

        // Listen for drill-down events
        this.advancedFramework.on('drillDown', (data) => {
            this.handleChartDrillDown(data);
        });

        // Listen for real-time updates
        this.advancedFramework.on('realtimeUpdate', (data) => {
            this.handleRealtimeUpdate(data);
        });
    }
    
    initializeCharts() {
        // Initialize Timeline Chart
        this.createTimelineChart();
        
        // Initialize Geographic Chart
        this.createGeographicChart();
        
        // Initialize Performance Chart
        this.createPerformanceChart();
        
        // Initialize Conversion Funnel Chart
        this.createConversionChart();
        
        // Initialize Campaign Performance Chart
        this.createCampaignChart();
    }
    
    createTimelineChart() {
        const ctx = document.getElementById('victimTimelineChart');
        if (!ctx) return;
        
        this.charts.timeline = new Chart(ctx, {
            type: this.chartConfigs.timeline.type,
            data: {
                labels: this.generateTimeLabels(24), // Last 24 hours
                datasets: [
                    {
                        label: 'Victims Captured',
                        data: new Array(24).fill(0),
                        borderColor: this.colorPalette.danger,
                        backgroundColor: this.hexToRgba(this.colorPalette.danger, 0.1),
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Gmail Access',
                        data: new Array(24).fill(0),
                        borderColor: this.colorPalette.success,
                        backgroundColor: this.hexToRgba(this.colorPalette.success, 0.1),
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'BeEF Sessions',
                        data: new Array(24).fill(0),
                        borderColor: this.colorPalette.warning,
                        backgroundColor: this.hexToRgba(this.colorPalette.warning, 0.1),
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: this.chartConfigs.timeline.options
        });
    }
    
    createGeographicChart() {
        const ctx = document.getElementById('geographicChart');
        if (!ctx) return;
        
        this.charts.geographic = new Chart(ctx, {
            type: this.chartConfigs.geographic.type,
            data: {
                labels: ['Vietnam', 'United States', 'United Kingdom', 'Canada', 'Australia', 'Singapore', 'Malaysia', 'Other'],
                datasets: [{
                    data: [45, 20, 15, 10, 5, 3, 2, 0],
                    backgroundColor: [
                        this.colorPalette.danger,
                        this.colorPalette.primary,
                        this.colorPalette.success,
                        this.colorPalette.warning,
                        this.colorPalette.info,
                        this.colorPalette.purple,
                        this.colorPalette.pink,
                        this.colorPalette.secondary
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: this.chartConfigs.geographic.options
        });
    }
    
    createPerformanceChart() {
        const ctx = document.getElementById('systemPerformanceChart');
        if (!ctx) return;
        
        this.charts.performance = new Chart(ctx, {
            type: this.chartConfigs.performance.type,
            data: {
                labels: ['CPU Usage', 'Memory Usage', 'Disk Usage', 'Network I/O', 'Database', 'Proxy Pool'],
                datasets: [{
                    label: 'Current Usage (%)',
                    data: [25, 40, 15, 30, 20, 35],
                    backgroundColor: [
                        this.colorPalette.primary,
                        this.colorPalette.success,
                        this.colorPalette.warning,
                        this.colorPalette.danger,
                        this.colorPalette.info,
                        this.colorPalette.purple
                    ],
                    borderWidth: 1,
                    borderColor: '#fff'
                }]
            },
            options: this.chartConfigs.performance.options
        });
    }
    
    createConversionChart() {
        const ctx = document.getElementById('conversionChart');
        if (!ctx) return;
        
        // Custom funnel chart implementation
        this.charts.conversion = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Landing Page', 'OAuth Initiated', 'Credentials Captured', 'Gmail Access', 'BeEF Hooked', 'Data Exfiltrated'],
                datasets: [{
                    label: 'Conversion Funnel',
                    data: [1000, 750, 500, 300, 200, 150],
                    backgroundColor: [
                        this.hexToRgba(this.colorPalette.primary, 0.8),
                        this.hexToRgba(this.colorPalette.info, 0.8),
                        this.hexToRgba(this.colorPalette.success, 0.8),
                        this.hexToRgba(this.colorPalette.warning, 0.8),
                        this.hexToRgba(this.colorPalette.danger, 0.8),
                        this.hexToRgba(this.colorPalette.purple, 0.8)
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Stage'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const value = context.parsed.x;
                                const previousValue = context.dataset.data[context.dataIndex - 1] || value;
                                const conversionRate = ((value / previousValue) * 100).toFixed(1);
                                return `Conversion Rate: ${conversionRate}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    createCampaignChart() {
        const ctx = document.getElementById('campaignChart');
        if (!ctx) return;
        
        this.charts.campaign = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Reach', 'Engagement', 'Conversion', 'Quality', 'Speed', 'Stealth'],
                datasets: [
                    {
                        label: 'Campaign Performance',
                        data: [85, 70, 60, 90, 75, 95],
                        borderColor: this.colorPalette.primary,
                        backgroundColor: this.hexToRgba(this.colorPalette.primary, 0.2),
                        pointBackgroundColor: this.colorPalette.primary,
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: this.colorPalette.primary
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }
    
    setupChartUpdates() {
        // Update charts every 30 seconds
        setInterval(() => {
            this.updateAllCharts();
        }, 30000);
    }
    
    updateAllCharts() {
        this.updateTimelineChart();
        this.updateGeographicChart();
        this.updatePerformanceChart();
    }
    
    updateTimelineChart() {
        if (!this.charts.timeline) return;
        
        // Fetch latest data
        fetch('/api/admin/dashboard/timeline-data')
            .then(response => response.json())
            .then(data => {
                this.charts.timeline.data.labels = data.labels;
                this.charts.timeline.data.datasets[0].data = data.victims;
                this.charts.timeline.data.datasets[1].data = data.gmail;
                this.charts.timeline.data.datasets[2].data = data.beef;
                this.charts.timeline.update('none');
            })
            .catch(error => {
                console.error('Error updating timeline chart:', error);
            });
    }
    
    updateGeographicChart() {
        if (!this.charts.geographic) return;
        
        fetch('/api/admin/dashboard/geographic-data')
            .then(response => response.json())
            .then(data => {
                this.charts.geographic.data.labels = data.labels;
                this.charts.geographic.data.datasets[0].data = data.values;
                this.charts.geographic.update('none');
            })
            .catch(error => {
                console.error('Error updating geographic chart:', error);
            });
    }
    
    updatePerformanceChart() {
        if (!this.charts.performance) return;
        
        fetch('/api/admin/dashboard/performance-data')
            .then(response => response.json())
            .then(data => {
                this.charts.performance.data.datasets[0].data = [
                    data.cpu,
                    data.memory,
                    data.disk,
                    data.network,
                    data.database,
                    data.proxy
                ];
                this.charts.performance.update('none');
            })
            .catch(error => {
                console.error('Error updating performance chart:', error);
            });
    }
    
    addDataPoint(chartName, datasetIndex, value) {
        if (!this.charts[chartName]) return;
        
        const chart = this.charts[chartName];
        const dataset = chart.data.datasets[datasetIndex];
        
        // Add new data point
        dataset.data.push(value);
        
        // Remove oldest data point if we exceed max points
        if (dataset.data.length > 50) {
            dataset.data.shift();
            chart.data.labels.shift();
        }
        
        // Add new time label
        const now = new Date();
        chart.data.labels.push(now.toLocaleTimeString());
        
        chart.update('none');
    }
    
    updateMetricCard(metricId, value, change) {
        const element = document.getElementById(metricId);
        if (element) {
            element.textContent = value;
        }
        
        const changeElement = document.getElementById(metricId + 'Change');
        if (changeElement) {
            const changeText = change > 0 ? `+${change}` : change.toString();
            changeElement.textContent = `${changeText} today`;
            changeElement.className = `text-${change >= 0 ? 'success' : 'danger'}`;
        }
    }
    
    generateTimeLabels(hours) {
        const labels = [];
        const now = new Date();
        
        for (let i = hours - 1; i >= 0; i--) {
            const time = new Date(now.getTime() - (i * 60 * 60 * 1000));
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
    
    /**
     * Handle chart drill-down interactions
     */
    handleChartDrillDown(data) {
        console.log('Chart drill-down:', data);

        // Show detailed information based on chart type and data
        switch (data.chartType) {
            case 'threatRadar':
                this.showThreatDetails(data);
                break;
            case 'riskMatrix':
                this.showRiskDetails(data);
                break;
            case 'phishingFunnel':
                this.showFunnelDetails(data);
                break;
            default:
                this.showGenericDetails(data);
        }
    }

    /**
     * Show threat details from radar chart drill-down
     */
    showThreatDetails(data) {
        const modal = this.createDetailModal('Chi tiết mức độ đe dọa', `
            <div class="row">
                <div class="col-md-6">
                    <h6>Thông tin đe dọa</h6>
                    <p><strong>Loại:</strong> ${data.label}</p>
                    <p><strong>Mức độ:</strong> ${data.value}%</p>
                    <p><strong>Phân loại:</strong> ${this.getThreatLevel(data.value)}</p>
                </div>
                <div class="col-md-6">
                    <h6>Thống kê</h6>
                    <canvas id="threatDetailChart" width="300" height="200"></canvas>
                </div>
            </div>
        `);

        // Create mini chart for details
        setTimeout(() => {
            this.createThreatDetailChart(data);
        }, 100);
    }

    /**
     * Show risk details from matrix chart drill-down
     */
    showRiskDetails(data) {
        this.createDetailModal('Chi tiết rủi ro bảo mật', `
            <div class="alert alert-warning">
                <h6><i class="fas fa-exclamation-triangle"></i> Thông tin rủi ro</h6>
                <p><strong>Tên:</strong> ${data.label}</p>
                <p><strong>Điểm rủi ro:</strong> ${data.value}</p>
                <p><strong>Mức độ:</strong> ${this.getRiskLevel(data.value)}</p>
            </div>
            <div class="mt-3">
                <h6>Khuyến nghị xử lý</h6>
                <ul class="list-group">
                    <li class="list-group-item">Thực hiện đánh giá bảo mật chi tiết</li>
                    <li class="list-group-item">Áp dụng các biện pháp giảm thiểu rủi ro</li>
                    <li class="list-group-item">Theo dõi và cập nhật thường xuyên</li>
                </ul>
            </div>
        `);
    }

    /**
     * Show funnel details from phishing funnel chart drill-down
     */
    showFunnelDetails(data) {
        this.createDetailModal('Chi tiết quy trình Phishing', `
            <div class="row">
                <div class="col-12">
                    <div class="funnel-stage">
                        <h6>${data.label}</h6>
                        <div class="progress" style="height: 30px;">
                            <div class="progress-bar bg-danger" role="progressbar"
                                 style="width: ${data.value}%">
                                ${data.value.toLocaleString()} nạn nhân
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-6">
                    <h6>Tỷ lệ chuyển đổi</h6>
                    <p>Từ giai đoạn trước: <span class="badge badge-success">${this.calculateConversionRate(data)}%</span></p>
                </div>
                <div class="col-md-6">
                    <h6>Thời gian trung bình</h6>
                    <p>${this.getAverageStageTime(data.label)}</p>
                </div>
            </div>
        `);
    }

    /**
     * Show generic details for other chart types
     */
    showGenericDetails(data) {
        this.createDetailModal(`Chi tiết: ${data.label}`, `
            <div class="row">
                <div class="col-12">
                    <p><strong>Giá trị:</strong> ${data.value}</p>
                    <p><strong>Loại biểu đồ:</strong> ${data.chartType}</p>
                    <p><strong>Dataset:</strong> ${data.dataset}</p>
                </div>
            </div>
        `);
    }

    /**
     * Handle real-time data updates
     */
    handleRealtimeUpdate(data) {
        // Update relevant charts with new data
        if (data.type === 'victim_update') {
            this.updateVictimMetrics(data);
        } else if (data.type === 'security_update') {
            this.updateSecurityMetrics(data);
        }
    }

    /**
     * Setup interactive features for charts
     */
    setupInteractiveFeatures() {
        // Add interactive buttons to chart containers
        document.querySelectorAll('.card.shadow').forEach(card => {
            const chartContainer = card.querySelector('canvas');
            if (chartContainer && !card.querySelector('.chart-controls')) {
                this.addChartControls(card, chartContainer);
            }
        });
    }

    /**
     * Add interactive controls to chart cards
     */
    addChartControls(card, canvas) {
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'chart-controls d-flex gap-2 mt-2';

        // Time range selector
        const timeRangeSelect = document.createElement('select');
        timeRangeSelect.className = 'form-select form-select-sm';
        timeRangeSelect.innerHTML = `
            <option value="1h">1 giờ</option>
            <option value="24h" selected>24 giờ</option>
            <option value="7d">7 ngày</option>
            <option value="30d">30 ngày</option>
        `;
        timeRangeSelect.addEventListener('change', (e) => {
            this.updateChartTimeRange(canvas.id, e.target.value);
        });

        // Export button
        const exportBtn = document.createElement('button');
        exportBtn.className = 'btn btn-sm btn-outline-primary';
        exportBtn.innerHTML = '<i class="fas fa-download"></i> Export';
        exportBtn.addEventListener('click', () => {
            this.exportChart(canvas.id);
        });

        // Fullscreen button
        const fullscreenBtn = document.createElement('button');
        fullscreenBtn.className = 'btn btn-sm btn-outline-secondary';
        fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i> Fullscreen';
        fullscreenBtn.addEventListener('click', () => {
            this.toggleFullscreenChart(canvas.id);
        });

        controlsDiv.appendChild(timeRangeSelect);
        controlsDiv.appendChild(exportBtn);
        controlsDiv.appendChild(fullscreenBtn);

        // Insert controls before the canvas
        const cardBody = card.querySelector('.card-body');
        if (cardBody) {
            cardBody.insertBefore(controlsDiv, canvas.parentNode);
        }
    }

    /**
     * Setup export features for charts
     */
    setupExportFeatures() {
        // Add global export event listeners
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                this.exportAllCharts();
            }
        });
    }

    /**
     * Update chart time range
     */
    updateChartTimeRange(canvasId, timeRange) {
        if (!this.advancedFramework) return;

        const chartInfo = this.advancedFramework.charts.get(canvasId);
        if (!chartInfo) return;

        // Update chart data based on time range
        this.advancedFramework.updateChartData(canvasId);

        this.showToast(`Cập nhật thời gian: ${timeRange}`, 'info');
    }

    /**
     * Export single chart
     */
    exportChart(canvasId) {
        if (!this.advancedFramework) return;

        // Show export options modal
        this.showExportModal(canvasId);
    }

    /**
     * Export all charts
     */
    exportAllCharts() {
        if (!this.advancedFramework) return;

        const formats = ['png', 'pdf', 'svg'];
        const format = formats[Math.floor(Math.random() * formats.length)]; // Default format

        this.advancedFramework.charts.forEach((chartInfo, canvasId) => {
            this.advancedFramework.exportChart(canvasId, format, `dashboard_chart_${canvasId}_${Date.now()}`);
        });

        this.showToast(`Đã xuất tất cả biểu đồ định dạng ${format.toUpperCase()}`, 'success');
    }

    /**
     * Toggle fullscreen mode for chart
     */
    toggleFullscreenChart(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const card = canvas.closest('.card');
        if (!card) return;

        card.classList.toggle('fullscreen-chart');

        if (card.classList.contains('fullscreen-chart')) {
            card.style.position = 'fixed';
            card.style.top = '0';
            card.style.left = '0';
            card.style.width = '100vw';
            card.style.height = '100vh';
            card.style.zIndex = '9999';
            card.style.background = 'white';
            card.style.padding = '20px';
            card.style.overflow = 'auto';
        } else {
            card.style.position = '';
            card.style.top = '';
            card.style.left = '';
            card.style.width = '';
            card.style.height = '';
            card.style.zIndex = '';
            card.style.background = '';
            card.style.padding = '';
            card.style.overflow = '';
        }

        // Resize chart to fit new dimensions
        setTimeout(() => {
            if (this.advancedFramework && this.advancedFramework.charts.has(canvasId)) {
                const chart = this.advancedFramework.charts.get(canvasId).chart;
                chart.resize();
            }
        }, 100);
    }

    /**
     * Create detail modal for drill-down information
     */
    createDetailModal(title, content) {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade show" style="display: block;" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" onclick="this.closest('.modal').remove()"></button>
                        </div>
                        <div class="modal-body">
                            ${content}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Đóng</button>
                            <button type="button" class="btn btn-primary" onclick="this.closest('.modal').remove()">Xuất báo cáo</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstElementChild);

        // Add backdrop click to close
        setTimeout(() => {
            const modal = document.querySelector('.modal');
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
        }, 100);
    }

    /**
     * Show export options modal
     */
    showExportModal(canvasId) {
        const exportModal = `
            <div class="modal fade show" style="display: block;" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Xuất biểu đồ</h5>
                            <button type="button" class="btn-close" onclick="this.closest('.modal').remove()"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row g-3">
                                <div class="col-12">
                                    <label class="form-label">Định dạng xuất</label>
                                    <div class="row">
                                        <div class="col-4">
                                            <button class="btn btn-outline-primary w-100" onclick="window.dashboardCharts.exportChartFormat('${canvasId}', 'png'); this.closest('.modal').remove();">
                                                <i class="fas fa-image"></i><br>PNG
                                            </button>
                                        </div>
                                        <div class="col-4">
                                            <button class="btn btn-outline-danger w-100" onclick="window.dashboardCharts.exportChartFormat('${canvasId}', 'pdf'); this.closest('.modal').remove();">
                                                <i class="fas fa-file-pdf"></i><br>PDF
                                            </button>
                                        </div>
                                        <div class="col-4">
                                            <button class="btn btn-outline-info w-100" onclick="window.dashboardCharts.exportChartFormat('${canvasId}', 'svg'); this.closest('.modal').remove();">
                                                <i class="fas fa-code"></i><br>SVG
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-12">
                                    <label class="form-label">Tên file</label>
                                    <input type="text" class="form-control" id="exportFilename" value="chart_export" placeholder="Nhập tên file">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = exportModal;
        document.body.appendChild(modalContainer.firstElementChild);
    }

    /**
     * Export chart in specific format
     */
    exportChartFormat(canvasId, format) {
        if (!this.advancedFramework) return;

        const filename = document.getElementById('exportFilename')?.value || `chart_${canvasId}`;
        this.advancedFramework.exportChart(canvasId, format, `${filename}.${format}`);

        this.showToast(`Đã xuất biểu đồ định dạng ${format.toUpperCase()}`, 'success');
    }

    /**
     * Update victim metrics with real-time data
     */
    updateVictimMetrics(data) {
        // Update victim-related charts with new data
        if (this.advancedFramework) {
            this.advancedFramework.updateSecurityMetrics({
                victimCount: data.count,
                lastUpdate: new Date()
            });
        }
    }

    /**
     * Update security metrics with real-time data
     */
    updateSecurityMetrics(data) {
        // Update security-related charts with new data
        if (this.advancedFramework) {
            this.advancedFramework.updateSecurityMetrics(data);
        }
    }

    /**
     * Create mini chart for threat details
     */
    createThreatDetailChart(data) {
        const ctx = document.getElementById('threatDetailChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Hiện tại', 'Trung bình', 'Mục tiêu'],
                datasets: [{
                    data: [data.value, 60, 80],
                    backgroundColor: [
                        '#dc3545',
                        '#ffc107',
                        '#28a745'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * Calculate conversion rate for funnel stages
     */
    calculateConversionRate(data) {
        // Implementation would calculate actual conversion rate
        return Math.floor(Math.random() * 30) + 10; // Mock data
    }

    /**
     * Get average time for funnel stage
     */
    getAverageStageTime(stageName) {
        const times = {
            'Email đã gửi': '2 phút',
            'Email đã mở': '5 phút',
            'Link đã click': '1 phút',
            'Thông tin đã nhập': '3 phút',
            'Gmail đã truy cập': '30 giây',
            'BeEF đã hook': '10 giây'
        };
        return times[stageName] || 'Không xác định';
    }

    /**
     * Get threat level classification
     */
    getThreatLevel(value) {
        if (value >= 90) return 'Nguy hiểm cao';
        if (value >= 75) return 'Cao';
        if (value >= 50) return 'Trung bình';
        if (value >= 25) return 'Thấp';
        return 'Rất thấp';
    }

    /**
     * Get risk level classification
     */
    getRiskLevel(score) {
        if (score >= 20) return 'Rủi ro rất cao';
        if (score >= 15) return 'Rủi ro cao';
        if (score >= 10) return 'Rủi ro trung bình';
        if (score >= 5) return 'Rủi ro thấp';
        return 'Rủi ro rất thấp';
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Simple toast implementation - replace with your toast system
        console.log(`[${type.toUpperCase()}] ${message}`);

        // You can integrate with existing toast system here
        if (window.showToast) {
            window.showToast(message, type);
        }
    }

    destroy() {
        // Destroy advanced framework
        if (this.advancedFramework) {
            this.advancedFramework.destroy();
        }

        // Destroy all charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });

        this.charts = {};
    }
}

// Initialize dashboard charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardCharts = new DashboardCharts();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardCharts;
}
