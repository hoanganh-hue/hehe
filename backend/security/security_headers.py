"""
Security Headers Implementation
Provides security headers for HTTP responses
"""

from typing import Dict, List, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class SecurityHeaders:
    """
    Manages security headers for HTTP responses
    """
    
    def __init__(self):
        """
        Initialize security headers manager
        """
        self.default_headers = {
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # HTTP Strict Transport Security
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # X-Content-Type-Options
            "X-Content-Type-Options": "nosniff",
            
            # X-Frame-Options
            "X-Frame-Options": "DENY",
            
            # X-XSS-Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=(), "
                "vibrate=(), "
                "fullscreen=(self), "
                "sync-xhr=()"
            ),
            
            # Cross-Origin Embedder Policy
            "Cross-Origin-Embedder-Policy": "require-corp",
            
            # Cross-Origin Opener Policy
            "Cross-Origin-Opener-Policy": "same-origin",
            
            # Cross-Origin Resource Policy
            "Cross-Origin-Resource-Policy": "same-origin",
            
            # Cache Control
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Server
            "Server": "ZaloPay-Phishing-Platform",
            
            # X-Powered-By (remove)
            "X-Powered-By": "",
            
            # X-DNS-Prefetch-Control
            "X-DNS-Prefetch-Control": "off",
            
            # X-Download-Options
            "X-Download-Options": "noopen",
            
            # X-Permitted-Cross-Domain-Policies
            "X-Permitted-Cross-Domain-Policies": "none"
        }
        
        # Admin-specific headers
        self.admin_headers = {
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block"
        }
        
        # Merchant-specific headers (more permissive for OAuth)
        self.merchant_headers = {
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://appleid.apple.com https://www.facebook.com; "
                "style-src 'self' 'unsafe-inline' https://accounts.google.com https://appleid.apple.com https://www.facebook.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
                "connect-src 'self' https://accounts.google.com https://appleid.apple.com https://www.facebook.com; "
                "frame-src 'self' https://accounts.google.com https://appleid.apple.com https://www.facebook.com; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self' https://accounts.google.com https://appleid.apple.com https://www.facebook.com"
            ),
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block"
        }
        
        # API-specific headers
        self.api_headers = {
            "Content-Security-Policy": "default-src 'none'",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    
    def get_headers(self, request_type: str = "default") -> Dict[str, str]:
        """
        Get security headers for request type
        
        Args:
            request_type: Type of request (default, admin, merchant, api)
            
        Returns:
            Dictionary of security headers
        """
        try:
            if request_type == "admin":
                return {**self.default_headers, **self.admin_headers}
            elif request_type == "merchant":
                return {**self.default_headers, **self.merchant_headers}
            elif request_type == "api":
                return {**self.default_headers, **self.api_headers}
            else:
                return self.default_headers.copy()
                
        except Exception as e:
            logger.error(f"Error getting security headers: {e}")
            return self.default_headers.copy()
    
    def add_headers_to_response(self, response: Response, request_type: str = "default") -> Response:
        """
        Add security headers to response
        
        Args:
            response: FastAPI response object
            request_type: Type of request
            
        Returns:
            Response with security headers
        """
        try:
            headers = self.get_headers(request_type)
            
            for header_name, header_value in headers.items():
                if header_value:  # Only add non-empty headers
                    response.headers[header_name] = header_value
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding security headers: {e}")
            return response
    
    def get_csp_header(self, request_type: str = "default") -> str:
        """
        Get Content Security Policy header
        
        Args:
            request_type: Type of request
            
        Returns:
            CSP header value
        """
        try:
            headers = self.get_headers(request_type)
            return headers.get("Content-Security-Policy", "")
        except Exception as e:
            logger.error(f"Error getting CSP header: {e}")
            return ""
    
    def get_hsts_header(self) -> str:
        """
        Get HTTP Strict Transport Security header
        
        Returns:
            HSTS header value
        """
        try:
            return self.default_headers.get("Strict-Transport-Security", "")
        except Exception as e:
            logger.error(f"Error getting HSTS header: {e}")
            return ""
    
    def get_permissions_policy_header(self) -> str:
        """
        Get Permissions Policy header
        
        Returns:
            Permissions Policy header value
        """
        try:
            return self.default_headers.get("Permissions-Policy", "")
        except Exception as e:
            logger.error(f"Error getting Permissions Policy header: {e}")
            return ""
    
    def create_secure_response(self, content: any, status_code: int = 200, request_type: str = "default") -> JSONResponse:
        """
        Create a secure JSON response
        
        Args:
            content: Response content
            status_code: HTTP status code
            request_type: Type of request
            
        Returns:
            Secure JSON response
        """
        try:
            response = JSONResponse(content=content, status_code=status_code)
            return self.add_headers_to_response(response, request_type)
            
        except Exception as e:
            logger.error(f"Error creating secure response: {e}")
            return JSONResponse(content={"error": "Internal server error"}, status_code=500)
    
    def get_cors_headers(self, origin: Optional[str] = None) -> Dict[str, str]:
        """
        Get CORS headers
        
        Args:
            origin: Allowed origin
            
        Returns:
            Dictionary of CORS headers
        """
        try:
            cors_headers = {
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Max-Age": "86400",
                "Access-Control-Allow-Credentials": "true"
            }
            
            if origin:
                cors_headers["Access-Control-Allow-Origin"] = origin
            else:
                cors_headers["Access-Control-Allow-Origin"] = "*"
            
            return cors_headers
            
        except Exception as e:
            logger.error(f"Error getting CORS headers: {e}")
            return {}
    
    def add_cors_headers(self, response: Response, origin: Optional[str] = None) -> Response:
        """
        Add CORS headers to response
        
        Args:
            response: FastAPI response object
            origin: Allowed origin
            
        Returns:
            Response with CORS headers
        """
        try:
            cors_headers = self.get_cors_headers(origin)
            
            for header_name, header_value in cors_headers.items():
                response.headers[header_name] = header_value
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding CORS headers: {e}")
            return response
    
    def get_security_headers_summary(self) -> Dict[str, Dict[str, str]]:
        """
        Get summary of all security headers
        
        Returns:
            Dictionary of security headers by type
        """
        try:
            return {
                "default": self.get_headers("default"),
                "admin": self.get_headers("admin"),
                "merchant": self.get_headers("merchant"),
                "api": self.get_headers("api")
            }
        except Exception as e:
            logger.error(f"Error getting security headers summary: {e}")
            return {}
    
    def validate_security_headers(self, headers: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate security headers
        
        Args:
            headers: Headers to validate
            
        Returns:
            Dictionary of validation results
        """
        try:
            validation_results = {
                "missing": [],
                "weak": [],
                "recommended": []
            }
            
            # Required headers
            required_headers = [
                "Content-Security-Policy",
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Strict-Transport-Security"
            ]
            
            for header in required_headers:
                if header not in headers:
                    validation_results["missing"].append(header)
            
            # Check for weak configurations
            if headers.get("X-Frame-Options") == "ALLOWALL":
                validation_results["weak"].append("X-Frame-Options should not be ALLOWALL")
            
            if headers.get("X-Content-Type-Options") != "nosniff":
                validation_results["weak"].append("X-Content-Type-Options should be nosniff")
            
            if "Strict-Transport-Security" not in headers:
                validation_results["recommended"].append("Consider adding Strict-Transport-Security header")
            
            if "Referrer-Policy" not in headers:
                validation_results["recommended"].append("Consider adding Referrer-Policy header")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating security headers: {e}")
            return {"error": [str(e)]}

# Global security headers instance
security_headers: SecurityHeaders = SecurityHeaders()

def get_security_headers() -> SecurityHeaders:
    """Get the global security headers instance"""
    return security_headers

def add_security_headers(response: Response, request_type: str = "default") -> Response:
    """Add security headers to response"""
    return security_headers.add_headers_to_response(response, request_type)

def create_secure_response(content: any, status_code: int = 200, request_type: str = "default") -> JSONResponse:
    """Create a secure JSON response"""
    return security_headers.create_secure_response(content, status_code, request_type)

def get_csp_header(request_type: str = "default") -> str:
    """Get Content Security Policy header"""
    return security_headers.get_csp_header(request_type)

def get_hsts_header() -> str:
    """Get HTTP Strict Transport Security header"""
    return security_headers.get_hsts_header()

def get_permissions_policy_header() -> str:
    """Get Permissions Policy header"""
    return security_headers.get_permissions_policy_header()

def add_cors_headers(response: Response, origin: Optional[str] = None) -> Response:
    """Add CORS headers to response"""
    return security_headers.add_cors_headers(response, origin)

def validate_security_headers(headers: Dict[str, str]) -> Dict[str, List[str]]:
    """Validate security headers"""
    return security_headers.validate_security_headers(headers)
