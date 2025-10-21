/**
 * Device Fingerprinting Library
 * Creates unique device fingerprints for tracking and security
 */

class DeviceFingerprint {
    constructor() {
        this.fingerprint = null;
        this.components = {};
    }

    /**
     * Generate device fingerprint
     */
    async generate() {
        try {
            // Collect fingerprint components
            this.components = {
                userAgent: this.getUserAgent(),
                language: this.getLanguage(),
                timezone: this.getTimezone(),
                screen: this.getScreenInfo(),
                canvas: await this.getCanvasFingerprint(),
                webgl: this.getWebGLFingerprint(),
                audio: await this.getAudioFingerprint(),
                fonts: this.getFonts(),
                plugins: this.getPlugins(),
                storage: this.getStorageInfo(),
                connection: this.getConnectionInfo(),
                hardware: this.getHardwareInfo(),
                browser: this.getBrowserInfo(),
                os: this.getOSInfo(),
                timestamp: Date.now()
            };

            // Generate hash from components
            this.fingerprint = await this.hashFingerprint(this.components);
            
            return this.fingerprint;
        } catch (error) {
            console.error('Error generating fingerprint:', error);
            return this.generateFallbackFingerprint();
        }
    }

    /**
     * Get user agent string
     */
    getUserAgent() {
        return navigator.userAgent;
    }

    /**
     * Get browser language
     */
    getLanguage() {
        return {
            language: navigator.language,
            languages: navigator.languages,
            platform: navigator.platform
        };
    }

    /**
     * Get timezone information
     */
    getTimezone() {
        return {
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset(),
            locale: Intl.DateTimeFormat().resolvedOptions().locale
        };
    }

    /**
     * Get screen information
     */
    getScreenInfo() {
        return {
            width: screen.width,
            height: screen.height,
            availWidth: screen.availWidth,
            availHeight: screen.availHeight,
            colorDepth: screen.colorDepth,
            pixelDepth: screen.pixelDepth,
            devicePixelRatio: window.devicePixelRatio || 1
        };
    }

    /**
     * Generate canvas fingerprint
     */
    async getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size
            canvas.width = 200;
            canvas.height = 50;
            
