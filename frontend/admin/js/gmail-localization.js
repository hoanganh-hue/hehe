/**
 * Gmail Interface Vietnamese Localization
 * Centralized language management for all Gmail interfaces
 */

const GmailLocalization = {
    // Common texts
    common: {
        loading: 'Đang tải...',
        processing: 'Đang xử lý...',
        error: 'Lỗi',
        success: 'Thành công',
        warning: 'Cảnh báo',
        info: 'Thông tin',
        confirm: 'Xác nhận',
        cancel: 'Hủy',
        save: 'Lưu',
        delete: 'Xóa',
        edit: 'Chỉnh sửa',
        view: 'Xem',
        export: 'Xuất',
        import: 'Nhập',
        refresh: 'Làm mới',
        search: 'Tìm kiếm',
        filter: 'Lọc',
        clear: 'Xóa',
        selectAll: 'Chọn tất cả',
        selected: 'Đã chọn',
        total: 'Tổng cộng',
        none: 'Không có',
        unknown: 'Không xác định',
        na: 'N/A',
        yes: 'Có',
        no: 'Không',
        enabled: 'Đã bật',
        disabled: 'Đã tắt',
        active: 'Đang hoạt động',
        inactive: 'Không hoạt động',
        online: 'Trực tuyến',
        offline: 'Ngoại tuyến',
        connected: 'Đã kết nối',
        disconnected: 'Mất kết nối',
        retry: 'Thử lại',
        back: 'Quay lại',
        next: 'Tiếp theo',
        previous: 'Trước',
        finish: 'Hoàn thành',
        close: 'Đóng',
        open: 'Mở',
        show: 'Hiển thị',
        hide: 'Ẩn',
        more: 'Thêm',
        less: 'Ít hơn',
        all: 'Tất cả',
        date: 'Ngày',
        time: 'Thời gian',
        size: 'Kích thước',
        count: 'Số lượng',
        status: 'Trạng thái',
        action: 'Thao tác',
        result: 'Kết quả',
        message: 'Tin nhắn',
        description: 'Mô tả',
        name: 'Tên',
        type: 'Loại',
        format: 'Định dạng',
        file: 'Tệp',
        folder: 'Thư mục',
        path: 'Đường dẫn',
        url: 'URL',
        email: 'Email',
        phone: 'Điện thoại',
        address: 'Địa chỉ',
        company: 'Công ty',
        position: 'Chức vụ',
        note: 'Ghi chú',
        tag: 'Thẻ',
        category: 'Danh mục',
        priority: 'Ưu tiên',
        level: 'Cấp độ',
        progress: 'Tiến trình',
        percentage: 'Phần trăm',
        speed: 'Tốc độ',
        duration: 'Thời lượng',
        remaining: 'Còn lại',
        elapsed: 'Đã trôi qua',
        estimated: 'Ước tính',
        actual: 'Thực tế',
        minimum: 'Tối thiểu',
        maximum: 'Tối đa',
        average: 'Trung bình',
        sum: 'Tổng',
        count: 'Đếm',
        min: 'Tối thiểu',
        max: 'Tối đa',
        avg: 'Trung bình'
    },

    // Gmail Access Interface
    gmailAccess: {
        title: 'Gmail Access Interface',
        subtitle: 'Quản lý truy cập Gmail và tiến trình khai thác dữ liệu',
        totalAccess: 'Tổng truy cập Gmail',
        extractedCount: 'Đã khai thác',
        extractingCount: 'Đang khai thác',
        errorCount: 'Lỗi khai thác',
        searchPlaceholder: 'Tìm kiếm email...',
        allStatus: 'Tất cả trạng thái',
        activeStatus: 'Đang hoạt động',
        expiredStatus: 'Đã hết hạn',
        revokedStatus: 'Đã thu hồi',
        allExtraction: 'Tình trạng khai thác',
        notStarted: 'Chưa bắt đầu',
        inProgress: 'Đang thực hiện',
        completed: 'Đã hoàn thành',
        failed: 'Thất bại',
        allTime: 'Tất cả thời gian',
        today: 'Hôm nay',
        thisWeek: 'Tuần này',
        thisMonth: 'Tháng này',
        customRange: 'Tùy chỉnh',
        extractAll: 'Khai thác tất cả',
        extractSelected: 'Khai thác đã chọn',
        exportSelected: 'Xuất dữ liệu đã chọn',
        deleteAccess: 'Xóa truy cập',
        viewData: 'Xem dữ liệu',
        exportData: 'Xuất dữ liệu',
        viewDetails: 'Xem chi tiết',
        bulkActions: 'Thao tác hàng loạt',
        itemsPerPage: 'Mục mỗi trang',
        items: 'mục',
        selectedCount: 'Đã chọn',
        noData: 'Không có dữ liệu truy cập Gmail nào',
        noDataDesc: 'Chưa có tài khoản Gmail nào được cấp quyền truy cập',
        accessStatus: 'Trạng thái truy cập',
        extractionProgress: 'Tiến trình khai thác',
        dataExtracted: 'Dữ liệu đã lấy',
        accessDate: 'Ngày truy cập',
        lastUpdated: 'Cập nhật cuối',
        actions: 'Thao tác',
        extractAction: 'Khai thác dữ liệu',
        pauseAction: 'Tạm dừng',
        cancelAction: 'Hủy bỏ',
        resumeAction: 'Tiếp tục',
        confirmExtractAll: 'Bạn có chắc chắn muốn khai thác dữ liệu từ tất cả tài khoản Gmail?',
        confirmDelete: 'Bạn có chắc chắn muốn xóa truy cập Gmail này?',
        confirmBulkDelete: 'Bạn có chắc chắn muốn xóa {0} truy cập Gmail?',
        extractionStarted: 'Đã bắt đầu khai thác dữ liệu Gmail',
        extractionFailed: 'Không thể bắt đầu khai thác: {0}',
        accessDeleted: 'Đã xóa truy cập Gmail',
        deleteFailed: 'Không thể xóa truy cập: {0}',
        selectAtLeastOne: 'Vui lòng chọn ít nhất một mục để {0}',
        tableExportCsv: 'Xuất CSV',
        tableExportJson: 'Xuất JSON',
        columnSelection: 'Chọn cột hiển thị',
        autoRefresh: 'Tự động làm mới',
        realTimeUpdates: 'Cập nhật thời gian thực',
        connectionLost: 'Mất kết nối WebSocket',
        connectionRestored: 'Kết nối đã được khôi phục',
        newAccessGranted: 'Cấp quyền truy cập Gmail mới: {0}',
        accessRevoked: 'Thu hồi quyền truy cập Gmail: {0}',
        systemNotification: 'Thông báo hệ thống: {0}'
    },

    // Gmail Extraction Progress
    extractionProgress: {
        title: 'Gmail Extraction Progress',
        subtitle: 'Theo dõi tiến trình khai thác dữ liệu Gmail theo thời gian thực',
        overallProgress: 'Tiến trình tổng thể',
        emailsPerSecond: 'Emails/giây',
        totalProcessed: 'Tổng emails đã xử lý',
        estimatedTime: 'Thời gian còn lại (ước tính)',
        activeExtractions: 'Các tiến trình đang hoạt động',
        performanceChart: 'Hiệu suất theo thời gian thực',
        realTimeLogs: 'Logs thời gian thực',
        controlPanel: 'Bảng điều khiển khai thác',
        startAll: 'Bắt đầu khai thác tất cả',
        pauseAll: 'Tạm dừng tất cả',
        resumeAll: 'Tiếp tục tất cả',
        stopAll: 'Dừng tất cả',
        autoScroll: 'Tự động cuộn',
        detailedView: 'Chế độ chi tiết',
        clearLogs: 'Xóa logs',
        filterLogs: 'Lọc logs',
        allLogs: 'Tất cả',
        infoLogs: 'Thông tin',
        successLogs: 'Thành công',
        warningLogs: 'Cảnh báo',
        errorLogs: 'Lỗi',
        noActiveExtractions: 'Không có tiến trình khai thác nào đang hoạt động',
        noActiveExtractionsDesc: 'Chưa có tiến trình khai thác Gmail nào đang chạy',
        extractionCompleted: 'Hoàn thành khai thác Gmail: {0}',
        extractionFailed: 'Thất bại khai thác Gmail: {0} - {1}',
        extractionPaused: 'Tạm dừng khai thác: {0}',
        extractionCancelled: 'Hủy khai thác: {0}',
        confirmStartAll: 'Bạn có chắc chắn muốn bắt đầu khai thác tất cả tài khoản Gmail?',
        confirmPauseAll: 'Bạn có chắc chắn muốn tạm dừng tất cả tiến trình khai thác?',
        confirmResumeAll: 'Bạn có chắc chắn muốn tiếp tục tất cả tiến trình khai thác?',
        confirmStopAll: 'Bạn có chắc chắn muốn dừng tất cả tiến trình khai thác?',
        confirmClearLogs: 'Bạn có chắc chắn muốn xóa tất cả logs?',
        startAllSuccess: 'Đã bắt đầu khai thác tất cả tài khoản Gmail',
        pauseAllSuccess: 'Đã tạm dừng tất cả tiến trình khai thác',
        resumeAllSuccess: 'Đã tiếp tục tất cả tiến trình khai thác',
        stopAllSuccess: 'Đã dừng tất cả tiến trình khai thác',
        startAllFailed: 'Không thể bắt đầu khai thác: {0}',
        pauseAllFailed: 'Không thể tạm dừng: {0}',
        resumeAllFailed: 'Không thể tiếp tục: {0}',
        stopAllFailed: 'Không thể dừng: {0}',
        logsCleared: 'Đã xóa tất cả logs',
        confirmPauseExtraction: 'Bạn có chắc chắn muốn tạm dừng tiến trình khai thác này?',
        confirmCancelExtraction: 'Bạn có chắc chắn muốn dừng tiến trình khai thác này?',
        extractionDetails: 'Chi tiết tiến trình khai thác',
        basicInfo: 'Thông tin cơ bản',
        dataStats: 'Thống kê dữ liệu',
        emailsProcessed: 'Emails đã xử lý',
        contactsFound: 'Liên hệ tìm thấy',
        attachmentsFound: 'Tệp đính kèm',
        dataSize: 'Dung lượng dữ liệu',
        startTime: 'Bắt đầu lúc',
        runTime: 'Thời gian chạy',
        currentStep: 'Bước hiện tại',
        progressPercentage: 'Tiến trình: {0}%',
        processingSpeed: '{0}/giây',
        logTimestamp: 'Thời gian',
        logLevel: 'Cấp độ',
        logMessage: 'Tin nhắn'
    },

    // Gmail Data Viewer
    dataViewer: {
        title: 'Gmail Data Viewer',
        subtitle: 'Xem trước và khám phá dữ liệu đã khai thác từ Gmail',
        totalEmails: 'Tổng emails',
        totalContacts: 'Liên hệ',
        totalAttachments: 'Tệp đính kèm',
        dataSize: 'Dung lượng dữ liệu',
        searchAllData: 'Tìm kiếm trong tất cả dữ liệu...',
        allDataTypes: 'Tất cả loại dữ liệu',
        emailsType: 'Emails',
        contactsType: 'Liên hệ',
        attachmentsType: 'Tệp đính kèm',
        allTime: 'Tất cả thời gian',
        today: 'Hôm nay',
        thisWeek: 'Tuần này',
        thisMonth: 'Tháng này',
        custom: 'Tùy chỉnh',
        senderFilter: 'Lọc theo người gửi',
        exportSelected: 'Xuất dữ liệu đã chọn',
        refreshData: 'Làm mới dữ liệu',
        extractedData: 'Dữ liệu đã khai thác',
        sortBy: 'Sắp xếp theo',
        sortDate: 'Theo ngày',
        sortSender: 'Theo người gửi',
        sortSize: 'Theo kích thước',
        previewPane: 'Xem trước',
        selectToPreview: 'Chọn một mục từ danh sách để xem trước',
        selectAllInPreview: 'Chọn tất cả',
        exportPreviewItem: 'Xuất mục này',
        noData: 'Không có dữ liệu nào phù hợp',
        noDataDesc: 'Không tìm thấy dữ liệu phù hợp với bộ lọc hiện tại',
        emailDetails: 'Chi tiết Email',
        from: 'Từ',
        to: 'Đến',
        subject: 'Chủ đề',
        content: 'Nội dung',
        attachments: 'Tệp đính kèm',
        noSubject: 'Không có chủ đề',
        noContent: 'Không có nội dung',
        noName: 'Không có tên',
        noEmail: 'Không có email',
        contactName: 'Tên liên hệ',
        contactEmail: 'Email liên hệ',
        contactPhone: 'Điện thoại liên hệ',
        contactCompany: 'Công ty',
        contactPosition: 'Chức vụ',
        communicationStats: 'Thống kê giao tiếp',
        emailsSent: 'Emails đã gửi',
        lastContact: 'Liên hệ cuối',
        attachmentFile: 'Tệp đính kèm',
        attachmentSize: 'Kích thước',
        attachmentType: 'Loại tệp',
        sourceEmail: 'Email nguồn',
        contentAnalysis: 'Phân tích nội dung',
        downloadAttachment: 'Tải xuống',
        viewFullEmail: 'Xem đầy đủ',
        exportEmail: 'Xuất Email',
        pdfDocument: 'Tài liệu PDF',
        imageFile: 'Tệp hình ảnh',
        archiveFile: 'Tệp nén',
        unknownType: 'Loại không xác định',
        searchHighlight: 'Đánh dấu tìm kiếm',
        dataNotFound: 'Không tìm thấy dữ liệu',
        loadingData: 'Đang tải dữ liệu Gmail...',
        loadingAllData: 'Đang tải tất cả dữ liệu Gmail...',
        loadFailed: 'Không thể tải dữ liệu Gmail: {0}',
        selectAtLeastOne: 'Vui lòng chọn ít nhất một mục để xuất'
    },

    // Gmail Export Interface
    exportInterface: {
        title: 'Gmail Export Interface',
        subtitle: 'Cấu hình và xuất dữ liệu Gmail với nhiều định dạng và tùy chọn nâng cao',
        totalExports: 'Tổng lượt xuất',
        completedExports: 'Hoàn thành',
        processingExports: 'Đang xử lý',
        totalExportSize: 'Dung lượng xuất',
        dataSource: 'Nguồn dữ liệu',
        selectGmailAccount: 'Chọn tài khoản Gmail:',
        allAccounts: 'Tất cả tài khoản',
        dataTypes: 'Loại dữ liệu:',
        emails: 'Emails',
        contacts: 'Liên hệ',
        attachments: 'Tệp đính kèm',
        exportFormat: 'Định dạng xuất',
        formatDescription: 'Định dạng đã chọn:',
        selectFormatFirst: 'Chọn định dạng xuất từ các tùy chọn bên trên',
        jsonFormat: 'JSON',
        jsonDesc: 'Dữ liệu có cấu trúc, dễ dàng xử lý bằng code',
        csvFormat: 'CSV',
        csvDesc: 'Định dạng bảng tính, tương thích với Excel',
        pdfFormat: 'PDF',
        pdfDesc: 'Báo cáo chuyên nghiệp với định dạng đẹp',
        xmlFormat: 'XML',
        xmlDesc: 'Định dạng trao đổi dữ liệu chuẩn',
        template: 'Mẫu xuất (Template)',
        createTemplate: 'Tạo mẫu mới',
        noTemplates: 'Chưa có mẫu xuất nào',
        noTemplatesDesc: 'Chưa có mẫu xuất nào được tạo',
        advancedOptions: 'Tùy chọn nâng cao',
        dateFilter: 'Lọc theo ngày:',
        to: 'đến',
        senderFilter: 'Lọc theo người gửi:',
        enterSenderEmail: 'Nhập email người gửi',
        keywordSearch: 'Từ khóa tìm kiếm:',
        searchInContent: 'Tìm kiếm trong nội dung',
        limitRecords: 'Giới hạn số lượng:',
        noLimit: 'Không giới hạn',
        includeAttachments: 'Bao gồm tệp đính kèm trong xuất',
        compressOutput: 'Nén tệp xuất (ZIP)',
        encryptOutput: 'Mã hóa tệp xuất',
        performExport: 'Thực hiện xuất',
        startExport: 'Bắt đầu xuất',
        previewExport: 'Xem trước',
        scheduleExport: 'Lên lịch',
        quickExport: 'Xuất nhanh',
        saveTemplate: 'Lưu mẫu',
        currentExportStatus: 'Trạng thái xuất hiện tại',
        noExportInProgress: 'Không có tiến trình xuất nào',
        exportHistory: 'Lịch sử xuất',
        noExportHistory: 'Chưa có lịch sử xuất nào',
        scheduledExports: 'Xuất theo lịch trình',
        noScheduledExports: 'Chưa có lịch xuất nào',
        noScheduledExportsDesc: 'Chưa có lịch xuất nào được tạo',
        addSchedule: 'Thêm lịch',
        formatSelected: 'Định dạng đã chọn',
        selectFormatWarning: 'Vui lòng chọn định dạng xuất',
        startingExport: 'Đang bắt đầu xuất dữ liệu...',
        exportStarted: 'Đã bắt đầu xuất dữ liệu',
        exportFailed: 'Không thể bắt đầu xuất: {0}',
        templateModal: 'Tạo/Lưu mẫu xuất',
        templateName: 'Tên mẫu:',
        enterTemplateName: 'Nhập tên mẫu xuất',
        templateDescription: 'Mô tả:',
        templateDescriptionPlaceholder: 'Mô tả về mẫu xuất này',
        templateConfig: 'Cấu hình mẫu:',
        saveTemplate: 'Lưu mẫu',
        scheduleModal: 'Lên lịch xuất dữ liệu',
        scheduleName: 'Tên lịch xuất:',
        enterScheduleName: 'Nhập tên lịch xuất',
        frequency: 'Tần suất:',
        daily: 'Hàng ngày',
        weekly: 'Hàng tuần',
        monthly: 'Hàng tháng',
        exportTime: 'Thời gian xuất:',
        enableSchedule: 'Kích hoạt lịch xuất này',
        saveSchedule: 'Lưu lịch',
        downloadFile: 'Tải xuống',
        viewDetails: 'Chi tiết',
        deleteFile: 'Xóa',
        editTemplate: 'Chỉnh sửa',
        duplicateTemplate: 'Sao chép',
        deleteTemplate: 'Xóa',
        toggleSchedule: 'Chuyển đổi trạng thái',
        activate: 'Kích hoạt',
        deactivate: 'Vô hiệu hóa',
        deleteSchedule: 'Xóa lịch',
        confirmStartExport: 'Bạn có chắc chắn muốn bắt đầu xuất dữ liệu?',
        confirmScheduleExport: 'Bạn có chắc chắn muốn lên lịch xuất này?',
        confirmDeleteExport: 'Bạn có chắc chắn muốn xóa tệp xuất này?',
        confirmDeleteTemplate: 'Bạn có chắc chắn muốn xóa mẫu này?',
        confirmDeleteSchedule: 'Bạn có chắc chắn muốn xóa lịch xuất này?',
        exportCompleted: 'Hoàn thành xuất dữ liệu',
        exportFailed: 'Thất bại xuất dữ liệu: {0}',
        scheduleSaved: 'Đã lưu lịch xuất',
        scheduleDeleted: 'Đã xóa lịch xuất',
        templateSaved: 'Đã lưu mẫu xuất',
        templateDeleted: 'Đã xóa mẫu xuất',
        fileDeleted: 'Đã xóa tệp xuất',
        operationFailed: 'Thao tác thất bại: {0}'
    },

    // Status and messages
    status: {
        active: 'Đang hoạt động',
        expired: 'Đã hết hạn',
        revoked: 'Đã thu hồi',
        completed: 'Hoàn thành',
        in_progress: 'Đang thực hiện',
        failed: 'Thất bại',
        paused: 'Tạm dừng',
        scheduled: 'Đã lên lịch',
        cancelled: 'Đã hủy',
        pending: 'Đang chờ',
        processing: 'Đang xử lý',
        success: 'Thành công',
        error: 'Lỗi',
        warning: 'Cảnh báo',
        info: 'Thông tin'
    },

    // File sizes
    fileSize: {
        bytes: 'Bytes',
        kb: 'KB',
        mb: 'MB',
        gb: 'GB',
        tb: 'TB'
    },

    // Time units
    time: {
        second: 'giây',
        minute: 'phút',
        hour: 'giờ',
        day: 'ngày',
        week: 'tuần',
        month: 'tháng',
        year: 'năm'
    },

    // Date formats
    dateFormat: {
        short: 'DD/MM/YYYY',
        long: 'DD/MM/YYYY HH:mm',
        full: 'DD/MM/YYYY HH:mm:ss',
        withSeconds: 'DD/MM/YYYY HH:mm:ss'
    }
};

