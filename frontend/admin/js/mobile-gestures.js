/**
 * Mobile Gestures & Accessibility Enhancements
 * ZaloPay Admin Portal - Touch & Accessibility Optimization
 */

// Touch gesture management class
class TouchGestureManager {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.minSwipeDistance = 50;
        this.longPressDuration = 500;
        this.longPressTimer = null;
        this.isLongPress = false;

        this.init();
    }

    init() {
        // Bind touch events
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });

        // Add accessibility enhancements
        this.enhanceAccessibility();

        // Add keyboard navigation support
        this.addKeyboardNavigation();
    }

    handleTouchStart(e) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;

        // Start long press timer
        this.longPressTimer = setTimeout(() => {
            this.isLongPress = true;
            this.handleLongPress(e);
        }, this.longPressDuration);
    }

    handleTouchMove(e) {
        if (!this.touchStartX || !this.touchStartY) return;

        const currentX = e.touches[0].clientX;
        const currentY = e.touches[0].clientY;

        // Cancel long press if finger moves too much
        const deltaX = Math.abs(currentX - this.touchStartX);
        const deltaY = Math.abs(currentY - this.touchStartY);

        if (deltaX > 10 || deltaY > 10) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
    }

    handleTouchEnd(e) {
        // Clear long press timer
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }

        if (this.isLongPress) {
            this.isLongPress = false;
            return;
        }

        this.touchEndX = e.changedTouches[0].clientX;
        this.touchEndY = e.changedTouches[0].clientY;

        this.handleGesture(e);
    }

    handleGesture(e) {
        const deltaX = this.touchStartX - this.touchEndX;
        const deltaY = this.touchStartY - this.touchEndY;
        const absDeltaX = Math.abs(deltaX);
        const absDeltaY = Math.abs(deltaY);

        // Determine primary direction
        if (Math.max(absDeltaX, absDeltaY) > this.minSwipeDistance) {
            if (absDeltaX > absDeltaY) {
                // Horizontal swipe
                if (deltaX > 0) {
                    this.handleSwipeLeft(e);
                } else {
                    this.handleSwipeRight(e);
                }
            } else {
                // Vertical swipe
                if (deltaY > 0) {
                    this.handleSwipeUp(e);
                } else {
                    this.handleSwipeDown(e);
                }
            }
        }
    }

    handleLongPress(e) {
        const target = e.target;

        // Add visual feedback for long press
        target.classList.add('long-press-active');

        // Show context menu for long press
        this.showContextMenu(e, target);

        // Remove long press class after animation
        setTimeout(() => {
            target.classList.remove('long-press-active');
        }, 200);
    }

    handleSwipeLeft(e) {
        const target = e.target;

        // Chart navigation
        if (target.closest('.chart-container')) {
            this.navigateChart('next');
            return;
        }

        // Table navigation
        if (target.closest('.table-responsive')) {
            this.scrollTable('right');
            return;
        }

        // Card swipe action
        if (target.closest('.card')) {
            this.handleCardSwipe(target.closest('.card'), 'left');
        }
    }

    handleSwipeRight(e) {
        const target = e.target;

        // Chart navigation
        if (target.closest('.chart-container')) {
            this.navigateChart('prev');
            return;
        }

        // Table navigation
        if (target.closest('.table-responsive')) {
            this.scrollTable('left');
            return;
        }

        // Card swipe action
        if (target.closest('.card')) {
            this.handleCardSwipe(target.closest('.card'), 'right');
        }
    }

    handleSwipeUp(e) {
        const target = e.target;

        // Pull to refresh on main content
        if (target.closest('.container-fluid') && !target.closest('.sidebar')) {
            this.pullToRefresh();
        }
    }

    handleSwipeDown(e) {
        const target = e.target;

        // Show mobile menu
        if (target.closest('.container-fluid') && !target.closest('.sidebar')) {
            this.showMobileMenu();
        }
    }

    handleCardSwipe(card, direction) {
        // Add swipe animation
        card.style.transform = direction === 'left' ?
            'translateX(-10px) rotateY(-5deg)' :
            'translateX(10px) rotateY(5deg)';

        setTimeout(() => {
            card.style.transform = '';
        }, 200);

        // Show card actions
        this.showCardActions(card, direction);
    }

    showContextMenu(e, target) {
        // Create context menu for long press
        const contextMenu = document.createElement('div');
        contextMenu.className = 'context-menu';
        contextMenu.innerHTML = `
            <div class="context-menu-item" onclick="copyToClipboard()">
                <i class="fas fa-copy"></i> Copy
            </div>
            <div class="context-menu-item" onclick="shareContent()">
                <i class="fas fa-share"></i> Share
            </div>
            <div class="context-menu-item" onclick="addToFavorites()">
                <i class="fas fa-star"></i> Favorite
            </div>
        `;

        // Position context menu
        const touch = e.touches[0];
        contextMenu.style.position = 'fixed';
        contextMenu.style.left = touch.clientX + 'px';
        contextMenu.style.top = touch.clientY + 'px';
        contextMenu.style.zIndex = '9999';

        document.body.appendChild(contextMenu);

        // Remove context menu on outside click
        setTimeout(() => {
            if (contextMenu.parentNode) {
                contextMenu.parentNode.removeChild(contextMenu);
            }
        }, 3000);
    }

    navigateChart(direction) {
        // Find active chart time range selector
        const timeRangeSelect = document.getElementById('chartTimeRange');
        if (timeRangeSelect) {
            const options = timeRangeSelect.options;
            const currentIndex = timeRangeSelect.selectedIndex;

            if (direction === 'next' && currentIndex < options.length - 1) {
                timeRangeSelect.selectedIndex = currentIndex + 1;
                // Trigger change event
                timeRangeSelect.dispatchEvent(new Event('change'));
                showToast('Chuyển đến khoảng thời gian tiếp theo', 'info');
            } else if (direction === 'prev' && currentIndex > 0) {
                timeRangeSelect.selectedIndex = currentIndex - 1;
                timeRangeSelect.dispatchEvent(new Event('change'));
                showToast('Chuyển đến khoảng thời gian trước đó', 'info');
            }
        }
    }

    scrollTable(direction) {
        const tableContainer = document.querySelector('.table-responsive');
        if (tableContainer) {
            const scrollAmount = 200;
            const currentScroll = tableContainer.scrollLeft;

            if (direction === 'left') {
                tableContainer.scrollLeft = Math.max(0, currentScroll - scrollAmount);
            } else {
                tableContainer.scrollLeft = currentScroll + scrollAmount;
            }
        }
    }

    pullToRefresh() {
        // Show pull to refresh indicator
        const indicator = document.createElement('div');
        indicator.className = 'pull-refresh-indicator';
        indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Đang làm mới...';
        indicator.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: var(--primary-color);
            color: white;
            text-align: center;
            padding: 10px;
            z-index: 9999;
            font-size: 14px;
        `;

        document.body.appendChild(indicator);

        // Simulate refresh
        setTimeout(() => {
            // Refresh current page data
            if (window.location.pathname.includes('dashboard')) {
                updateDashboard();
            } else if (window.location.pathname.includes('victim')) {
                refreshData();
            } else if (window.location.pathname.includes('campaign')) {
                refreshCampaigns();
            }

            // Remove indicator
            if (indicator.parentNode) {
                indicator.parentNode.removeChild(indicator);
            }
        }, 1500);
    }

    showMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        const backdrop = document.querySelector('.sidebar-backdrop');

        if (sidebar && backdrop) {
            sidebar.classList.add('show');
            backdrop.classList.add('show');
        }
    }

    showCardActions(card, direction) {
        // Show quick actions for card
        const actions = card.querySelector('.card-actions') || this.createCardActions(card);

        actions.style.display = 'flex';
        actions.style.position = 'absolute';
        actions.style.top = '10px';
        actions.style.right = direction === 'left' ? '10px' : 'auto';
        actions.style.left = direction === 'right' ? '10px' : 'auto';

        setTimeout(() => {
            actions.style.display = 'none';
        }, 3000);
    }

    createCardActions(card) {
        const actions = document.createElement('div');
        actions.className = 'card-actions';
        actions.style.cssText = `
            display: none;
            gap: 5px;
            background: rgba(0, 0, 0, 0.8);
            padding: 5px;
            border-radius: 5px;
        `;

        actions.innerHTML = `
            <button class="btn btn-sm btn-outline-light" onclick="editCard()" title="Edit">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-outline-light" onclick="deleteCard()" title="Delete">
                <i class="fas fa-trash"></i>
            </button>
        `;

        card.style.position = 'relative';
        card.appendChild(actions);

        return actions;
    }

    enhanceAccessibility() {
        // Add ARIA labels to interactive elements
        document.querySelectorAll('.btn').forEach(btn => {
            if (!btn.getAttribute('aria-label')) {
                const icon = btn.querySelector('i');
                const text = btn.textContent.trim();
                if (icon && text) {
                    btn.setAttribute('aria-label', text);
                }
            }
        });

        // Add skip links for keyboard navigation
        this.addSkipLinks();

        // Enhance form accessibility
        this.enhanceFormAccessibility();

        // Add live regions for dynamic content
        this.addLiveRegions();
    }

    addSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Bỏ qua đến nội dung chính';
        skipLink.className = 'skip-link';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--primary-color);
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 9999;
            transition: top 0.3s;
        `;

        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });

        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });

        document.body.insertBefore(skipLink, document.body.firstChild);

        // Add main content ID
        const mainContent = document.querySelector('.container-fluid');
        if (mainContent) {
            mainContent.id = 'main-content';
            mainContent.setAttribute('tabindex', '-1');
        }
    }

    enhanceFormAccessibility() {
        // Add proper labels to form controls
        document.querySelectorAll('input, select, textarea').forEach(control => {
            const label = document.querySelector(`label[for="${control.id}"]`);
            if (!label && !control.getAttribute('aria-label')) {
                // Create aria-label from placeholder or nearby text
                const placeholder = control.getAttribute('placeholder');
                if (placeholder) {
                    control.setAttribute('aria-label', placeholder);
                }
            }
        });

        // Add form validation feedback
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const invalidControls = form.querySelectorAll(':invalid');
                if (invalidControls.length > 0) {
                    e.preventDefault();
                    invalidControls[0].focus();
                    this.announceToScreenReader(`Vui lòng kiểm tra ${invalidControls.length} trường không hợp lệ`);
                }
            });
        });
    }

    addLiveRegions() {
        // Create live region for announcements
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-region';
        document.body.appendChild(liveRegion);
    }

    announceToScreenReader(message) {
        const liveRegion = document.getElementById('live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }

    addKeyboardNavigation() {
        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Alt + M: Toggle mobile menu
            if (e.altKey && e.key === 'm') {
                e.preventDefault();
                this.showMobileMenu();
            }

            // Alt + R: Refresh current page
            if (e.altKey && e.key === 'r') {
                e.preventDefault();
                this.refreshCurrentPage();
            }

            // Escape: Close modals and menus
            if (e.key === 'Escape') {
                this.closeAllModals();
                this.closeMobileMenu();
            }
        });
    }

    refreshCurrentPage() {
        // Refresh based on current page
        if (window.location.pathname.includes('dashboard')) {
            updateDashboard();
        } else if (window.location.pathname.includes('victim')) {
            refreshData();
        } else if (window.location.pathname.includes('campaign')) {
            refreshCampaigns();
        } else {
            window.location.reload();
        }
    }

    closeAllModals() {
        document.querySelectorAll('.modal.show').forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }

    closeMobileMenu() {
        const sidebar = document.querySelector('.sidebar.show');
        const backdrop = document.querySelector('.sidebar-backdrop.show');

        if (sidebar) sidebar.classList.remove('show');
        if (backdrop) backdrop.classList.remove('show');
    }
}

