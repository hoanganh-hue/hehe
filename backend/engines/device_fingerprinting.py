"""
Device Fingerprinting Engine
Advanced device fingerprinting and browser profiling
"""

import asyncio
import json
import hashlib
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DeviceProfile:
    """Device profile data structure"""
    fingerprint_id: str
    screen_resolution: str
    color_depth: int
    timezone: str
    language: str
    platform: str
    plugins: List[str]
    fonts: List[str]
    canvas_signature: str
    webgl_vendor: str
    webgl_renderer: str
    audio_fingerprint: str
    webrtc_ips: List[str]
    user_agent: str
    created_at: datetime

class DeviceFingerprintEngine:
    """Advanced device fingerprinting engine"""
    
    def __init__(self):
        self.regional_profiles = RegionalProfileManager()
        self.fingerprint_cache = {}
        
    async def generate_vietnamese_profile(self) -> DeviceProfile:
        """Generate realistic Vietnamese device profile"""
        
        # Vietnamese market characteristics
        vietnamese_characteristics = {
            'browsers': {
                'chrome': 0.68,    # 68% Chrome usage in Vietnam
                'edge': 0.15,      # 15% Edge usage
                'firefox': 0.12,   # 12% Firefox usage
                'safari': 0.05     # 5% Safari usage (Mac users)
            },
            'screen_resolutions': {
                '1366x768': 0.35,  # Most common laptop resolution
                '1920x1080': 0.40, # Standard FHD
                '1440x900': 0.15,  # MacBook Pro
                '1280x720': 0.10   # Lower-end devices
            },
            'operating_systems': {
                'Windows 10': 0.55,
                'Windows 11': 0.25,
                'macOS': 0.15,
                'Linux': 0.05
            },
            'timezones': {
                'Asia/Ho_Chi_Minh': 0.95,
                'Asia/Bangkok': 0.03,
                'Asia/Singapore': 0.02
            },
            'languages': {
                'vi-VN,vi;q=0.9,en;q=0.8': 0.70,
                'vi-VN': 0.20,
                'en-US,en;q=0.9,vi;q=0.8': 0.10
            }
        }
        
        # Generate profile based on Vietnamese characteristics
        browser = self.weighted_random_selection(vietnamese_characteristics['browsers'])
        screen_res = self.weighted_random_selection(vietnamese_characteristics['screen_resolutions'])
        os = self.weighted_random_selection(vietnamese_characteristics['operating_systems'])
        timezone = self.weighted_random_selection(vietnamese_characteristics['timezones'])
        language = self.weighted_random_selection(vietnamese_characteristics['languages'])
        
        # Generate device profile
        profile = DeviceProfile(
            fingerprint_id=self.generate_fingerprint_id(),
            screen_resolution=screen_res,
            color_depth=24,
            timezone=timezone,
            language=language,
            platform=self.get_platform_from_os(os),
            plugins=self.generate_realistic_plugins(browser),
            fonts=self.generate_vietnamese_fonts(),
            canvas_signature=self.generate_canvas_signature(),
            webgl_vendor=self.generate_webgl_vendor(),
            webgl_renderer=self.generate_webgl_renderer(),
            audio_fingerprint=self.generate_audio_fingerprint(),
            webrtc_ips=self.generate_webrtc_ips(),
            user_agent=self.generate_user_agent(browser, os),
            created_at=datetime.now(timezone.utc)
        )
        
        return profile
    
    def generate_fingerprint_id(self) -> str:
        """Generate unique fingerprint ID"""
        timestamp = str(int(datetime.now().timestamp() * 1000))
        random_data = str(random.randint(100000, 999999))
        combined = f"{timestamp}_{random_data}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def weighted_random_selection(self, choices: Dict[str, float]) -> str:
        """Select item based on weighted probabilities"""
        rand = random.random()
        cumulative = 0.0
        
        for choice, weight in choices.items():
            cumulative += weight
            if rand <= cumulative:
                return choice
        
        return list(choices.keys())[-1]
    
    def get_platform_from_os(self, os: str) -> str:
        """Get platform string from OS"""
        if 'Windows' in os:
            return 'Win32'
        elif 'macOS' in os:
            return 'MacIntel'
        elif 'Linux' in os:
            return 'Linux x86_64'
        return 'Win32'
    
    def generate_realistic_plugins(self, browser: str) -> List[str]:
        """Generate realistic browser plugins based on browser type"""
        base_plugins = [
            'Chrome PDF Plugin',
            'Widevine Content Decryption Module',
            'Native Client'
        ]
        
        if browser == 'chrome':
            base_plugins.extend([
                'Chrome PDF Viewer',
                'Chromium PDF Viewer',
                'Microsoft Edge PDF Viewer',
                'WebKit built-in PDF'
            ])
        elif browser == 'firefox':
            base_plugins.extend([
                'Firefox PDF Plugin',
                'OpenH264 Video Codec',
                'Widevine Content Decryption Module'
            ])
        elif browser == 'safari':
            base_plugins.extend([
                'Safari PDF Plugin',
                'WebKit built-in PDF'
            ])
        
        return base_plugins
    
    def generate_vietnamese_fonts(self) -> List[str]:
        """Generate realistic Vietnamese font list"""
        vietnamese_fonts = [
            'Arial',
            'Times New Roman',
            'Helvetica',
            'Calibri',
            'Tahoma',
            'Verdana',
            'Georgia',
            'Trebuchet MS',
            'Arial Unicode MS',
            'Lucida Grande',
            'Segoe UI',
            'Microsoft YaHei',
            'SimSun',
            'SimHei'
        ]
        
        # Randomly select 8-12 fonts
        num_fonts = random.randint(8, 12)
        return random.sample(vietnamese_fonts, num_fonts)
    
    def generate_canvas_signature(self) -> str:
        """Generate unique canvas signature"""
        # Simulate canvas fingerprinting
        canvas_data = f"canvas_{random.randint(100000, 999999)}_{random.randint(100000, 999999)}"
        return hashlib.sha256(canvas_data.encode()).hexdigest()[:32]
    
    def generate_webgl_vendor(self) -> str:
        """Generate realistic WebGL vendor"""
        vendors = [
            'Intel Inc.',
            'NVIDIA Corporation',
            'AMD',
            'Apple Inc.',
            'Microsoft Corporation'
        ]
        return random.choice(vendors)
    
    def generate_webgl_renderer(self) -> str:
        """Generate realistic WebGL renderer"""
        renderers = [
            'Intel(R) HD Graphics 620',
            'Intel(R) UHD Graphics 630',
            'NVIDIA GeForce GTX 1060',
            'AMD Radeon RX 580',
            'Apple M1',
            'Intel(R) Iris(R) Graphics 6100'
        ]
        return random.choice(renderers)
    
    def generate_audio_fingerprint(self) -> str:
        """Generate audio context fingerprint"""
        sample_rate = random.choice([44100, 48000])
        channels = random.choice([2, 6, 8])
        sample_size = random.choice([16, 24, 32])
        random_value = random.uniform(0.1, 0.9)
        
        return f"{sample_rate}:{channels}:f{sample_size}:{random_value:.10f}"
    
    def generate_webrtc_ips(self) -> List[str]:
        """Generate realistic WebRTC IP addresses"""
        # Simulate Vietnamese IP ranges
        vietnamese_ips = [
            '192.168.1.100',
            '10.0.0.150',
            '172.16.0.50',
            '203.162.4.191',  # Vietnam IP range
            '14.169.0.1'      # Vietnam IP range
        ]
        
        return random.sample(vietnamese_ips, random.randint(2, 4))
    
    def generate_user_agent(self, browser: str, os: str) -> str:
        """Generate realistic user agent string"""
        if browser == 'chrome' and 'Windows' in os:
            chrome_version = f"{random.randint(115, 120)}.0.{random.randint(0, 9999)}.0"
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
        
        elif browser == 'chrome' and 'macOS' in os:
            chrome_version = f"{random.randint(115, 120)}.0.{random.randint(0, 9999)}.0"
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
        
        elif browser == 'firefox' and 'Windows' in os:
            firefox_version = f"{random.randint(115, 120)}.0"
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}"
        
        elif browser == 'safari' and 'macOS' in os:
            safari_version = f"{random.randint(15, 17)}.0"
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version} Safari/605.1.15"
        
        # Default Chrome on Windows
        chrome_version = f"{random.randint(115, 120)}.0.{random.randint(0, 9999)}.0"
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
    
    async def apply_fingerprint_to_session(self, profile: DeviceProfile, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply device fingerprint to session data"""
        
        session_data.update({
            'device_fingerprint': {
                'fingerprint_id': profile.fingerprint_id,
                'screen_resolution': profile.screen_resolution,
                'color_depth': profile.color_depth,
                'timezone': profile.timezone,
                'language': profile.language,
                'platform': profile.platform,
                'plugins': profile.plugins,
                'fonts': profile.fonts,
                'canvas_signature': profile.canvas_signature,
                'webgl_vendor': profile.webgl_vendor,
                'webgl_renderer': profile.webgl_renderer,
                'audio_fingerprint': profile.audio_fingerprint,
                'webrtc_ips': profile.webrtc_ips
            },
            'user_agent': profile.user_agent,
            'fingerprint_applied_at': profile.created_at.isoformat()
        })
        
        return session_data
    
    async def detect_fingerprint_anomalies(self, profile: DeviceProfile) -> List[str]:
        """Detect potential fingerprint anomalies"""
        anomalies = []
        
        # Check for suspicious plugin combinations
        suspicious_plugins = ['Chrome PDF Plugin', 'Widevine Content Decryption Module']
        if all(plugin in profile.plugins for plugin in suspicious_plugins):
            if len(profile.plugins) < 5:  # Too few plugins
                anomalies.append("Suspicious plugin combination")
        
        # Check for unrealistic screen resolution
        width, height = map(int, profile.screen_resolution.split('x'))
        if width < 800 or height < 600:
            anomalies.append("Unrealistic screen resolution")
        
        # Check for suspicious timezone
        if profile.timezone not in ['Asia/Ho_Chi_Minh', 'Asia/Bangkok', 'Asia/Singapore']:
            anomalies.append("Suspicious timezone for Vietnamese user")
        
        # Check for suspicious language settings
        if 'vi' not in profile.language.lower():
            anomalies.append("No Vietnamese language preference")
        
        return anomalies
    
    async def generate_stealth_profile(self) -> DeviceProfile:
        """Generate stealth profile to avoid detection"""
        
        # Use most common characteristics to blend in
        stealth_profile = DeviceProfile(
            fingerprint_id=self.generate_fingerprint_id(),
            screen_resolution='1920x1080',  # Most common
            color_depth=24,
            timezone='Asia/Ho_Chi_Minh',
            language='vi-VN,vi;q=0.9,en;q=0.8',
            platform='Win32',
            plugins=[
                'Chrome PDF Plugin',
                'Widevine Content Decryption Module',
                'Native Client',
                'Chrome PDF Viewer',
                'Chromium PDF Viewer'
            ],
            fonts=[
                'Arial', 'Times New Roman', 'Helvetica', 'Calibri', 'Tahoma',
                'Verdana', 'Georgia', 'Trebuchet MS', 'Arial Unicode MS'
            ],
            canvas_signature=self.generate_canvas_signature(),
            webgl_vendor='Intel Inc.',
            webgl_renderer='Intel(R) HD Graphics 620',
            audio_fingerprint=self.generate_audio_fingerprint(),
            webrtc_ips=['192.168.1.100', '10.0.0.150'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            created_at=datetime.now(timezone.utc)
        )
        
        return stealth_profile

class RegionalProfileManager:
    """Manager for regional device profiles"""
    
    def __init__(self):
        self.regional_data = {
            'vietnam': {
                'common_resolutions': ['1920x1080', '1366x768', '1440x900'],
                'common_browsers': ['chrome', 'edge', 'firefox'],
                'common_os': ['Windows 10', 'Windows 11', 'macOS'],
                'timezone': 'Asia/Ho_Chi_Minh',
                'language': 'vi-VN'
            },
            'thailand': {
                'common_resolutions': ['1920x1080', '1366x768'],
                'common_browsers': ['chrome', 'edge'],
                'common_os': ['Windows 10', 'Windows 11'],
                'timezone': 'Asia/Bangkok',
                'language': 'th-TH'
            },
            'singapore': {
                'common_resolutions': ['1920x1080', '1440x900'],
                'common_browsers': ['chrome', 'safari'],
                'common_os': ['Windows 10', 'macOS'],
                'timezone': 'Asia/Singapore',
                'language': 'en-SG'
            }
        }
    
    def get_regional_profile(self, region: str) -> Dict[str, Any]:
        """Get regional profile data"""
        return self.regional_data.get(region, self.regional_data['vietnam'])
    
    def get_common_characteristics(self, region: str) -> Dict[str, List[str]]:
        """Get common characteristics for region"""
        profile = self.get_regional_profile(region)
        return {
            'resolutions': profile['common_resolutions'],
            'browsers': profile['common_browsers'],
            'os': profile['common_os']
        }