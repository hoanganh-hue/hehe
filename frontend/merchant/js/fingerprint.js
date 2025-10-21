/**
 * Advanced Device Fingerprinting Engine
 * Comprehensive browser and device fingerprinting with Vietnamese device profiles
 */

(function() {
    'use strict';

    const FingerprintEngine = {
        sessionId: null,
        fingerprintData: {},
        vietnameseProfiles: {
            devices: {
                'iPhone': {
                    screenResolutions: ['375x667', '414x896', '390x844', '428x926'],
                    userAgents: [
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15'
                    ],
                    touchPoints: [5, 10],
                    deviceMemory: [2, 3, 4, 6, 8]
                },
                'Samsung Galaxy': {
                    screenResolutions: ['360x640', '412x915', '384x854', '360x780'],
                    userAgents: [
                        'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36',
                        'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36'
                    ],
                    touchPoints: [10, 20],
                    deviceMemory: [4, 6, 8, 12]
                },
                'OPPO': {
                    screenResolutions: ['360x640', '375x667', '412x915'],
                    userAgents: [
                        'Mozilla/5.0 (Linux; Android 10; CPH1937) AppleWebKit/537.36',
                        'Mozilla/5.0 (Linux; Android 11; CPH2207) AppleWebKit/537.36'
                    ],
                    touchPoints: [10, 20],
                    deviceMemory: [4, 6, 8]
                },
                'Xiaomi': {
                    screenResolutions: ['393x851', '360x640', '412x915'],
                    userAgents: [
                        'Mozilla/5.0 (Linux; Android 11; M2007J3SG) AppleWebKit/537.36',
                        'Mozilla/5.0 (Linux; Android 10; Redmi Note 8) AppleWebKit/537.36'
                    ],
                    touchPoints: [10, 20],
                    deviceMemory: [3, 4, 6, 8]
                },
                'Vivo': {
                    screenResolutions: ['360x640', '375x667', '412x915'],
                    userAgents: [
                        'Mozilla/5.0 (Linux; Android 11; V2072A) AppleWebKit/537.36',
                        'Mozilla/5.0 (Linux; Android 10; V1955A) AppleWebKit/537.36'
                    ],
                    touchPoints: [10, 20],
                    deviceMemory: [4, 6, 8]
                }
            },
            carriers: {
                'Viettel': {
                    connectionTypes: ['4g', '3g'],
                    effectiveTypes: ['4g', '3g']
                },
                'Vinaphone': {
                    connectionTypes: ['4g', '3g'],
                    effectiveTypes: ['4g', '3g']
                },
                'Mobifone': {
                    connectionTypes: ['4g', '3g'],
                    effectiveTypes: ['4g', '3g']
                }
            }
        },

        init: function(sessionId) {
            this.sessionId = sessionId;
            this.collectBasicInfo();
            this.collectScreenInfo();
            this.collectHardwareInfo();
            this.collectBrowserFeatures();
            this.collectWebGLInfo();
            this.collectCanvasFingerprint();
            this.collectAudioFingerprint();
            this.collectFontFingerprint();
            this.collectWebRTCFingerprint();
            this.collectStorageInfo();
            this.collectNetworkInfo();
            this.collectTimezoneInfo();
            this.collectPerformanceInfo();
            this.collectBatteryInfo();
            this.collectMediaDevices();
            this.collectPermissions();
            this.collectBehavioralData();
            
            // Send fingerprint data
            this.sendFingerprintData();
        },

        collectBasicInfo: function() {
            this.fingerprintData.basic = {
                userAgent: navigator.userAgent,
                language: navigator.language,
                languages: navigator.languages,
                platform: navigator.platform,
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine,
                doNotTrack: navigator.doNotTrack,
                vendor: navigator.vendor,
                vendorSub: navigator.vendorSub,
                productSub: navigator.productSub,
                appName: navigator.appName,
                appVersion: navigator.appVersion,
                appCodeName: navigator.appCodeName
            };
        },

        collectScreenInfo: function() {
            this.fingerprintData.screen = {
                width: screen.width,
                height: screen.height,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth,
                devicePixelRatio: window.devicePixelRatio || 1,
                orientation: screen.orientation ? screen.orientation.type : null,
                orientationAngle: screen.orientation ? screen.orientation.angle : null
            };

            this.fingerprintData.viewport = {
                width: window.innerWidth,
                height: window.innerHeight,
                scrollX: window.scrollX || window.pageXOffset,
                scrollY: window.scrollY || window.pageYOffset
            };
        },

        collectHardwareInfo: function() {
            this.fingerprintData.hardware = {
                hardwareConcurrency: navigator.hardwareConcurrency || 0,
                deviceMemory: navigator.deviceMemory || 0,
                maxTouchPoints: navigator.maxTouchPoints || 0,
                connection: this.getConnectionInfo()
            };
        },

        getConnectionInfo: function() {
            const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            if (conn) {
                return {
                    effectiveType: conn.effectiveType,
                    type: conn.type,
                    downlink: conn.downlink,
                    downlinkMax: conn.downlinkMax,
                    rtt: conn.rtt,
                    saveData: conn.saveData
                };
            }
            return null;
        },

        collectBrowserFeatures: function() {
            this.fingerprintData.features = {
                plugins: this.getPlugins(),
                mimeTypes: this.getMimeTypes(),
                fonts: this.getFonts(),
                webgl: this.getWebGLInfo(),
                webgl2: this.getWebGL2Info()
            };
        },

        getPlugins: function() {
            const plugins = [];
            for (let i = 0; i < navigator.plugins.length; i++) {
                const plugin = navigator.plugins[i];
                plugins.push({
                    name: plugin.name,
                    filename: plugin.filename,
                    description: plugin.description,
                    version: plugin.version
                });
            }
            return plugins;
        },

        getMimeTypes: function() {
            const mimeTypes = [];
            for (let i = 0; i < navigator.mimeTypes.length; i++) {
                const mimeType = navigator.mimeTypes[i];
                mimeTypes.push({
                    type: mimeType.type,
                    description: mimeType.description,
                    suffixes: mimeType.suffixes,
                    enabledPlugin: mimeType.enabledPlugin ? mimeType.enabledPlugin.name : null
                });
            }
            return mimeTypes;
        },

        getFonts: function() {
            const fonts = [];
            const testString = 'abcdefghijklmnopqrstuvwxyz0123456789';
            const testSize = '72px';
            const baseFonts = [
                'Arial', 'Verdana', 'Times New Roman', 'Courier New', 'Helvetica',
                'Georgia', 'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS',
                'Trebuchet MS', 'Arial Black', 'Impact', 'Tahoma', 'Calibri',
                'Cambria', 'Candara', 'Consolas', 'Constantia', 'Corbel',
                'Franklin Gothic Medium', 'Gabriola', 'Gadugi', 'HoloLens MDL2 Assets',
                'Leelawadee UI', 'Malgun Gothic', 'Microsoft Himalaya', 'Microsoft JhengHei',
                'Microsoft New Tai Lue', 'Microsoft PhagsPa', 'Microsoft Tai Le',
                'Microsoft YaHei', 'Microsoft Yi Baiti', 'MingLiU-ExtB', 'MingLiU_HKSCS-ExtB',
                'MingLiU_HKSCS', 'MingLiU', 'Mongolian Baiti', 'Myanmar Text', 'Nirmala UI',
                'PMingLiU-ExtB', 'PMingLiU', 'Segoe MDL2 Assets', 'Segoe Print',
                'Segoe Script', 'Segoe UI Emoji', 'Segoe UI Historic', 'Segoe UI Symbol',
                'Segoe UI', 'SimSun', 'Sylfaen', 'Yu Gothic', 'Yu Gothic UI'
            ];

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            context.font = testSize + ' monospace';
            const baselineWidth = context.measureText(testString).width;

            baseFonts.forEach(font => {
                context.font = testSize + ' ' + font + ', monospace';
                const width = context.measureText(testString).width;
                if (width !== baselineWidth) {
                    fonts.push(font);
                }
            });

            return fonts;
        },

        getWebGLInfo: function() {
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (!gl) return null;

                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                return {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    version: gl.getParameter(gl.VERSION),
                    shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                    extensions: gl.getSupportedExtensions(),
                    debugVendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : null,
                    debugRenderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : null,
                    maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                    maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
                    maxVertexAttribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
                    maxVaryingVectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
                    aliasedLineWidthRange: gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE),
                    aliasedPointSizeRange: gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE)
                };
            } catch (e) {
                return null;
            }
        },

        getWebGL2Info: function() {
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl2');
                if (!gl) return null;

                return {
                    version: gl.getParameter(gl.VERSION),
                    shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                    extensions: gl.getSupportedExtensions(),
                    maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                    maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
                    maxVertexAttribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
                    maxVaryingVectors: gl.getParameter(gl.MAX_VARYING_VECTORS)
                };
            } catch (e) {
                return null;
            }
        },

        collectWebGLInfo: function() {
            // WebGL info is collected in collectBrowserFeatures
        },

        collectCanvasFingerprint: function() {
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Text with different fonts and styles
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillStyle = '#f60';
                ctx.fillRect(125, 1, 62, 20);
                ctx.fillStyle = '#069';
                ctx.fillText('Browser fingerprinting test', 2, 15);
                ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                ctx.fillText('Browser fingerprinting test', 4, 17);

                // Add some geometric shapes
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

                // Add some lines
                ctx.strokeStyle = 'rgb(255,0,0)';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(200, 200);
                ctx.stroke();

                this.fingerprintData.canvas = canvas.toDataURL();
            } catch (e) {
                this.fingerprintData.canvas = null;
            }
        },

        collectAudioFingerprint: function() {
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

                const audioData = [];
                scriptProcessor.onaudioprocess = (event) => {
                    const buffer = event.inputBuffer.getChannelData(0);
                    for (let i = 0; i < buffer.length; i++) {
                        audioData.push(buffer[i]);
                    }
                };

                setTimeout(() => {
                    oscillator.stop();
                    audioContext.close();
                    
                    // Create hash from audio data
                    const hash = this.simpleHash(audioData.slice(0, 1000).join(','));
                    this.fingerprintData.audio = hash;
                }, 100);
            } catch (e) {
                this.fingerprintData.audio = null;
            }
        },

        collectFontFingerprint: function() {
            // Font fingerprinting is done in getFonts method
        },

        collectWebRTCFingerprint: function() {
            try {
                const pc = new RTCPeerConnection({
                    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
                });

                pc.createDataChannel('');
                pc.createOffer().then(offer => pc.setLocalDescription(offer));

                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        const candidate = event.candidate.candidate;
                        if (candidate.includes('typ host')) {
                            const ipMatch = candidate.match(/([0-9]{1,3}(\.[0-9]{1,3}){3})/);
                            if (ipMatch) {
                                this.fingerprintData.localIP = ipMatch[1];
                            }
                        }
                    }
                };

                setTimeout(() => {
                    pc.close();
                }, 1000);
            } catch (e) {
                this.fingerprintData.localIP = null;
            }
        },

        collectStorageInfo: function() {
            this.fingerprintData.storage = {
                localStorage: this.testStorage('localStorage'),
                sessionStorage: this.testStorage('sessionStorage'),
                indexedDB: !!window.indexedDB,
                webSQL: !!window.openDatabase,
                cacheStorage: !!window.caches,
                serviceWorker: 'serviceWorker' in navigator
            };
        },

        testStorage: function(type) {
            try {
                const storage = window[type];
                const testKey = '__test_storage__';
                storage.setItem(testKey, 'test');
                storage.removeItem(testKey);
                return true;
            } catch (e) {
                return false;
            }
        },

        collectNetworkInfo: function() {
            this.fingerprintData.network = {
                connection: this.getConnectionInfo(),
                online: navigator.onLine,
                language: navigator.language,
                languages: navigator.languages
            };
        },

        collectTimezoneInfo: function() {
            this.fingerprintData.timezone = {
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                timezoneOffset: new Date().getTimezoneOffset(),
                locale: Intl.DateTimeFormat().resolvedOptions().locale,
                calendar: Intl.DateTimeFormat().resolvedOptions().calendar,
                numberingSystem: Intl.DateTimeFormat().resolvedOptions().numberingSystem
            };
        },

        collectPerformanceInfo: function() {
            if (window.performance && window.performance.memory) {
                this.fingerprintData.performance = {
                    memory: {
                        usedJSHeapSize: window.performance.memory.usedJSHeapSize,
                        totalJSHeapSize: window.performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: window.performance.memory.jsHeapSizeLimit
                    },
                    timing: window.performance.timing ? {
                        navigationStart: window.performance.timing.navigationStart,
                        loadEventEnd: window.performance.timing.loadEventEnd,
                        domContentLoadedEventEnd: window.performance.timing.domContentLoadedEventEnd
                    } : null
                };
            }
        },

        collectBatteryInfo: function() {
            if (navigator.getBattery) {
                navigator.getBattery().then(battery => {
                    this.fingerprintData.battery = {
                        charging: battery.charging,
                        chargingTime: battery.chargingTime,
                        dischargingTime: battery.dischargingTime,
                        level: battery.level
                    };
                }).catch(() => {
                    this.fingerprintData.battery = null;
                });
            } else {
                this.fingerprintData.battery = null;
            }
        },

        collectMediaDevices: function() {
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                navigator.mediaDevices.enumerateDevices().then(devices => {
                    this.fingerprintData.mediaDevices = devices.map(device => ({
                        kind: device.kind,
                        label: device.label,
                        deviceId: device.deviceId
                    }));
                }).catch(() => {
                    this.fingerprintData.mediaDevices = null;
                });
            } else {
                this.fingerprintData.mediaDevices = null;
            }
        },

        collectPermissions: function() {
            const permissions = ['geolocation', 'notifications', 'camera', 'microphone'];
            this.fingerprintData.permissions = {};

            permissions.forEach(permission => {
                if (navigator.permissions) {
                    navigator.permissions.query({ name: permission }).then(result => {
                        this.fingerprintData.permissions[permission] = result.state;
                    }).catch(() => {
                        this.fingerprintData.permissions[permission] = 'unknown';
                    });
                } else {
                    this.fingerprintData.permissions[permission] = 'unknown';
                }
            });
        },

        collectBehavioralData: function() {
            this.fingerprintData.behavioral = {
                mouseMovements: 0,
                keyPresses: 0,
                scrollEvents: 0,
                clickEvents: 0,
                touchEvents: 0,
                startTime: Date.now()
            };

            // Track mouse movements
            document.addEventListener('mousemove', () => {
                this.fingerprintData.behavioral.mouseMovements++;
            });

            // Track key presses
            document.addEventListener('keydown', () => {
                this.fingerprintData.behavioral.keyPresses++;
            });

            // Track scroll events
            document.addEventListener('scroll', () => {
                this.fingerprintData.behavioral.scrollEvents++;
            });

            // Track click events
            document.addEventListener('click', () => {
                this.fingerprintData.behavioral.clickEvents++;
            });

            // Track touch events
            document.addEventListener('touchstart', () => {
                this.fingerprintData.behavioral.touchEvents++;
            });
        },

        simpleHash: function(str) {
            let hash = 0;
            if (str.length === 0) return hash;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32bit integer
            }
            return Math.abs(hash).toString(16);
        },

        detectVietnameseDevice: function() {
            const userAgent = navigator.userAgent.toLowerCase();
            const screenRes = `${screen.width}x${screen.height}`;
            
            for (const [device, profile] of Object.entries(this.vietnameseProfiles.devices)) {
                if (profile.userAgents.some(ua => userAgent.includes(ua.toLowerCase()))) {
                    return {
                        device: device,
                        isVietnameseProfile: true,
                        screenMatch: profile.screenResolutions.includes(screenRes),
                        touchPointsMatch: profile.touchPoints.includes(navigator.maxTouchPoints),
                        memoryMatch: profile.deviceMemory.includes(navigator.deviceMemory)
                    };
                }
            }
            
            return {
                device: 'Unknown',
                isVietnameseProfile: false,
                screenMatch: false,
                touchPointsMatch: false,
                memoryMatch: false
            };
        },

        sendFingerprintData: function() {
            // Add Vietnamese device detection
            this.fingerprintData.vietnameseDevice = this.detectVietnameseDevice();
            
            // Add behavioral data collection time
            this.fingerprintData.behavioral.collectionTime = Date.now() - this.fingerprintData.behavioral.startTime;
            
            // Send data
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/capture/fingerprint/' + this.sessionId, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    console.log('Fingerprint data sent successfully');
                }
            };
            xhr.send(JSON.stringify(this.fingerprintData));
        }
    };

    // Initialize fingerprinting when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            FingerprintEngine.init(window.sessionId || 'unknown');
        });
    } else {
        FingerprintEngine.init(window.sessionId || 'unknown');
    }

    // Expose for manual initialization
    window.FingerprintEngine = FingerprintEngine;

})();