// Accessibility utilities
class AccessibilityManager {
    constructor() {
        this.init();
    }

    init() {
        // Add focus indicators
        this.addFocusIndicators();

        // Add high contrast support
        this.addHighContrastSupport();

        // Add reduced motion support
        this.addReducedMotionSupport();

        // Add screen reader optimizations
        this.optimizeForScreenReaders();
    }

    addFocusIndicators() {
        // Enhanced focus styles
        const focusStyle = document.createElement('style');
        focusStyle.textContent = `
            .focus-visible {
                outline: 3px solid var(--primary-color) !important;
                outline-offset: 2px !important;
            }

            .btn:focus-visible,
            .form-control:focus-visible,
            .form-select:focus-visible {
                outline: 3px solid var(--primary-color) !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 0 3px rgba(0, 104, 255, 0.2) !important;
            }
        `;
        document.head.appendChild(focusStyle);
    }

    addHighContrastSupport() {
        // Detect high contrast preference
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            document.body.classList.add('high-contrast');
        }

        // Listen for changes
        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            if (e.matches) {
                document.body.classList.add('high-contrast');
            } else {
                document.body.classList.remove('high-contrast');
            }
        });
    }

    addReducedMotionSupport() {
        // Detect reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduced-motion');
        }

        // Listen for changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            if (e.matches) {
                document.body.classList.add('reduced-motion');
            } else {
                document.body.classList.remove('reduced-motion');
            }
        });
    }

    optimizeForScreenReaders() {
        // Add screen reader only content
        document.querySelectorAll('[data-sr-text]').forEach(element => {
            const srText = element.getAttribute('data-sr-text');
            const srSpan = document.createElement('span');
            srSpan.className = 'sr-only';
            srSpan.textContent = srText;
            element.appendChild(srSpan);
        });

        // Add table headers for screen readers
        document.querySelectorAll('.table').forEach(table => {
            if (!table.getAttribute('role')) {
                table.setAttribute('role', 'table');
            }

            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                header.setAttribute('scope', 'col');
                if (!header.getAttribute('id')) {
                    header.id = `header-${index}`;
                }
            });

            const cells = table.querySelectorAll('td');
            cells.forEach((cell, index) => {
                const headerIndex = index % headers.length;
                const headerId = headers[headerIndex]?.id;
                if (headerId) {
                    cell.setAttribute('headers', headerId);
                }
            });
        });
    }
}

