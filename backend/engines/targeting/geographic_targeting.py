"""
Geographic Targeting Engine
Targeting victims based on geographic location
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging
import requests
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GeographicTarget:
    """Geographic targeting criteria"""
    countries: List[str]
    regions: List[str]
    cities: List[str]
    exclude_countries: List[str]
    exclude_regions: List[str]
    exclude_cities: List[str]
    timezone_preferences: List[str]
    language_preferences: List[str]

class GeographicTargetingEngine:
    """Geographic targeting engine for campaigns"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Geographic data
        self.country_codes = {
            "Vietnam": "VN",
            "United States": "US",
            "United Kingdom": "GB",
            "Canada": "CA",
            "Australia": "AU",
            "Singapore": "SG",
            "Malaysia": "MY",
            "Thailand": "TH",
            "Philippines": "PH",
            "Indonesia": "ID"
        }
        
        self.vietnam_cities = [
            "Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong", "Can Tho",
            "Bien Hoa", "Hue", "Nha Trang", "Quy Nhon", "Vung Tau",
            "Thai Nguyen", "Thanh Hoa", "Nam Dinh", "Vinh", "Buon Ma Thuot"
        ]
        
        self.vietnam_regions = [
            "Northern Vietnam", "Central Vietnam", "Southern Vietnam",
            "Mekong Delta", "Central Highlands", "Red River Delta"
        ]
    
    def initialize_targeting(self, targeting_config: Any) -> bool:
        """Initialize geographic targeting"""
        try:
            self.target_config = targeting_config
            logger.info("Geographic targeting initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing geographic targeting: {e}")
            return False
    
    def get_target_victims(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get victims matching geographic criteria"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.victims
            query = {}
            
            # Build geographic query
            if self.target_config.countries:
                country_codes = [self.country_codes.get(country, country) for country in self.target_config.countries]
                query["country"] = {"$in": country_codes}
            
            if self.target_config.cities:
                query["city"] = {"$in": self.target_config.cities}
            
            # Exclude criteria
            if self.target_config.exclude_countries:
                exclude_codes = [self.country_codes.get(country, country) for country in self.target_config.exclude_countries]
                query["country"] = {"$nin": exclude_codes}
            
            if self.target_config.exclude_cities:
                query["city"] = {"$nin": self.target_config.exclude_cities}
            
            # Execute query
            cursor = collection.find(query).limit(limit)
            victims = list(cursor)
            
            logger.info(f"Found {len(victims)} victims matching geographic criteria")
            return victims
            
        except Exception as e:
            logger.error(f"Error getting geographic targets: {e}")
            return []
    
    def analyze_geographic_distribution(self, victims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze geographic distribution of victims"""
        try:
            distribution = {
                "by_country": {},
                "by_city": {},
                "by_region": {},
                "total_victims": len(victims)
            }
            
            for victim in victims:
                country = victim.get("country", "Unknown")
                city = victim.get("city", "Unknown")
                
                # Count by country
                distribution["by_country"][country] = distribution["by_country"].get(country, 0) + 1
                
                # Count by city
                distribution["by_city"][city] = distribution["by_city"].get(city, 0) + 1
                
                # Count by region (Vietnam specific)
                if country == "VN":
                    region = self._get_vietnam_region(city)
                    distribution["by_region"][region] = distribution["by_region"].get(region, 0) + 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error analyzing geographic distribution: {e}")
            return {}
    
    def _get_vietnam_region(self, city: str) -> str:
        """Get Vietnam region for city"""
        northern_cities = ["Hanoi", "Hai Phong", "Thai Nguyen", "Thanh Hoa", "Nam Dinh", "Vinh"]
        central_cities = ["Da Nang", "Hue", "Nha Trang", "Quy Nhon", "Vung Tau"]
        southern_cities = ["Ho Chi Minh City", "Can Tho", "Bien Hoa", "Buon Ma Thuot"]
        
        if city in northern_cities:
            return "Northern Vietnam"
        elif city in central_cities:
            return "Central Vietnam"
        elif city in southern_cities:
            return "Southern Vietnam"
        else:
            return "Unknown Region"
    
    def get_optimal_delivery_times(self, country: str) -> List[int]:
        """Get optimal delivery times for country"""
        # Business hours in local timezone
        optimal_times = {
            "VN": [9, 10, 11, 14, 15, 16],  # Vietnam business hours
            "US": [9, 10, 11, 14, 15, 16],  # US business hours
            "GB": [9, 10, 11, 14, 15, 16],  # UK business hours
            "CA": [9, 10, 11, 14, 15, 16],  # Canada business hours
            "AU": [9, 10, 11, 14, 15, 16],  # Australia business hours
        }
        
        return optimal_times.get(country, [9, 10, 11, 14, 15, 16])
    
    def get_localization_settings(self, country: str) -> Dict[str, Any]:
        """Get localization settings for country"""
        localization = {
            "VN": {
                "language": "vi",
                "currency": "VND",
                "date_format": "DD/MM/YYYY",
                "timezone": "Asia/Ho_Chi_Minh",
                "phone_format": "+84",
                "address_format": "street, ward, district, city"
            },
            "US": {
                "language": "en",
                "currency": "USD",
                "date_format": "MM/DD/YYYY",
                "timezone": "America/New_York",
                "phone_format": "+1",
                "address_format": "street, city, state, zip"
            },
            "GB": {
                "language": "en",
                "currency": "GBP",
                "date_format": "DD/MM/YYYY",
                "timezone": "Europe/London",
                "phone_format": "+44",
                "address_format": "street, city, postcode"
            }
        }
        
        return localization.get(country, localization["US"])
