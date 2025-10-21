"""
Advanced Fingerprint Analyzer
Vietnamese device profile matching and advanced fingerprint analysis
"""

import os
import json
import hashlib
import secrets
import time
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import re
import statistics
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class VietnameseDeviceProfile:
    """Vietnamese device profile definitions"""
    
    DEVICE_PROFILES = {
        'iPhone': {
            'screen_resolutions': ['375x667', '414x896', '390x844', '428x926', '393x852'],
            'user_agent_patterns': [
                r'iPhone.*OS (\d+)_(\d+)',
                r'iPhone.*Mobile'
            ],
            'touch_points': [5, 10],
            'device_memory': [2, 3, 4, 6, 8],
            'hardware_concurrency': [2, 4, 6],
            'webgl_vendors': ['Apple Inc.', 'Apple'],
            'webgl_renderers': ['Apple GPU', 'Apple A14 GPU', 'Apple A15 GPU'],
            'popularity_score': 0.9,
            'market_share': 0.25
        },
        'Samsung Galaxy': {
            'screen_resolutions': ['360x640', '412x915', '384x854', '360x780', '414x896'],
            'user_agent_patterns': [
                r'SM-G\d+',
                r'Galaxy.*Mobile',
                r'Samsung.*Android'
            ],
            'touch_points': [10, 20],
            'device_memory': [4, 6, 8, 12],
            'hardware_concurrency': [4, 6, 8],
            'webgl_vendors': ['Google Inc.', 'Qualcomm'],
            'webgl_renderers': ['Adreno', 'Mali', 'PowerVR'],
            'popularity_score': 0.85,
            'market_share': 0.30
        },
        'OPPO': {
            'screen_resolutions': ['360x640', '375x667', '412x915', '393x851'],
            'user_agent_patterns': [
                r'CPH\d+',
                r'OPPO.*Mobile',
                r'OPPO.*Android'
            ],
            'touch_points': [10, 20],
            'device_memory': [4, 6, 8],
            'hardware_concurrency': [4, 6, 8],
            'webgl_vendors': ['Google Inc.', 'Qualcomm'],
            'webgl_renderers': ['Adreno', 'Mali'],
            'popularity_score': 0.75,
            'market_share': 0.15
        },
        'Xiaomi': {
            'screen_resolutions': ['393x851', '360x640', '412x915', '375x667'],
            'user_agent_patterns': [
                r'M\d+',
                r'Redmi.*Mobile',
                r'Mi.*Mobile',
                r'Xiaomi.*Android'
            ],
            'touch_points': [10, 20],
            'device_memory': [3, 4, 6, 8],
            'hardware_concurrency': [4, 6, 8],
            'webgl_vendors': ['Google Inc.', 'Qualcomm'],
            'webgl_renderers': ['Adreno', 'Mali'],
            'popularity_score': 0.80,
            'market_share': 0.20
        },
        'Vivo': {
            'screen_resolutions': ['360x640', '375x667', '412x915', '393x851'],
            'user_agent_patterns': [
                r'V\d+',
                r'Vivo.*Mobile',
                r'Vivo.*Android'
            ],
            'touch_points': [10, 20],
            'device_memory': [4, 6, 8],
            'hardware_concurrency': [4, 6, 8],
            'webgl_vendors': ['Google Inc.', 'Qualcomm'],
            'webgl_renderers': ['Adreno', 'Mali'],
            'popularity_score': 0.70,
            'market_share': 0.10
        },
        'Desktop': {
            'screen_resolutions': ['1920x1080', '1366x768', '1440x900', '1536x864', '1280x720'],
            'user_agent_patterns': [
                r'Windows NT',
                r'Macintosh',
                r'Linux',
                r'X11'
            ],
            'touch_points': [0],
            'device_memory': [8, 16, 32],
            'hardware_concurrency': [4, 6, 8, 12, 16],
            'webgl_vendors': ['Google Inc.', 'NVIDIA', 'AMD', 'Intel'],
            'webgl_renderers': ['NVIDIA', 'AMD', 'Intel', 'ANGLE'],
            'popularity_score': 0.60,
            'market_share': 0.05
        }
    }
    
    CARRIER_PROFILES = {
        'Viettel': {
            'connection_types': ['4g', '3g'],
            'effective_types': ['4g', '3g'],
            'rtt_ranges': [50, 200],
            'downlink_ranges': [1, 10],
            'market_share': 0.45
        },
        'Vinaphone': {
            'connection_types': ['4g', '3g'],
            'effective_types': ['4g', '3g'],
            'rtt_ranges': [60, 250],
            'downlink_ranges': [1, 8],
            'market_share': 0.30
        },
        'Mobifone': {
            'connection_types': ['4g', '3g'],
            'effective_types': ['4g', '3g'],
            'rtt_ranges': [70, 300],
            'downlink_ranges': [1, 6],
            'market_share': 0.25
        }
    }