// Touch feedback manager
class TouchFeedbackManager {
    constructor() {
        this.init();
    }

    init() {
        // Add touch feedback to all interactive elements
        document.querySelectorAll('button, .btn, .card, .info-box').forEach(element => {
            this.addTouchFeedback(element);
        });

        // Add haptic feedback simulation
        this.addHapticFeedback();
    }

    addTouchFeedback(element) {
        let touchTimer = null;

        element.addEventListener('touchstart', (e) => {
            // Add visual feedback
            element.classList.add('touch-active');

            // Add ripple effect
            this.createRippleEffect(e, element);

            // Clear any existing timer
            if (touchTimer) {
                clearTimeout(touchTimer);
            }

            // Set long press feedback
            touchTimer = setTimeout(() => {
                element.classList.add('long-press-feedback');
            }, 500);
        }, { passive: true });

        element.addEventListener('touchend', () => {
            // Remove visual feedback
            element.classList.remove('touch-active', 'long-press-feedback');

            // Clear timer
            if (touchTimer) {
                clearTimeout(touchTimer);
                touchTimer = null;
            }
        }, { passive: true });

        element.addEventListener('touchcancel', () => {
            // Remove all feedback classes
            element.classList.remove('touch-active', 'long-press-feedback');

            // Clear timer
            if (touchTimer) {
                clearTimeout(touchTimer);
                touchTimer = null;
            }
        }, { passive: true });
    }