/**
 * Get localized text
 * @param {string} section - Section name (e.g., 'common', 'gmailAccess')
 * @param {string} key - Text key
 * @param {object} params - Parameters for string formatting
 * @returns {string} Localized text
 */
function getLocalizedText(section, key, params = {}) {
    let text = '';

    if (section && GmailLocalization[section] && GmailLocalization[section][key]) {
        text = GmailLocalization[section][key];
    } else if (GmailLocalization.common[key]) {
        text = GmailLocalization.common[key];
    } else {
        text = key; // Fallback to key if not found
    }

    // Replace parameters in text
    if (params) {
        for (const [param, value] of Object.entries(params)) {
            text = text.replace(new RegExp(`{${param}}`, 'g'), value);
        }
    }

    return text;
}

/**
 * Format file size with localization
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSizeLocalized(bytes) {
    if (bytes === 0) return `0 ${GmailLocalization.fileSize.bytes}`;

    const k = 1024;
    const sizes = [
        GmailLocalization.fileSize.bytes,
        GmailLocalization.fileSize.kb,
        GmailLocalization.fileSize.mb,
        GmailLocalization.fileSize.gb
    ];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format date with localization
 * @param {string} dateString - Date string
 * @param {string} format - Date format
 * @returns {string} Formatted date
 */