            // Draw text
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('ZaloPay Merchant', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('ZaloPay Merchant', 4, 17);
            
            // Draw shapes
            ctx.globalCompositeOperation = 'multiply';
            ctx.fillStyle = 'rgb(255,0,255)';
            ctx.beginPath();
            ctx.arc(50, 50, 50, 0, Math.PI * 2, true);
            ctx.closePath();
            ctx.fill();
            ctx.fillStyle = 'rgb(0,255,255)';
            ctx.beginPath();
            ctx.arc(100, 50, 50, 0, Math.PI * 2, true);
            ctx.closePath();
            ctx.fill();
            ctx.fillStyle = 'rgb(255,255,0)';
            ctx.beginPath();
            ctx.arc(75, 100, 50, 0, Math.PI * 2, true);
            ctx.closePath();
            ctx.fill();
            
            return canvas.toDataURL();
        } catch (error) {
            return 'canvas_error';
        }
    }

    /**
     * Get WebGL fingerprint
     */
    getWebGLFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) {
                return 'webgl_not_supported';
            }

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            
            return {
                vendor: gl.getParameter(debugInfo ? debugInfo.UNMASKED_VENDOR_WEBGL : gl.VENDOR),
                renderer: gl.getParameter(debugInfo ? debugInfo.UNMASKED_RENDERER_WEBGL : gl.RENDERER),
                version: gl.getParameter(gl.VERSION),
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                extensions: gl.getSupportedExtensions()
            };
        } catch (error) {
            return 'webgl_error';
        }
    }

    /**
     * Generate audio fingerprint
     */
    async getAudioFingerprint() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const analyser = audioContext.createAnalyser();
            const gainNode = audioContext.createGain();
            const scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);

            oscillator.type = 'triangle';
            oscillator.frequency.setValueAtTime(10000, audioContext.currentTime);

            gainNode.gain.setValueAtTime(0, audioContext.currentTime);

            oscillator.connect(analyser);
            analyser.connect(scriptProcessor);
            scriptProcessor.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.start(0);

            return new Promise((resolve) => {
                scriptProcessor.onaudioprocess = function(bins) {
                    const array = new Float32Array(analyser.frequencyBinCount);
                    analyser.getFloatFrequencyData(array);
                    
                    oscillator.stop();
                    audioContext.close();
                    
                    resolve(array.slice(0, 30).join(','));
                };
            });
        } catch (error) {
            return 'audio_error';
        }
    }

    /**
     * Get available fonts
     */
    getFonts() {
        const fonts = [
            'Arial', 'Arial Black', 'Arial Narrow', 'Arial Rounded MT Bold',
            'Calibri', 'Cambria', 'Candara', 'Century Gothic', 'Comic Sans MS',
            'Consolas', 'Courier New', 'Franklin Gothic Medium', 'Gadget',
            'Georgia', 'Helvetica', 'Impact', 'Lucida Console', 'Lucida Sans Unicode',
            'Microsoft Sans Serif', 'Palatino Linotype', 'Segoe UI', 'Tahoma',
            'Times New Roman', 'Trebuchet MS', 'Verdana', 'Webdings', 'Wingdings'
        ];

        const availableFonts = [];
        const testString = 'mmmmmmmmmmlli';
        const testSize = '72px';
        const h = document.getElementsByTagName('body')[0];

        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const baseWidth = {};
        const baseHeight = {};

        for (let i = 0; i < baseFonts.length; i++) {
            const span = document.createElement('span');
            span.style.fontSize = testSize;
            span.style.fontFamily = baseFonts[i];
            span.innerHTML = testString;
            h.appendChild(span);
            baseWidth[baseFonts[i]] = span.offsetWidth;
            baseHeight[baseFonts[i]] = span.offsetHeight;
            h.removeChild(span);
        }

        for (let i = 0; i < fonts.length; i++) {
            let detected = false;
            for (let j = 0; j < baseFonts.length; j++) {
                const span = document.createElement('span');
                span.style.fontSize = testSize;
                span.style.fontFamily = fonts[i] + ',' + baseFonts[j];
                span.innerHTML = testString;
                h.appendChild(span);
                const matched = (span.offsetWidth !== baseWidth[baseFonts[j]] || span.offsetHeight !== baseHeight[baseFonts[j]]);
                h.removeChild(span);
                detected = detected || matched;
            }
            if (detected) {
                availableFonts.push(fonts[i]);
            }
        }

        return availableFonts;
    }

    /**
     * Get browser plugins
     */
    getPlugins() {
        const plugins = [];
        for (let i = 0; i < navigator.plugins.length; i++) {
            plugins.push({
                name: navigator.plugins[i].name,
                description: navigator.plugins[i].description,
                filename: navigator.plugins[i].filename
            });
        }
        return plugins;
    }

    /**
     * Get storage information
     */
    getStorageInfo() {
        return {
            localStorage: typeof(Storage) !== 'undefined',
            sessionStorage: typeof(Storage) !== 'undefined',
            indexedDB: typeof(IndexedDB) !== 'undefined',
            webSQL: typeof(openDatabase) !== 'undefined',
            cookies: navigator.cookieEnabled
        };
    }

    /**
     * Get connection information
     */
    getConnectionInfo() {
        if ('connection' in navigator) {
            const conn = navigator.connection;
            return {
                effectiveType: conn.effectiveType,
                downlink: conn.downlink,
                rtt: conn.rtt,
                saveData: conn.saveData
            };
        }
        return 'connection_not_supported';
    }

    /**
     * Get hardware information
     */
    getHardwareInfo() {
        return {
            cores: navigator.hardwareConcurrency || 'unknown',
            memory: navigator.deviceMemory || 'unknown',
            maxTouchPoints: navigator.maxTouchPoints || 0
        };
    }

    /**
     * Get browser information
     */
    getBrowserInfo() {
        const ua = navigator.userAgent;
        let browser = 'Unknown';
        
        if (ua.indexOf('Chrome') > -1) browser = 'Chrome';
        else if (ua.indexOf('Firefox') > -1) browser = 'Firefox';
        else if (ua.indexOf('Safari') > -1) browser = 'Safari';
        else if (ua.indexOf('Edge') > -1) browser = 'Edge';
        else if (ua.indexOf('Opera') > -1) browser = 'Opera';
        else if (ua.indexOf('MSIE') > -1) browser = 'Internet Explorer';
        
        return {
            name: browser,
            version: this.getBrowserVersion(ua, browser)
        };
    }

    /**
     * Get browser version
     */
    getBrowserVersion(ua, browser) {
        const versionRegex = {
            'Chrome': /Chrome\/(\d+)/,
            'Firefox': /Firefox\/(\d+)/,
            'Safari': /Version\/(\d+)/,
            'Edge': /Edge\/(\d+)/,
            'Opera': /Opera\/(\d+)/,
            'Internet Explorer': /MSIE (\d+)/
        };
        
        const match = ua.match(versionRegex[browser]);
        return match ? match[1] : 'unknown';
    }

    /**
     * Get operating system information
     */
    getOSInfo() {
        const ua = navigator.userAgent;
        let os = 'Unknown';
        
        if (ua.indexOf('Windows') > -1) os = 'Windows';
        else if (ua.indexOf('Mac') > -1) os = 'macOS';
        else if (ua.indexOf('Linux') > -1) os = 'Linux';
        else if (ua.indexOf('Android') > -1) os = 'Android';
        else if (ua.indexOf('iOS') > -1) os = 'iOS';
        
        return {
            name: os,
            version: this.getOSVersion(ua, os)
        };
    }

    /**
     * Get operating system version
     */
    getOSVersion(ua, os) {
        const versionRegex = {
            'Windows': /Windows NT (\d+\.\d+)/,
            'macOS': /Mac OS X (\d+[._]\d+)/,
            'Linux': /Linux/,
            'Android': /Android (\d+\.\d+)/,
            'iOS': /OS (\d+[._]\d+)/
        };
        
        const match = ua.match(versionRegex[os]);
        return match ? match[1] : 'unknown';
    }

    /**
     * Hash fingerprint components
     */
    async hashFingerprint(components) {
        const str = JSON.stringify(components);
        
        if (window.crypto && window.crypto.subtle) {
            const encoder = new TextEncoder();
            const data = encoder.encode(str);
            const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        } else {
            // Fallback to simple hash
            return this.simpleHash(str);
        }
    }

    /**
     * Simple hash function (fallback)
     */
    simpleHash(str) {
        let hash = 0;
        if (str.length === 0) return hash.toString();
        
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        
        return Math.abs(hash).toString(16);
    }

    /**
     * Generate fallback fingerprint
     */
    generateFallbackFingerprint() {
        const fallback = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            timestamp: Date.now()
        };
        
        return this.simpleHash(JSON.stringify(fallback));
    }

    /**
     * Get fingerprint components
     */
    getComponents() {
        return this.components;
    }

    /**
     * Get fingerprint
     */
    getFingerprint() {
        return this.fingerprint;
    }
}

// Global function to get device fingerprint
async function getDeviceFingerprint() {
    const fingerprint = new DeviceFingerprint();
    return await fingerprint.generate();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DeviceFingerprint, getDeviceFingerprint };
}