    createRippleEffect(e, element) {
        const touch = e.touches[0];
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = touch.clientX - rect.left - size / 2;
        const y = touch.clientY - rect.top - size / 2;

        const ripple = document.createElement('div');
        ripple.className = 'ripple-effect';
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(0, 104, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
            z-index: 1000;
        `;

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        // Remove ripple after animation
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    addHapticFeedback() {
        // Add CSS for ripple animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple-animation {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }

            .touch-active {
                transform: scale(0.95);
                transition: transform 0.1s ease;
            }

            .long-press-feedback {
                background-color: rgba(0, 104, 255, 0.1) !important;
                transform: scale(1.05);
            }

            .context-menu {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                min-width: 150px;
                animation: context-menu-appear 0.2s ease;
            }

            .context-menu-item {
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
                transition: background-color 0.2s;
            }

            .context-menu-item:hover {
                background-color: #f8f9fa;
            }

            .context-menu-item:last-child {
                border-bottom: none;
            }

            @keyframes context-menu-appear {
                from {
                    opacity: 0;
                    transform: scale(0.8);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }

            .pull-refresh-indicator {
                animation: slide-down 0.3s ease;
            }

            @keyframes slide-down {
                from {
                    transform: translateY(-100%);
                }
                to {
                    transform: translateY(0);
                }
            }

            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }

            .skip-link:focus {
                top: 6px !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize managers when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize touch gesture manager
    window.touchGestureManager = new TouchGestureManager();

    // Initialize accessibility manager
    window.accessibilityManager = new AccessibilityManager();

    // Initialize touch feedback manager
    window.touchFeedbackManager = new TouchFeedbackManager();

    // Add mobile-specific enhancements
    addMobileEnhancements();
});

// Mobile-specific enhancements
function addMobileEnhancements() {
    // Add viewport height fix for mobile browsers
    function setVH() {
        let vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }

    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', setVH);

    // Add safe area support for devices with notches
    function setSafeArea() {
        const style = document.createElement('style');
        style.textContent = `
            .safe-area-top { padding-top: env(safe-area-inset-top); }
            .safe-area-bottom { padding-bottom: env(safe-area-inset-bottom); }
            .safe-area-left { padding-left: env(safe-area-inset-left); }
            .safe-area-right { padding-right: env(safe-area-inset-right); }
        `;
        document.head.appendChild(style);
    }

    setSafeArea();

    // Add performance monitoring for mobile
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData && perfData.loadEventEnd - perfData.loadEventStart > 3000) {
                    console.warn('Page load took longer than 3 seconds on mobile');
                }
            }, 0);
        });
    }
}

// Global utility functions
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'warning' ? 'warning' : type === 'danger' ? 'danger' : 'info'} border-0" role="alert" aria-live="assertive">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Đóng thông báo"></button>
            </div>
        </div>
    `;

    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.setAttribute('aria-live', 'polite');
        toastContainer.setAttribute('aria-atomic', 'false');
        document.body.appendChild(toastContainer);
    }

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toast = new bootstrap.Toast(toastContainer.lastElementChild);
    toast.show();
}

function copyToClipboard() {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(window.getSelection().toString()).then(() => {
            showToast('Đã sao chép vào clipboard', 'success');
        }).catch(() => {
            showToast('Không thể sao chép', 'error');
        });
    }
}

function shareContent() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            text: 'Chia sẻ nội dung từ ZaloPay Admin Portal',
            url: window.location.href
        }).catch(() => {
            showToast('Không thể chia sẻ', 'error');
        });
    } else {
        showToast('Chia sẻ không được hỗ trợ trên thiết bị này', 'warning');
    }
}

function addToFavorites() {
    showToast('Đã thêm vào danh sách yêu thích', 'success');
    // Implementation would add to favorites
}