function formatDateLocalized(dateString, format = 'long') {
    if (!dateString) return GmailLocalization.common.na;

    const date = new Date(dateString);
    const formatPattern = GmailLocalization.dateFormat[format] || GmailLocalization.dateFormat.long;

    // Simple date formatting (can be enhanced with moment.js if available)
    return date.toLocaleDateString('vi-VN') + ' ' + date.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Format duration with localization
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration
 */
function formatDurationLocalized(seconds) {
    if (!seconds) return GmailLocalization.common.na;

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

/**
 * Get localized status text
 * @param {string} status - Status value
 * @param {string} section - Section for status texts
 * @returns {string} Localized status text
 */
function getLocalizedStatus(status, section = 'status') {
    if (GmailLocalization[section] && GmailLocalization[section][status]) {
        return GmailLocalization[section][status];
    }
    return status;
}

/**
 * Initialize localization for current page
 */
function initializeLocalization() {
    // Set page title if available
    const titleElement = document.querySelector('title');
    if (titleElement) {
        const currentInterface = getCurrentInterface();
        if (GmailLocalization[currentInterface] && GmailLocalization[currentInterface].title) {
            titleElement.textContent = GmailLocalization[currentInterface].title + ' - ZaloPay Admin';
        }
    }

    // Set subtitle if available
    const subtitleElement = document.querySelector('.text-muted');
    if (subtitleElement) {
        const currentInterface = getCurrentInterface();
        if (GmailLocalization[currentInterface] && GmailLocalization[currentInterface].subtitle) {
            subtitleElement.textContent = GmailLocalization[currentInterface].subtitle;
        }
    }
}

/**
 * Get current interface name based on URL
 */
function getCurrentInterface() {
    const path = window.location.pathname;
    const filename = path.substring(path.lastIndexOf('/') + 1);

    if (filename.includes('gmail_access')) return 'gmailAccess';
    if (filename.includes('gmail_extraction_progress')) return 'extractionProgress';
    if (filename.includes('gmail_data_viewer')) return 'dataViewer';
    if (filename.includes('gmail_export_interface')) return 'exportInterface';

    return 'common';
}

// Initialize localization when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeLocalization();
});