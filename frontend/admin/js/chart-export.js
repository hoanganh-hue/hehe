/**
 * Chart Export System
 * Handles chart export functionality including PNG, PDF, SVG formats
 * and batch export capabilities for the Advanced Chart Framework
 */

class ChartExportSystem {
    constructor(options = {}) {
        this.options = {
            defaultFormat: 'png',
            defaultQuality: 1.0,
            maxCanvasSize: 4096,
            enableBatchExport: true,
            enableCustomTemplates: true,
            watermarkEnabled: false,
            watermarkText: 'ZaloPay Security Dashboard',
            ...options
        };

        this.exportQueue = [];
        this.isExporting = false;
        this.exportHistory = [];
        this.templates = new Map();
        this.formatHandlers = new Map();

        this.init();
    }

    init() {
        this.loadDefaultTemplates();
        this.registerFormatHandlers();
        this.loadExportHistory();
        this.setupGlobalKeyboardShortcuts();
    }

    /**
     * Load default export templates
     */
    loadDefaultTemplates() {
        const defaultTemplates = {
            securityReport: {
                id: 'securityReport',
                name: 'Báo cáo bảo mật',
                description: 'Template báo cáo bảo mật chuyên nghiệp',
                format: 'pdf',
                layout: 'A4',
                orientation: 'portrait',
                sections: [
                    {
                        type: 'header',
                        title: 'Báo cáo bảo mật ZaloPay',
                        subtitle: 'Dashboard tổng quan',
                        includeDate: true,
                        includeLogo: true
                    },
                    {
                        type: 'charts',
                        chartIds: ['threatRadar', 'riskMatrix'],
                        layout: '2x2',
                        spacing: 20
                    },
                    {
                        type: 'summary',
                        title: 'Tóm tắt',
                        includeMetrics: true,
                        includeRecommendations: true
                    }
                ],
                styles: {
                    fontFamily: 'Arial, sans-serif',
                    primaryColor: '#0068FF',
                    backgroundColor: '#ffffff',
                    textColor: '#212529'
                }
            },

            presentation: {
                id: 'presentation',
                name: 'Thuyết trình',
                description: 'Template xuất cho mục đích thuyết trình',
                format: 'pdf',
                layout: '16:9',
                orientation: 'landscape',
                sections: [
                    {
                        type: 'title',
                        title: 'Báo cáo bảo mật',
                        backgroundColor: '#0068FF',
                        textColor: '#ffffff'
                    },
                    {
                        type: 'charts',
                        chartIds: ['phishingFunnel', 'geographicHeatMap'],
                        layout: '1x2',
                        spacing: 30
                    }
                ]
            },

            compact: {
                id: 'compact',
                name: 'Nhỏ gọn',
                description: 'Template xuất nhỏ gọn cho email hoặc chia sẻ nhanh',
                format: 'png',
                layout: 'square',
                sections: [
                    {
                        type: 'charts',
                        chartIds: ['threatRadar'],
                        layout: 'single',
                        includeBackground: true
                    }
                ]
            }
        };

        Object.entries(defaultTemplates).forEach(([key, template]) => {
            this.templates.set(key, template);
        });
    }

    /**
     * Register format handlers for different export types
     */
    registerFormatHandlers() {
        this.formatHandlers.set('png', {
            handler: this.exportAsPNG.bind(this),
            mimeType: 'image/png',
            extension: 'png',
            supportsBatch: true,
            quality: true
        });

        this.formatHandlers.set('jpeg', {
            handler: this.exportAsJPEG.bind(this),
            mimeType: 'image/jpeg',
            extension: 'jpg',
            supportsBatch: true,
            quality: true
        });

        this.formatHandlers.set('svg', {
            handler: this.exportAsSVG.bind(this),
            mimeType: 'image/svg+xml',
            extension: 'svg',
            supportsBatch: false,
            quality: false
        });

        this.formatHandlers.set('pdf', {
            handler: this.exportAsPDF.bind(this),
            mimeType: 'application/pdf',
            extension: 'pdf',
            supportsBatch: true,
            quality: false
        });

        this.formatHandlers.set('json', {
            handler: this.exportAsJSON.bind(this),
            mimeType: 'application/json',
            extension: 'json',
            supportsBatch: true,
            quality: false
        });
    }

