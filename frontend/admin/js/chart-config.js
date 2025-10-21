/**
 * Chart Configuration System
 * Manages chart themes, user preferences, and configuration templates
 * for the Advanced Chart Framework
 */

class ChartConfigurationSystem {
    constructor(options = {}) {
        this.options = {
            persistenceEnabled: true,
            defaultTheme: 'security',
            defaultLocale: 'vi',
            configVersion: '1.0',
            ...options
        };

        this.configs = new Map();
        this.themes = new Map();
        this.templates = new Map();
        this.userPreferences = {};
        this.eventListeners = new Map();

        this.init();
    }

    init() {
        this.loadDefaultConfigurations();
        this.loadDefaultThemes();
        this.loadDefaultTemplates();
        this.loadUserPreferences();
        this.setupEventListeners();
    }

    /**
     * Load default chart configurations
     */
    loadDefaultConfigurations() {
        const defaultConfigs = {
            // Security Dashboard Charts
            threatRadar: {
                id: 'threatRadar',
                name: 'Biểu đồ radar đe dọa',
                description: 'Hiển thị mức độ đe dọa bảo mật theo các loại tấn công',
                type: 'radar',
                category: 'security',
                defaultOptions: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                font: { size: 12 },
                                padding: 20,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            callbacks: {
                                label: (context) => `${context.label}: ${context.parsed.r}%`
                            }
                        }
                    },
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
                },
                dataStructure: {
                    labels: ['Phishing', 'Malware', 'Social Engineering', 'Network Attack', 'Data Breach', 'Insider Threat'],
                    datasets: [{
                        label: 'Mức độ đe dọa',
                        data: [65, 45, 80, 30, 55, 25],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        pointBackgroundColor: '#dc3545',
                        pointBorderColor: '#fff'
                    }]
                }
            },

            riskMatrix: {
                id: 'riskMatrix',
                name: 'Ma trận rủi ro',
                description: 'Đánh giá rủi ro bảo mật theo khả năng và ảnh hưởng',
                type: 'scatter',
                category: 'security',
                defaultOptions: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: { size: 11 },
                                usePointStyle: true
                            }
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
                },
                dataStructure: {
                    datasets: [{
                        label: 'Rủi ro bảo mật',
                        data: [
                            { x: 4, y: 4, risk: 'very_high', label: 'Dữ liệu nhạy cảm' },
                            { x: 3, y: 3, risk: 'high', label: 'Thông tin cá nhân' },
                            { x: 2, y: 2, risk: 'medium', label: 'Thông tin nội bộ' }
                        ],
                        backgroundColor: (context) => {
                            const risk = context.raw.risk;
                            const colors = {
                                very_high: '#721c24',
                                high: '#dc3545',
                                medium: '#fd7e14',
                                low: '#ffc107'
                            };
                            return colors[risk] || '#6c757d';
                        }
                    }]
                }
            },

            phishingFunnel: {
                id: 'phishingFunnel',
                name: 'Phễu Phishing',
                description: 'Quy trình tấn công phishing từ gửi email đến hook thành công',
                type: 'bar',
                category: 'security',
                defaultOptions: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
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
                            title: { display: true, text: 'Số lượng nạn nhân' },
                            beginAtZero: true
                        },
                        y: {
                            title: { display: true, text: 'Giai đoạn tấn công' }
                        }
                    }
                },
                dataStructure: {
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
                            '#17a2b8',
                            '#007bff',
                            '#ffc107',
                            '#fd7e14',
                            '#dc3545',
                            '#721c24'
                        ]
                    }]
                }
            },

            realtimeTimeline: {
                id: 'realtimeTimeline',
                name: 'Timeline thời gian thực',
                description: 'Theo dõi hoạt động bảo mật theo thời gian thực',
                type: 'line',
                category: 'monitoring',
                defaultOptions: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 750,
                        easing: 'easeInOutQuart'
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Thời gian' },
                            ticks: { font: { size: 10 } }
                        },
                        y: {
                            title: { display: true, text: 'Số lượng' },
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: { position: 'top' }
                    }
                },
                dataStructure: {
                    labels: [], // Will be populated with real-time data
                    datasets: [
                        {
                            label: 'Nạn nhân mới',
                            data: [],
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Gmail truy cập',
                            data: [],
                            borderColor: '#ffc107',
                            backgroundColor: 'rgba(255, 193, 7, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                }
            },

            geographicHeatMap: {
                id: 'geographicHeatMap',
                name: 'Bản đồ nhiệt địa lý',
                description: 'Phân bố nạn nhân theo quốc gia và khu vực',
                type: 'doughnut',
                category: 'geographic',
                defaultOptions: {
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
                                label: (context) => {
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${context.label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                },
                dataStructure: {
                    labels: ['Việt Nam', 'Hoa Kỳ', 'Anh', 'Canada', 'Úc', 'Singapore', 'Malaysia', 'Khác'],
                    datasets: [{
                        label: 'Nạn nhân theo quốc gia',
                        data: [45, 20, 15, 10, 5, 3, 2, 0],
                        backgroundColor: [
                            '#dc3545',
                            '#007bff',
                            '#28a745',
                            '#ffc107',
                            '#17a2b8',
                            '#6f42c1',
                            '#e83e8c',
                            '#6c757d'
                        ]
                    }]
                }
            }
        };

        // Store configurations
        Object.entries(defaultConfigs).forEach(([key, config]) => {
            this.configs.set(key, config);
        });
    }

    /**
     * Load default themes
     */
    loadDefaultThemes() {
        const defaultThemes = {
            security: {
                id: 'security',
                name: 'Bảo mật',
                description: 'Theme tối ưu cho hiển thị dữ liệu bảo mật',
                colors: {
                    primary: '#0068FF',
                    secondary: '#6c757d',
                    success: '#28a745',
                    danger: '#dc3545',
                    warning: '#ffc107',
                    info: '#17a2b8',
                    threat: {
                        critical: '#721c24',
                        high: '#dc3545',
                        medium: '#fd7e14',
                        low: '#ffc107',
                        very_low: '#28a745'
                    },
                    risk: {
                        very_high: '#721c24',
                        high: '#dc3545',
                        medium: '#fd7e14',
                        low: '#ffc107',
                        very_low: '#28a745'
                    }
                },
                fonts: {
                    family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                    size: 12,
                    titleSize: 14,
                    legendSize: 11
                },
                background: {
                    chart: 'rgba(255, 255, 255, 0.9)',
                    modal: '#ffffff',
                    tooltip: 'rgba(0, 0, 0, 0.8)'
                },
                borders: {
                    chart: 'rgba(0, 0, 0, 0.1)',
                    card: 'rgba(0, 0, 0, 0.125)'
                }
            },

            dark: {
                id: 'dark',
                name: 'Tối',
                description: 'Theme tối cho môi trường làm việc ban đêm',
                colors: {
                    primary: '#4f83cc',
                    secondary: '#adb5bd',
                    success: '#40c057',
                    danger: '#fa5252',
                    warning: '#ffd43b',
                    info: '#339af0',
                    threat: {
                        critical: '#ff6b6b',
                        high: '#ff8e8e',
                        medium: '#ffa8a8',
                        low: '#ffc9c9',
                        very_low: '#e6f3e6'
                    },
                    risk: {
                        very_high: '#ff6b6b',
                        high: '#ff8e8e',
                        medium: '#ffa8a8',
                        low: '#ffc9c9',
                        very_low: '#e6f3e6'
                    }
                },
                fonts: {
                    family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                    size: 12,
                    titleSize: 14,
                    legendSize: 11
                },
                background: {
                    chart: 'rgba(33, 37, 41, 0.9)',
                    modal: '#343a40',
                    tooltip: 'rgba(0, 0, 0, 0.9)'
                },
                borders: {
                    chart: 'rgba(255, 255, 255, 0.1)',
                    card: 'rgba(255, 255, 255, 0.125)'
                }
            },

            light: {
                id: 'light',
                name: 'Sáng',
                description: 'Theme sáng mặc định',
                colors: {
                    primary: '#0068FF',
                    secondary: '#6c757d',
                    success: '#28a745',
                    danger: '#dc3545',
                    warning: '#ffc107',
                    info: '#17a2b8',
                    threat: {
                        critical: '#721c24',
                        high: '#dc3545',
                        medium: '#fd7e14',
                        low: '#ffc107',
                        very_low: '#28a745'
                    },
                    risk: {
                        very_high: '#721c24',
                        high: '#dc3545',
                        medium: '#fd7e14',
                        low: '#ffc107',
                        very_low: '#28a745'
                    }
                },
                fonts: {
                    family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                    size: 12,
                    titleSize: 14,
                    legendSize: 11
                },
                background: {
                    chart: 'rgba(255, 255, 255, 0.9)',
                    modal: '#ffffff',
                    tooltip: 'rgba(0, 0, 0, 0.8)'
                },
                borders: {
                    chart: 'rgba(0, 0, 0, 0.1)',
                    card: 'rgba(0, 0, 0, 0.125)'
                }
            }
        };

        Object.entries(defaultThemes).forEach(([key, theme]) => {
            this.themes.set(key, theme);
        });
    }

    /**
     * Load default chart templates
     */
    loadDefaultTemplates() {
        const defaultTemplates = {
            securityDashboard: {
                id: 'securityDashboard',
                name: 'Dashboard Bảo mật',
                description: 'Template dashboard tổng quan bảo mật',
                charts: [
                    { id: 'threatRadar', position: 'row1', size: 'col-xl-6' },
                    { id: 'riskMatrix', position: 'row1', size: 'col-xl-6' },
                    { id: 'phishingFunnel', position: 'row2', size: 'col-xl-8' },
                    { id: 'realtimeTimeline', position: 'row2', size: 'col-xl-4' },
                    { id: 'geographicHeatMap', position: 'row3', size: 'col-xl-12' }
                ],
                layout: {
                    rows: 3,
                    columns: 12,
                    responsive: true
                }
            },

            monitoringDashboard: {
                id: 'monitoringDashboard',
                name: 'Dashboard Giám sát',
                description: 'Template dashboard giám sát thời gian thực',
                charts: [
                    { id: 'realtimeTimeline', position: 'row1', size: 'col-xl-12' },
                    { id: 'geographicHeatMap', position: 'row2', size: 'col-xl-8' },
                    { id: 'threatRadar', position: 'row3', size: 'col-xl-6' },
                    { id: 'riskMatrix', position: 'row3', size: 'col-xl-6' }
                ]
            },

            compactView: {
                id: 'compactView',
                name: 'Chế độ xem nhỏ gọn',
                description: 'Template hiển thị nhiều biểu đồ trong không gian hạn chế',
                charts: [
                    { id: 'threatRadar', position: 'row1', size: 'col-xl-6' },
                    { id: 'riskMatrix', position: 'row1', size: 'col-xl-6' },
                    { id: 'geographicHeatMap', position: 'row2', size: 'col-xl-12' }
                ]
            }
        };

        Object.entries(defaultTemplates).forEach(([key, template]) => {
            this.templates.set(key, template);
        });
    }

    /**
     * Load user preferences from localStorage
     */
    loadUserPreferences() {
        try {
            const saved = localStorage.getItem('chartUserPreferences');
            if (saved) {
                this.userPreferences = { ...this.userPreferences, ...JSON.parse(saved) };
            } else {
                // Set default preferences
                this.userPreferences = {
                    theme: this.options.defaultTheme,
                    locale: this.options.defaultLocale,
                    realTimeEnabled: true,
                    drillDownEnabled: true,
                    exportEnabled: true,
                    updateInterval: 5000,
                    maxDataPoints: 100,
                    autoSave: true,
                    notifications: true
                };
            }
        } catch (error) {
            console.warn('Không thể tải tùy chọn người dùng:', error);
            this.setDefaultPreferences();
        }
    }

    /**
     * Set default user preferences
     */
    setDefaultPreferences() {
        this.userPreferences = {
            theme: this.options.defaultTheme,
            locale: this.options.defaultLocale,
            realTimeEnabled: true,
            drillDownEnabled: true,
            exportEnabled: true,
            updateInterval: 5000,
            maxDataPoints: 100,
            autoSave: true,
            notifications: true
        };
    }

    /**
     * Save user preferences to localStorage
     */
    saveUserPreferences() {
        if (!this.options.persistenceEnabled) return;

        try {
            localStorage.setItem('chartUserPreferences', JSON.stringify(this.userPreferences));
            this.emit('preferencesSaved', this.userPreferences);
        } catch (error) {
            console.warn('Không thể lưu tùy chọn người dùng:', error);
        }
    }

    /**
     * Get configuration for specific chart type
     */
    getChartConfig(chartType) {
        return this.configs.get(chartType) || null;
    }

    /**
     * Get theme configuration
     */
    getTheme(themeId = null) {
        const themeKey = themeId || this.userPreferences.theme;
        return this.themes.get(themeKey) || this.themes.get(this.options.defaultTheme);
    }

    /**
     * Get template configuration
     */
    getTemplate(templateId) {
        return this.templates.get(templateId) || null;
    }

    /**
     * Apply theme to chart options
     */
    applyThemeToOptions(options, themeId = null) {
        const theme = this.getTheme(themeId);
        if (!theme) return options;

        // Deep merge theme colors into options
        const themedOptions = this.deepMerge(options, {
            plugins: {
                legend: {
                    labels: {
                        font: {
                            family: theme.fonts.family,
                            size: theme.fonts.legendSize
                        }
                    }
                },
                tooltip: {
                    backgroundColor: theme.background.tooltip,
                    titleColor: theme.colors.primary,
                    bodyColor: theme.colors.primary,
                    borderColor: theme.borders.chart,
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    ticks: {
                        font: {
                            family: theme.fonts.family,
                            size: theme.fonts.size
                        }
                    },
                    title: {
                        font: {
                            family: theme.fonts.family,
                            size: theme.fonts.titleSize
                        }
                    },
                    grid: {
                        color: theme.borders.chart
                    }
                },
                y: {
                    ticks: {
                        font: {
                            family: theme.fonts.family,
                            size: theme.fonts.size
                        }
                    },
                    title: {
                        font: {
                            family: theme.fonts.family,
                            size: theme.fonts.titleSize
                        }
                    },
                    grid: {
                        color: theme.borders.chart
                    }
                },
                r: {
                    ticks: {
                        font: {
                            family: theme.fonts.family,
                            size: theme.fonts.size
                        }
                    },
                    pointLabels: {
                        font: {
                            family: theme.fonts.family,
                            size: theme.fonts.size
                        }
                    },
                    grid: {
                        color: theme.borders.chart
                    }
                }
            }
        });

        return themedOptions;
    }

    /**
     * Create chart configuration with theme applied
     */
    createThemedChartConfig(chartType, customOptions = {}) {
        const baseConfig = this.getChartConfig(chartType);
        if (!baseConfig) return null;

        const themedOptions = this.applyThemeToOptions(baseConfig.defaultOptions);

        return {
            ...baseConfig,
            options: this.deepMerge(themedOptions, customOptions),
            data: customOptions.data || baseConfig.dataStructure
        };
    }

    /**
     * Update user preference
     */
    updateUserPreference(key, value) {
        this.userPreferences[key] = value;

        if (this.options.persistenceEnabled && this.userPreferences.autoSave) {
            this.saveUserPreferences();
        }

        this.emit('preferenceChanged', { key, value });
    }

    /**
     * Get user preference
     */
    getUserPreference(key) {
        return this.userPreferences[key];
    }

    /**
     * Apply locale to chart configuration
     */
    applyLocaleToConfig(config, locale) {
        // Implementation would translate labels based on locale
        // For now, return config as-is
        return config;
    }

    /**
     * Create custom chart configuration
     */
    createCustomConfig(configData) {
        const config = {
            id: configData.id,
            name: configData.name,
            description: configData.description,
            type: configData.type,
            category: configData.category || 'custom',
            defaultOptions: configData.options || {},
            dataStructure: configData.dataStructure || { labels: [], datasets: [] },
            createdAt: new Date(),
            version: '1.0'
        };

        this.configs.set(config.id, config);
        this.emit('configCreated', config);

        return config;
    }

    /**
     * Create custom theme
     */
    createCustomTheme(themeData) {
        const theme = {
            id: themeData.id,
            name: themeData.name,
            description: themeData.description,
            colors: themeData.colors || {},
            fonts: themeData.fonts || {},
            background: themeData.background || {},
            borders: themeData.borders || {},
            createdAt: new Date()
        };

        this.themes.set(theme.id, theme);
        this.emit('themeCreated', theme);

        return theme;
    }

    /**
     * Create custom template
     */
    createCustomTemplate(templateData) {
        const template = {
            id: templateData.id,
            name: templateData.name,
            description: templateData.description,
            charts: templateData.charts || [],
            layout: templateData.layout || {},
            createdAt: new Date()
        };

        this.templates.set(template.id, template);
        this.emit('templateCreated', template);

        return template;
    }

    /**
     * Export configuration as JSON
     */
    exportConfiguration() {
        const exportData = {
            version: this.options.configVersion,
            exportDate: new Date(),
            configs: Array.from(this.configs.entries()),
            themes: Array.from(this.themes.entries()),
            templates: Array.from(this.templates.entries()),
            preferences: this.userPreferences
        };

        return JSON.stringify(exportData, null, 2);
    }

    /**
     * Import configuration from JSON
     */
    importConfiguration(jsonData) {
        try {
            const data = JSON.parse(jsonData);

            if (data.configs) {
                data.configs.forEach(([key, config]) => {
                    this.configs.set(key, config);
                });
            }

            if (data.themes) {
                data.themes.forEach(([key, theme]) => {
                    this.themes.set(key, theme);
                });
            }

            if (data.templates) {
                data.templates.forEach(([key, template]) => {
                    this.templates.set(key, template);
                });
            }

            if (data.preferences) {
                this.userPreferences = { ...this.userPreferences, ...data.preferences };
                this.saveUserPreferences();
            }

            this.emit('configurationImported', data);
            return true;
        } catch (error) {
            console.error('Lỗi nhập cấu hình:', error);
            return false;
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for system theme changes
        window.addEventListener('themeChange', (event) => {
            this.updateUserPreference('theme', event.detail.theme);
        });

        // Listen for locale changes
        window.addEventListener('localeChange', (event) => {
            this.updateUserPreference('locale', event.detail.locale);
        });
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
     * Utility functions
     */
    deepMerge(target, source) {
        const result = { ...target };

        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this.deepMerge(target[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }

        return result;
    }

    getRiskLevel(score) {
        if (score >= 20) return 'Rủi ro rất cao';
        if (score >= 15) return 'Rủi ro cao';
        if (score >= 10) return 'Rủi ro trung bình';
        if (score >= 5) return 'Rủi ro thấp';
        return 'Rủi ro rất thấp';
    }

    /**
     * Get all available configurations
     */
    getAllConfigurations() {
        return Array.from(this.configs.values());
    }

    /**
     * Get all available themes
     */
    getAllThemes() {
        return Array.from(this.themes.values());
    }

    /**
     * Get all available templates
     */
    getAllTemplates() {
        return Array.from(this.templates.values());
    }

    /**
     * Reset to default configurations
     */
    resetToDefaults() {
        this.configs.clear();
        this.themes.clear();
        this.templates.clear();

        this.loadDefaultConfigurations();
        this.loadDefaultThemes();
        this.loadDefaultTemplates();
        this.setDefaultPreferences();

        this.emit('resetToDefaults', {});
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        this.configs.clear();
        this.themes.clear();
        this.templates.clear();
        this.userPreferences = {};
        this.eventListeners.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartConfigurationSystem;
}

// Make available globally
window.ChartConfigurationSystem = ChartConfigurationSystem;