class FingerprintAnalyzer:
    """Advanced fingerprint analysis engine"""
    
    def __init__(self):
        self.vietnamese_profiles = VietnameseDeviceProfile()
        self.analysis_cache = {}
        self.device_statistics = defaultdict(list)
        
    def analyze_fingerprint(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive fingerprint analysis
        
        Args:
            fingerprint_data: Raw fingerprint data from client
            
        Returns:
            Analysis results with device detection, risk assessment, etc.
        """
        try:
            analysis = {
                'device_detection': self._detect_device_type(fingerprint_data),
                'vietnamese_profile_match': self._match_vietnamese_profile(fingerprint_data),
                'risk_assessment': self._assess_risk(fingerprint_data),
                'consistency_check': self._check_consistency(fingerprint_data),
                'behavioral_analysis': self._analyze_behavior(fingerprint_data),
                'uniqueness_score': self._calculate_uniqueness(fingerprint_data),
                'bot_probability': self._calculate_bot_probability(fingerprint_data),
                'confidence_score': 0.0,
                'recommendations': []
            }
            
            # Calculate overall confidence score
            analysis['confidence_score'] = self._calculate_confidence_score(analysis)
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing fingerprint: {e}")
            return self._get_default_analysis()
    
    def _detect_device_type(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect device type based on fingerprint data"""
        try:
            user_agent = fingerprint_data.get('basic', {}).get('userAgent', '').lower()
            screen_width = fingerprint_data.get('screen', {}).get('width', 0)
            screen_height = fingerprint_data.get('screen', {}).get('height', 0)
            max_touch_points = fingerprint_data.get('hardware', {}).get('maxTouchPoints', 0)
            
            device_type = 'Unknown'
            confidence = 0.0
            
            # Check against known device profiles
            for device_name, profile in self.vietnamese_profiles.DEVICE_PROFILES.items():
                device_confidence = 0.0
                
                # Check user agent patterns
                for pattern in profile['user_agent_patterns']:
                    if re.search(pattern, user_agent, re.IGNORECASE):
                        device_confidence += 0.4
                
                # Check screen resolution
                screen_res = f"{screen_width}x{screen_height}"
                if screen_res in profile['screen_resolutions']:
                    device_confidence += 0.3
                
                # Check touch points
                if max_touch_points in profile['touch_points']:
                    device_confidence += 0.2
                
                # Check hardware concurrency
                hw_concurrency = fingerprint_data.get('hardware', {}).get('hardwareConcurrency', 0)
                if hw_concurrency in profile['hardware_concurrency']:
                    device_confidence += 0.1
                
                if device_confidence > confidence:
                    confidence = device_confidence
                    device_type = device_name
            
            return {
                'device_type': device_type,
                'confidence': confidence,
                'screen_resolution': f"{screen_width}x{screen_height}",
                'is_mobile': max_touch_points > 0 or 'mobile' in user_agent,
                'is_desktop': max_touch_points == 0 and 'mobile' not in user_agent
            }
            
        except Exception as e:
            logger.error(f"Error detecting device type: {e}")
            return {'device_type': 'Unknown', 'confidence': 0.0}
    
    def _match_vietnamese_profile(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match fingerprint against Vietnamese device profiles"""
        try:
            device_detection = self._detect_device_type(fingerprint_data)
            device_type = device_detection['device_type']
            
            if device_type not in self.vietnamese_profiles.DEVICE_PROFILES:
                return {
                    'is_vietnamese_profile': False,
                    'match_score': 0.0,
                    'profile_details': None
                }
            
            profile = self.vietnamese_profiles.DEVICE_PROFILES[device_type]
            match_score = 0.0
            match_details = {}
            
            # Screen resolution match
            screen_width = fingerprint_data.get('screen', {}).get('width', 0)
            screen_height = fingerprint_data.get('screen', {}).get('height', 0)
            screen_res = f"{screen_width}x{screen_height}"
            
            if screen_res in profile['screen_resolutions']:
                match_score += 0.3
                match_details['screen_match'] = True
            else:
                match_details['screen_match'] = False
            
            # Touch points match
            max_touch_points = fingerprint_data.get('hardware', {}).get('maxTouchPoints', 0)
            if max_touch_points in profile['touch_points']:
                match_score += 0.2
                match_details['touch_match'] = True
            else:
                match_details['touch_match'] = False
            
            # Device memory match
            device_memory = fingerprint_data.get('hardware', {}).get('deviceMemory', 0)
            if device_memory in profile['device_memory']:
                match_score += 0.2
                match_details['memory_match'] = True
            else:
                match_details['memory_match'] = False
            
            # WebGL vendor match
            webgl_vendor = fingerprint_data.get('features', {}).get('webgl', {}).get('vendor', '')
            if webgl_vendor in profile['webgl_vendors']:
                match_score += 0.15
                match_details['webgl_vendor_match'] = True
            else:
                match_details['webgl_vendor_match'] = False
            
            # WebGL renderer match
            webgl_renderer = fingerprint_data.get('features', {}).get('webgl', {}).get('renderer', '')
            if webgl_renderer in profile['webgl_renderers']:
                match_score += 0.15
                match_details['webgl_renderer_match'] = True
            else:
                match_details['webgl_renderer_match'] = False
            
            return {
                'is_vietnamese_profile': match_score >= 0.5,
                'match_score': match_score,
                'profile_details': match_details,
                'market_share': profile['market_share'],
                'popularity_score': profile['popularity_score']
            }
            
        except Exception as e:
            logger.error(f"Error matching Vietnamese profile: {e}")
            return {'is_vietnamese_profile': False, 'match_score': 0.0}
    
    def _assess_risk(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk level of the fingerprint"""
        try:
            risk_score = 0.0
            risk_factors = []
            
            # Check for bot-like characteristics
            basic_info = fingerprint_data.get('basic', {})
            
            # Missing or suspicious user agent
            user_agent = basic_info.get('userAgent', '')
            if not user_agent or user_agent in ['', 'undefined', 'null']:
                risk_score += 0.3
                risk_factors.append('Missing or empty user agent')
            elif len(user_agent) < 50:
                risk_score += 0.1
                risk_factors.append('Suspiciously short user agent')
            
            # Check for headless browser indicators
            plugins = fingerprint_data.get('features', {}).get('plugins', [])
            if not plugins:
                risk_score += 0.2
                risk_factors.append('No browser plugins detected')
            
            # Check WebGL support
            webgl_info = fingerprint_data.get('features', {}).get('webgl', {})
            if not webgl_info or not webgl_info.get('vendor'):
                risk_score += 0.15
                risk_factors.append('No WebGL support')
            
            # Check for suspicious screen dimensions
            screen_width = fingerprint_data.get('screen', {}).get('width', 0)
            screen_height = fingerprint_data.get('screen', {}).get('height', 0)
            if screen_width < 800 or screen_height < 600:
                risk_score += 0.1
                risk_factors.append('Unusually small screen dimensions')
            
            # Check for missing hardware info
            hardware = fingerprint_data.get('hardware', {})
            if not hardware.get('hardwareConcurrency'):
                risk_score += 0.1
                risk_factors.append('Missing hardware concurrency info')
            
            # Check for suspicious font list
            fonts = fingerprint_data.get('features', {}).get('fonts', [])
            if len(fonts) < 10:
                risk_score += 0.1
                risk_factors.append('Unusually small font list')
            
            # Check for missing canvas fingerprint
            canvas_fingerprint = fingerprint_data.get('canvas')
            if not canvas_fingerprint:
                risk_score += 0.15
                risk_factors.append('Missing canvas fingerprint')
            
            # Check for missing audio fingerprint
            audio_fingerprint = fingerprint_data.get('audio')
            if not audio_fingerprint:
                risk_score += 0.1
                risk_factors.append('Missing audio fingerprint')
            
            # Determine risk level
            if risk_score >= 0.7:
                risk_level = 'HIGH'
            elif risk_score >= 0.4:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'risk_score': min(risk_score, 1.0),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'bot_indicators': len(risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return {'risk_score': 0.5, 'risk_level': 'MEDIUM', 'risk_factors': []}
    
    def _check_consistency(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check consistency of fingerprint data"""
        try:
            consistency_score = 1.0
            inconsistencies = []
            
            # Check screen vs viewport consistency
            screen_width = fingerprint_data.get('screen', {}).get('width', 0)
            screen_height = fingerprint_data.get('screen', {}).get('height', 0)
            viewport_width = fingerprint_data.get('viewport', {}).get('width', 0)
            viewport_height = fingerprint_data.get('viewport', {}).get('height', 0)
            
            if viewport_width > screen_width or viewport_height > screen_height:
                consistency_score -= 0.2
                inconsistencies.append('Viewport larger than screen')
            
            # Check device pixel ratio consistency
            device_pixel_ratio = fingerprint_data.get('screen', {}).get('devicePixelRatio', 1)
            if device_pixel_ratio < 0.5 or device_pixel_ratio > 4:
                consistency_score -= 0.1
                inconsistencies.append('Suspicious device pixel ratio')
            
            # Check hardware consistency
            hardware_concurrency = fingerprint_data.get('hardware', {}).get('hardwareConcurrency', 0)
            device_memory = fingerprint_data.get('hardware', {}).get('deviceMemory', 0)
            
            if hardware_concurrency > 0 and device_memory > 0:
                # High-end devices should have reasonable memory
                if hardware_concurrency >= 8 and device_memory < 4:
                    consistency_score -= 0.1
                    inconsistencies.append('Hardware concurrency vs memory mismatch')
            
            # Check WebGL consistency
            webgl_info = fingerprint_data.get('features', {}).get('webgl', {})
            if webgl_info:
                vendor = webgl_info.get('vendor', '')
                renderer = webgl_info.get('renderer', '')
                
                # Check for suspicious WebGL combinations
                if 'Intel' in vendor and 'NVIDIA' in renderer:
                    consistency_score -= 0.2
                    inconsistencies.append('WebGL vendor/renderer mismatch')
            
            return {
                'consistency_score': max(consistency_score, 0.0),
                'inconsistencies': inconsistencies,
                'is_consistent': consistency_score >= 0.8
            }
            
        except Exception as e:
            logger.error(f"Error checking consistency: {e}")
            return {'consistency_score': 0.5, 'inconsistencies': [], 'is_consistent': False}
    
    def _analyze_behavior(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns"""
        try:
            behavioral_data = fingerprint_data.get('behavioral', {})
            
            if not behavioral_data:
                return {
                    'behavior_score': 0.5,
                    'behavior_type': 'unknown',
                    'suspicious_patterns': []
                }
            
            collection_time = behavioral_data.get('collectionTime', 0)
            mouse_movements = behavioral_data.get('mouseMovements', 0)
            key_presses = behavioral_data.get('keyPresses', 0)
            scroll_events = behavioral_data.get('scrollEvents', 0)
            click_events = behavioral_data.get('clickEvents', 0)
            touch_events = behavioral_data.get('touchEvents', 0)
            
            behavior_score = 0.5
            suspicious_patterns = []
            
            # Analyze interaction patterns
            total_interactions = mouse_movements + key_presses + scroll_events + click_events + touch_events
            
            if collection_time > 0:
                interaction_rate = total_interactions / (collection_time / 1000)  # interactions per second
                
                # Very low interaction rate might indicate bot
                if interaction_rate < 0.1:
                    behavior_score -= 0.2
                    suspicious_patterns.append('Very low interaction rate')
                
                # Very high interaction rate might indicate automated behavior
                elif interaction_rate > 10:
                    behavior_score -= 0.1
                    suspicious_patterns.append('Unusually high interaction rate')
            
            # Check for human-like patterns
            if mouse_movements > 0 and click_events > 0:
                mouse_to_click_ratio = mouse_movements / click_events
                if mouse_to_click_ratio < 5:  # Too few mouse movements per click
                    behavior_score -= 0.1
                    suspicious_patterns.append('Unnatural mouse-to-click ratio')
            
            # Determine behavior type
            if behavior_score >= 0.8:
                behavior_type = 'human'
            elif behavior_score >= 0.6:
                behavior_type = 'likely_human'
            elif behavior_score >= 0.4:
                behavior_type = 'suspicious'
            else:
                behavior_type = 'bot'
            
            return {
                'behavior_score': max(behavior_score, 0.0),
                'behavior_type': behavior_type,
                'suspicious_patterns': suspicious_patterns,
                'interaction_rate': interaction_rate if collection_time > 0 else 0,
                'total_interactions': total_interactions
            }
            
        except Exception as e:
            logger.error(f"Error analyzing behavior: {e}")
            return {'behavior_score': 0.5, 'behavior_type': 'unknown', 'suspicious_patterns': []}
    
    def _calculate_uniqueness(self, fingerprint_data: Dict[str, Any]) -> float:
        """Calculate uniqueness score of the fingerprint"""
        try:
            # Create a hash of key fingerprint components
            key_components = [
                fingerprint_data.get('basic', {}).get('userAgent', ''),
                str(fingerprint_data.get('screen', {}).get('width', 0)),
                str(fingerprint_data.get('screen', {}).get('height', 0)),
                str(fingerprint_data.get('hardware', {}).get('hardwareConcurrency', 0)),
                str(fingerprint_data.get('hardware', {}).get('deviceMemory', 0)),
                fingerprint_data.get('canvas', ''),
                fingerprint_data.get('audio', ''),
                fingerprint_data.get('features', {}).get('webgl', {}).get('vendor', ''),
                fingerprint_data.get('features', {}).get('webgl', {}).get('renderer', ''),
                fingerprint_data.get('timezone', {}).get('timezone', '')
            ]
            
            fingerprint_hash = hashlib.sha256('|'.join(key_components).encode()).hexdigest()
            
            # Check if this fingerprint hash has been seen before
            if fingerprint_hash in self.analysis_cache:
                return 0.1  # Very low uniqueness if seen before
            
            # Store in cache
            self.analysis_cache[fingerprint_hash] = time.time()
            
            # Clean old entries from cache (older than 1 hour)
            current_time = time.time()
            self.analysis_cache = {
                k: v for k, v in self.analysis_cache.items() 
                if current_time - v < 3600
            }
            
            return 1.0  # High uniqueness for new fingerprints
            
        except Exception as e:
            logger.error(f"Error calculating uniqueness: {e}")
            return 0.5
    
    def _calculate_bot_probability(self, fingerprint_data: Dict[str, Any]) -> float:
        """Calculate probability that this is a bot"""
        try:
            bot_score = 0.0
            
            # Risk assessment contributes to bot probability
            risk_assessment = self._assess_risk(fingerprint_data)
            bot_score += risk_assessment['risk_score'] * 0.4
            
            # Behavioral analysis contributes to bot probability
            behavioral_analysis = self._analyze_behavior(fingerprint_data)
            if behavioral_analysis['behavior_type'] == 'bot':
                bot_score += 0.4
            elif behavioral_analysis['behavior_type'] == 'suspicious':
                bot_score += 0.2
            
            # Consistency check contributes to bot probability
            consistency_check = self._check_consistency(fingerprint_data)
            if not consistency_check['is_consistent']:
                bot_score += 0.2
            
            # Check for specific bot indicators
            basic_info = fingerprint_data.get('basic', {})
            user_agent = basic_info.get('userAgent', '').lower()
            
            # Known bot user agents
            bot_patterns = [
                'headless', 'phantom', 'selenium', 'webdriver', 'bot', 'crawler',
                'spider', 'scraper', 'automated', 'test'
            ]
            
            for pattern in bot_patterns:
                if pattern in user_agent:
                    bot_score += 0.3
                    break
            
            return min(bot_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating bot probability: {e}")
            return 0.5
    
    def _calculate_confidence_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the analysis"""
        try:
            confidence = 0.0
            
            # Device detection confidence
            device_detection = analysis.get('device_detection', {})
            confidence += device_detection.get('confidence', 0) * 0.2
            
            # Vietnamese profile match
            vietnamese_match = analysis.get('vietnamese_profile_match', {})
            confidence += vietnamese_match.get('match_score', 0) * 0.2
            
            # Consistency score
            consistency_check = analysis.get('consistency_check', {})
            confidence += consistency_check.get('consistency_score', 0) * 0.2
            
            # Behavioral analysis
            behavioral_analysis = analysis.get('behavioral_analysis', {})
            confidence += behavioral_analysis.get('behavior_score', 0) * 0.2
            
            # Uniqueness score
            confidence += analysis.get('uniqueness_score', 0) * 0.1
            
            # Risk assessment (inverse)
            risk_assessment = analysis.get('risk_assessment', {})
            confidence += (1.0 - risk_assessment.get('risk_score', 0.5)) * 0.1
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        try:
            recommendations = []
            
            # Risk-based recommendations
            risk_assessment = analysis.get('risk_assessment', {})
            if risk_assessment.get('risk_level') == 'HIGH':
                recommendations.append('High risk fingerprint detected - consider additional verification')
            
            # Device-based recommendations
            device_detection = analysis.get('device_detection', {})
            if device_detection.get('device_type') == 'Unknown':
                recommendations.append('Unknown device type - verify device compatibility')
            
            # Vietnamese profile recommendations
            vietnamese_match = analysis.get('vietnamese_profile_match', {})
            if not vietnamese_match.get('is_vietnamese_profile'):
                recommendations.append('Device does not match Vietnamese market profiles')
            
            # Behavioral recommendations
            behavioral_analysis = analysis.get('behavioral_analysis', {})
            if behavioral_analysis.get('behavior_type') == 'bot':
                recommendations.append('Bot-like behavior detected - implement CAPTCHA')
            
            # Consistency recommendations
            consistency_check = analysis.get('consistency_check', {})
            if not consistency_check.get('is_consistent'):
                recommendations.append('Fingerprint inconsistencies detected - verify authenticity')
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ['Analysis error - manual review recommended']
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Get default analysis when errors occur"""
        return {
            'device_detection': {'device_type': 'Unknown', 'confidence': 0.0},
            'vietnamese_profile_match': {'is_vietnamese_profile': False, 'match_score': 0.0},
            'risk_assessment': {'risk_score': 0.5, 'risk_level': 'MEDIUM', 'risk_factors': []},
            'consistency_check': {'consistency_score': 0.5, 'is_consistent': False},
            'behavioral_analysis': {'behavior_score': 0.5, 'behavior_type': 'unknown'},
            'uniqueness_score': 0.5,
            'bot_probability': 0.5,
            'confidence_score': 0.5,
            'recommendations': ['Analysis error - manual review recommended']
        }

# Global analyzer instance
fingerprint_analyzer = None

def initialize_fingerprint_analyzer() -> FingerprintAnalyzer:
    """Initialize global fingerprint analyzer"""
    global fingerprint_analyzer
    fingerprint_analyzer = FingerprintAnalyzer()
    return fingerprint_analyzer

def get_fingerprint_analyzer() -> FingerprintAnalyzer:
    """Get global fingerprint analyzer"""
    if fingerprint_analyzer is None:
        raise ValueError("Fingerprint analyzer not initialized")
    return fingerprint_analyzer

# Convenience function
def analyze_fingerprint(fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze fingerprint (global convenience function)"""
    return get_fingerprint_analyzer().analyze_fingerprint(fingerprint_data)