    /**
     * Export single chart
     */
    async exportChart(canvasId, format = null, options = {}) {
        const exportFormat = format || this.options.defaultFormat;
        const handler = this.formatHandlers.get(exportFormat);

        if (!handler) {
            throw new Error(`Định dạng không được hỗ trợ: ${exportFormat}`);
        }

        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            throw new Error(`Không tìm thấy canvas: ${canvasId}`);
        }

        const exportOptions = {
            format: exportFormat,
            quality: this.options.defaultQuality,
            filename: options.filename || `chart_${canvasId}_${Date.now()}`,
            includeBackground: options.includeBackground !== false,
            scale: options.scale || 1,
            ...options
        };

        try {
            const result = await handler.handler(canvas, exportOptions);

            // Add to export history
            this.addToExportHistory({
                canvasId,
                format: exportFormat,
                filename: exportOptions.filename,
                timestamp: new Date(),
                size: result.size || 0,
                success: true
            });

            this.emit('chartExported', {
                canvasId,
                format: exportFormat,
                result,
                options: exportOptions
            });

            return result;
        } catch (error) {
            console.error('Lỗi xuất biểu đồ:', error);

            // Add failed export to history
            this.addToExportHistory({
                canvasId,
                format: exportFormat,
                filename: exportOptions.filename,
                timestamp: new Date(),
                success: false,
                error: error.message
            });

            throw error;
        }
    }

    /**
     * Export multiple charts as batch
     */
    async exportBatch(chartIds, format = null, options = {}) {
        if (!this.options.enableBatchExport) {
            throw new Error('Batch export không được bật');
        }

        const exportFormat = format || this.options.defaultFormat;
        const handler = this.formatHandlers.get(exportFormat);

        if (!handler || !handler.supportsBatch) {
            throw new Error(`Định dạng không hỗ trợ batch export: ${exportFormat}`);
        }

        const results = [];
        const errors = [];

        this.isExporting = true;
        this.emit('batchExportStarted', { chartIds, format: exportFormat });

        for (const canvasId of chartIds) {
            try {
                const result = await this.exportChart(canvasId, exportFormat, {
                    ...options,
                    filename: `${options.filename || 'batch_export'}_${canvasId}_${Date.now()}`
                });
                results.push({ canvasId, success: true, result });
            } catch (error) {
                errors.push({ canvasId, success: false, error: error.message });
                results.push({ canvasId, success: false, error: error.message });
            }

            // Small delay between exports to prevent overwhelming the system
            await this.delay(100);
        }

        this.isExporting = false;

        this.emit('batchExportCompleted', {
            total: chartIds.length,
            successful: results.filter(r => r.success).length,
            failed: errors.length,
            results,
            errors
        });

        return { results, errors };
    }

    /**
     * Export using template
     */
    async exportWithTemplate(templateId, chartIds, options = {}) {
        const template = this.templates.get(templateId);
        if (!template) {
            throw new Error(`Template không tồn tại: ${templateId}`);
        }

        this.emit('templateExportStarted', { templateId, chartIds });

        try {
            let result;

            switch (template.format) {
                case 'pdf':
                    result = await this.exportAsPDFWithTemplate(template, chartIds, options);
                    break;
                case 'png':
                    result = await this.exportAsPNGWithTemplate(template, chartIds, options);
                    break;
                default:
                    throw new Error(`Định dạng template không được hỗ trợ: ${template.format}`);
            }

            this.emit('templateExportCompleted', { templateId, result });
            return result;
        } catch (error) {
            this.emit('templateExportFailed', { templateId, error: error.message });
            throw error;
        }
    }

    /**
     * Export chart as PNG
     */
    async exportAsPNG(canvas, options) {
        return new Promise((resolve, reject) => {
            try {
                // Create temporary canvas for high-quality export
                const exportCanvas = this.createExportCanvas(canvas, options);

                // Convert to blob
                exportCanvas.toBlob((blob) => {
                    if (blob) {
                        const url = URL.createObjectURL(blob);
                        this.downloadFile(url, `${options.filename}.png`);

                        resolve({
                            blob,
                            url,
                            size: blob.size,
                            filename: `${options.filename}.png`
                        });
                    } else {
                        reject(new Error('Không thể tạo blob từ canvas'));
                    }
                }, 'image/png', options.quality);

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Export chart as JPEG
     */
    async exportAsJPEG(canvas, options) {
        return new Promise((resolve, reject) => {
            try {
                const exportCanvas = this.createExportCanvas(canvas, options);

                exportCanvas.toBlob((blob) => {
                    if (blob) {
                        const url = URL.createObjectURL(blob);
                        this.downloadFile(url, `${options.filename}.jpg`);

                        resolve({
                            blob,
                            url,
                            size: blob.size,
                            filename: `${options.filename}.jpg`
                        });
                    } else {
                        reject(new Error('Không thể tạo blob từ canvas'));
                    }
                }, 'image/jpeg', options.quality);

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Export chart as SVG
     */
    async exportAsSVG(canvas, options) {
        // Note: This is a simplified SVG export
        // For production, consider using a library like canvas2svg

        const svgString = `
            <svg width="${canvas.width}" height="${canvas.height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="white"/>
                <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle"
                      font-family="Arial" font-size="16" fill="#666">
                    SVG Export - Chart: ${options.filename}
                </text>
            </svg>
        `;

        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);

        this.downloadFile(url, `${options.filename}.svg`);

        return {
            blob,
            url,
            size: blob.size,
            filename: `${options.filename}.svg`,
            svgString
        };
    }

    /**
     * Export chart as PDF
     */
    async exportAsPDF(canvas, options) {
        // Note: This requires jsPDF library for full implementation
        // For now, we'll create a simple PDF structure

        const pdfData = {
            filename: `${options.filename}.pdf`,
            canvas: canvas.id,
            exportedAt: new Date(),
            dimensions: {
                width: canvas.width,
                height: canvas.height
            }
        };

        // In a real implementation, you would use jsPDF:
        // const pdf = new jsPDF();
        // pdf.addImage(canvas.toDataURL(), 'PNG', 0, 0, width, height);
        // pdf.save(filename);

        console.log('PDF Export (jsPDF required):', pdfData);

        return {
            filename: pdfData.filename,
            data: pdfData,
            size: JSON.stringify(pdfData).length
        };
    }

    /**
     * Export chart as JSON data
     */
    async exportAsJSON(canvas, options) {
        const chart = window.dashboardCharts?.charts?.[canvas.id] ||
                     window.advancedChartFramework?.charts?.get(canvas.id);

        const jsonData = {
            filename: `${options.filename}.json`,
            exportDate: new Date(),
            chartType: chart?.type || 'unknown',
            canvasId: canvas.id,
            dimensions: {
                width: canvas.width,
                height: canvas.height
            },
            data: chart ? {
                labels: chart.data.labels,
                datasets: chart.data.datasets.map(dataset => ({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: dataset.backgroundColor,
                    borderColor: dataset.borderColor
                }))
            } : null
        };

        const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        this.downloadFile(url, `${options.filename}.json`);

        return {
            blob,
            url,
            size: blob.size,
            filename: `${options.filename}.json`,
            data: jsonData
        };
    }

    /**
     * Export as PDF with template
     */
    async exportAsPDFWithTemplate(template, chartIds, options) {
        // Implementation would create PDF with template layout
        console.log('PDF Template Export:', { template, chartIds, options });

        return {
            filename: `report_${Date.now()}.pdf`,
            template: template.id,
            charts: chartIds
        };
    }

    /**
     * Export as PNG with template
     */
    async exportAsPNGWithTemplate(template, chartIds, options) {
        // Implementation would create composite PNG with template layout
        console.log('PNG Template Export:', { template, chartIds, options });

        return {
            filename: `composite_${Date.now()}.png`,
            template: template.id,
            charts: chartIds
        };
    }

    /**
     * Create export canvas with proper scaling
     */
    createExportCanvas(originalCanvas, options) {
        const scale = options.scale || 1;
        const width = Math.min(originalCanvas.width * scale, this.options.maxCanvasSize);
        const height = Math.min(originalCanvas.height * scale, this.options.maxCanvasSize);

        const exportCanvas = document.createElement('canvas');
        const ctx = exportCanvas.getContext('2d');

        exportCanvas.width = width;
        exportCanvas.height = height;

        // Scale context for high DPI displays
        const dpr = window.devicePixelRatio || 1;
        ctx.scale(dpr, dpr);

        // Fill background if requested
        if (options.includeBackground !== false) {
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, width, height);
        }

        // Draw original canvas scaled
        ctx.drawImage(originalCanvas, 0, 0, width, height);

        // Add watermark if enabled
        if (this.options.watermarkEnabled) {
            this.addWatermark(ctx, width, height);
        }

        return exportCanvas;
    }

    /**
     * Add watermark to exported image
     */
    addWatermark(ctx, width, height) {
        ctx.save();
        ctx.globalAlpha = 0.1;
        ctx.font = 'bold 16px Arial';
        ctx.fillStyle = '#666666';
        ctx.textAlign = 'right';
        ctx.fillText(this.options.watermarkText, width - 20, height - 20);
        ctx.restore();
    }

    /**
     * Download file from URL
     */
    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean up object URL after download
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    /**
     * Show export modal with options
     */
    showExportModal(canvasId) {
        const modalHtml = `
            <div class="modal fade show" style="display: block;" tabindex="-1">
                <div class="modal-dialog modal-lg">
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
                                        <div class="col-6 col-md-3">
                                            <button class="btn btn-outline-primary w-100 export-format-btn"
                                                    data-format="png" onclick="window.chartExport.exportChartFormat('${canvasId}', 'png')">
                                                <i class="fas fa-image"></i><br>PNG
                                            </button>
                                        </div>
                                        <div class="col-6 col-md-3">
                                            <button class="btn btn-outline-warning w-100 export-format-btn"
                                                    data-format="jpeg" onclick="window.chartExport.exportChartFormat('${canvasId}', 'jpeg')">
                                                <i class="fas fa-image"></i><br>JPEG
                                            </button>
                                        </div>
                                        <div class="col-6 col-md-3">
                                            <button class="btn btn-outline-info w-100 export-format-btn"
                                                    data-format="svg" onclick="window.chartExport.exportChartFormat('${canvasId}', 'svg')">
                                                <i class="fas fa-code"></i><br>SVG
                                            </button>
                                        </div>
                                        <div class="col-6 col-md-3">
                                            <button class="btn btn-outline-danger w-100 export-format-btn"
                                                    data-format="pdf" onclick="window.chartExport.exportChartFormat('${canvasId}', 'pdf')">
                                                <i class="fas fa-file-pdf"></i><br>PDF
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-12">
                                    <label class="form-label">Tên file</label>
                                    <input type="text" class="form-control" id="exportFilename" value="chart_export" placeholder="Nhập tên file">
                                </div>
                                <div class="col-12">
                                    <label class="form-label">Tùy chọn nâng cao</label>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="includeBackground" checked>
                                        <label class="form-check-label" for="includeBackground">
                                            Bao gồm nền trắng
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="enableWatermark">
                                        <label class="form-check-label" for="enableWatermark">
                                            Thêm watermark
                                        </label>
                                    </div>
                                </div>
                                <div class="col-12">
                                    <label class="form-label">Template (PDF)</label>
                                    <select class="form-select" id="exportTemplate">
                                        <option value="">Không sử dụng template</option>
                                        <option value="securityReport">Báo cáo bảo mật</option>
                                        <option value="presentation">Thuyết trình</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Đóng</button>
                            <button type="button" class="btn btn-primary" onclick="window.chartExport.exportWithOptions('${canvasId}')">Xuất</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstElementChild);

        // Setup modal event listeners
        this.setupExportModalEvents(canvasId);
    }

    /**
     * Setup events for export modal
     */
    setupExportModalEvents(canvasId) {
        const modal = document.querySelector('.modal');
        const watermarkCheckbox = document.getElementById('enableWatermark');

        // Handle watermark toggle
        if (watermarkCheckbox) {
            watermarkCheckbox.addEventListener('change', (e) => {
                this.options.watermarkEnabled = e.target.checked;
            });
        }

        // Handle backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Export with options from modal
     */
    async exportWithOptions(canvasId) {
        const format = document.querySelector('.export-format-btn.active')?.dataset.format || 'png';
        const filename = document.getElementById('exportFilename')?.value || 'chart_export';
        const includeBackground = document.getElementById('includeBackground')?.checked !== false;
        const template = document.getElementById('exportTemplate')?.value;

        const options = {
            filename,
            includeBackground,
            watermarkEnabled: this.options.watermarkEnabled
        };

        try {
            if (template) {
                await this.exportWithTemplate(template, [canvasId], options);
            } else {
                await this.exportChart(canvasId, format, options);
            }

            // Close modal
            document.querySelector('.modal').remove();
            this.showToast('Xuất biểu đồ thành công!', 'success');

        } catch (error) {
            console.error('Lỗi xuất biểu đồ:', error);
            this.showToast('Lỗi xuất biểu đồ: ' + error.message, 'error');
        }
    }

    /**
     * Export chart with specific format (called from modal)
     */
    async exportChartFormat(canvasId, format) {
        // Set active format button
        document.querySelectorAll('.export-format-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-format="${format}"]`).classList.add('active');

        const filename = document.getElementById('exportFilename')?.value || 'chart_export';
        const includeBackground = document.getElementById('includeBackground')?.checked !== false;

        await this.exportChart(canvasId, format, {
            filename,
            includeBackground,
            watermarkEnabled: this.options.watermarkEnabled
        });

        document.querySelector('.modal').remove();
        this.showToast(`Đã xuất biểu đồ định dạng ${format.toUpperCase()}`, 'success');
    }

    /**
     * Setup global keyboard shortcuts for export
     */
    setupGlobalKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + E for export current chart
            if ((e.ctrlKey || e.metaKey) && e.key === 'e' && !e.shiftKey) {
                e.preventDefault();
                const activeCanvas = document.querySelector('canvas:hover');
                if (activeCanvas) {
                    this.showExportModal(activeCanvas.id);
                }
            }

            // Ctrl/Cmd + Shift + E for batch export
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'E') {
                e.preventDefault();
                this.exportAllCharts();
            }
        });
    }

    /**
     * Export all charts on the page
     */
    async exportAllCharts() {
        const canvasElements = document.querySelectorAll('canvas');
        const canvasIds = Array.from(canvasElements).map(canvas => canvas.id).filter(id => id);

        if (canvasIds.length === 0) {
            this.showToast('Không tìm thấy biểu đồ nào để xuất', 'warning');
            return;
        }

        try {
            await this.exportBatch(canvasIds, this.options.defaultFormat, {
                filename: `batch_export_${Date.now()}`
            });

            this.showToast(`Đã xuất ${canvasIds.length} biểu đồ`, 'success');
        } catch (error) {
            console.error('Lỗi xuất hàng loạt:', error);
            this.showToast('Lỗi xuất hàng loạt: ' + error.message, 'error');
        }
    }

    /**
     * Add export to history
     */
    addToExportHistory(exportData) {
        this.exportHistory.unshift(exportData);

        // Keep only last 100 exports
        if (this.exportHistory.length > 100) {
            this.exportHistory = this.exportHistory.slice(0, 100);
        }

        this.saveExportHistory();
    }

    /**
     * Load export history from localStorage
     */
    loadExportHistory() {
        try {
            const saved = localStorage.getItem('chartExportHistory');
            if (saved) {
                this.exportHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Không thể tải lịch sử xuất:', error);
        }
    }

    /**
     * Save export history to localStorage
     */
    saveExportHistory() {
        try {
            localStorage.setItem('chartExportHistory', JSON.stringify(this.exportHistory));
        } catch (error) {
            console.warn('Không thể lưu lịch sử xuất:', error);
        }
    }

    /**
     * Get export history
     */
    getExportHistory(limit = 50) {
        return this.exportHistory.slice(0, limit);
    }

    /**
     * Clear export history
     */
    clearExportHistory() {
        this.exportHistory = [];
        this.saveExportHistory();
        this.emit('historyCleared', {});
    }

    /**
     * Create custom export template
     */
    createCustomTemplate(templateData) {
        const template = {
            id: templateData.id,
            name: templateData.name,
            description: templateData.description,
            format: templateData.format || 'png',
            layout: templateData.layout || 'A4',
            orientation: templateData.orientation || 'portrait',
            sections: templateData.sections || [],
            styles: templateData.styles || {},
            createdAt: new Date()
        };

        this.templates.set(template.id, template);
        this.emit('templateCreated', template);

        return template;
    }

    /**
     * Get all export templates
     */
    getAllTemplates() {
        return Array.from(this.templates.values());
    }

    /**
     * Utility functions
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    showToast(message, type = 'info') {
        // Simple toast implementation - replace with your toast system
        console.log(`[${type.toUpperCase()}] ${message}`);

        // You can integrate with existing toast system here
        if (window.showToast) {
            window.showToast(message, type);
        }
    }

    /**
     * Event system
     */
    on(event, callback) {
        if (!this.eventListeners) {
            this.eventListeners = new Map();
        }
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    emit(event, data) {
        if (this.eventListeners && this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => callback(data));
        }
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        this.exportQueue = [];
        this.templates.clear();
        this.formatHandlers.clear();
        this.exportHistory = [];

        if (this.eventListeners) {
            this.eventListeners.clear();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartExportSystem;
}

// Make available globally
window.ChartExportSystem = ChartExportSystem;