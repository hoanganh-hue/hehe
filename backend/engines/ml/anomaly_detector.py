"""
Anomaly Detection Engine
Advanced anomaly detection and pattern analysis for the ZaloPay Merchant Phishing Platform
"""

import os
import json
import time
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import joblib
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

# Machine Learning imports
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN, KMeans, OPTICS
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.neural_network import MLPClassifier
from sklearn.svm import OneClassSVM
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.stats import zscore
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    """Anomaly type enumeration"""
    STATISTICAL = "statistical"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    NETWORK = "network"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATA_QUALITY = "data_quality"
    SYSTEM = "system"

class AnomalySeverity(Enum):
    """Anomaly severity enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float
    confidence: float
    description: str
    detected_at: datetime
    features: Dict[str, Any]
    context: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any]

@dataclass
class AnomalyPattern:
    """Anomaly pattern structure"""
    pattern_id: str
    pattern_name: str
    anomaly_type: AnomalyType
    description: str
    frequency: float
    confidence: float
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    created_at: datetime
    last_seen: datetime

class AnomalyDetector:
    """Advanced anomaly detection engine"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.detectors = {}
        self.scalers = {}
        self.label_encoders = {}
        self.anomaly_patterns = {}
        
        # Initialize anomaly detectors
        self._initialize_detectors()
        
        # Historical data storage
        self.historical_data = defaultdict(deque)
        self.max_history_size = 10000
        
        # Anomaly cache
        self.anomaly_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Thresholds for different anomaly types
        self.thresholds = {
            AnomalyType.STATISTICAL: 0.1,
            AnomalyType.BEHAVIORAL: 0.15,
            AnomalyType.TEMPORAL: 0.2,
            AnomalyType.NETWORK: 0.25,
            AnomalyType.SECURITY: 0.05,
            AnomalyType.PERFORMANCE: 0.3,
            AnomalyType.DATA_QUALITY: 0.2,
            AnomalyType.SYSTEM: 0.1
        }
    
    def _initialize_detectors(self):
        """Initialize anomaly detection models"""
        try:
            # Statistical anomaly detectors
            self.detectors[AnomalyType.STATISTICAL] = {
                'isolation_forest': IsolationForest(contamination=0.1, random_state=42),
                'one_class_svm': OneClassSVM(nu=0.1, kernel='rbf'),
                'zscore': None,  # Custom implementation
                'iqr': None  # Custom implementation
            }
            
            # Behavioral anomaly detectors
            self.detectors[AnomalyType.BEHAVIORAL] = {
                'isolation_forest': IsolationForest(contamination=0.15, random_state=42),
                'dbscan': DBSCAN(eps=0.5, min_samples=5),
                'kmeans': KMeans(n_clusters=5, random_state=42),
                'optics': OPTICS(min_samples=5, max_eps=0.5)
            }
            
            # Temporal anomaly detectors
            self.detectors[AnomalyType.TEMPORAL] = {
                'isolation_forest': IsolationForest(contamination=0.2, random_state=42),
                'one_class_svm': OneClassSVM(nu=0.2, kernel='rbf'),
                'seasonal_decomposition': None,  # Custom implementation
                'change_point': None  # Custom implementation
            }
            
            # Network anomaly detectors
            self.detectors[AnomalyType.NETWORK] = {
                'isolation_forest': IsolationForest(contamination=0.25, random_state=42),
                'dbscan': DBSCAN(eps=0.3, min_samples=3),
                'kmeans': KMeans(n_clusters=3, random_state=42),
                'network_analysis': None  # Custom implementation
            }
            
            # Security anomaly detectors
            self.detectors[AnomalyType.SECURITY] = {
                'isolation_forest': IsolationForest(contamination=0.05, random_state=42),
                'one_class_svm': OneClassSVM(nu=0.05, kernel='rbf'),
                'security_rules': None,  # Custom implementation
                'threat_intelligence': None  # Custom implementation
            }
            
            # Performance anomaly detectors
            self.detectors[AnomalyType.PERFORMANCE] = {
                'isolation_forest': IsolationForest(contamination=0.3, random_state=42),
                'one_class_svm': OneClassSVM(nu=0.3, kernel='rbf'),
                'threshold_based': None,  # Custom implementation
                'trend_analysis': None  # Custom implementation
            }
            
            # Data quality anomaly detectors
            self.detectors[AnomalyType.DATA_QUALITY] = {
                'isolation_forest': IsolationForest(contamination=0.2, random_state=42),
                'dbscan': DBSCAN(eps=0.4, min_samples=3),
                'data_validation': None,  # Custom implementation
                'completeness_check': None  # Custom implementation
            }
            
            # System anomaly detectors
            self.detectors[AnomalyType.SYSTEM] = {
                'isolation_forest': IsolationForest(contamination=0.1, random_state=42),
                'one_class_svm': OneClassSVM(nu=0.1, kernel='rbf'),
                'system_metrics': None,  # Custom implementation
                'resource_monitoring': None  # Custom implementation
            }
            
            # Initialize scalers and encoders
            for anomaly_type in AnomalyType:
                self.scalers[anomaly_type] = StandardScaler()
                self.label_encoders[anomaly_type] = LabelEncoder()
            
            logger.info("Anomaly detection models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing anomaly detectors: {e}")
            raise
    
    def create_anomaly_features(self, data: Dict[str, Any], anomaly_type: AnomalyType) -> np.ndarray:
        """Create features for anomaly detection"""
        try:
            features = []
            
            if anomaly_type == AnomalyType.STATISTICAL:
                features = self._create_statistical_features(data)
            elif anomaly_type == AnomalyType.BEHAVIORAL:
                features = self._create_behavioral_features(data)
            elif anomaly_type == AnomalyType.TEMPORAL:
                features = self._create_temporal_features(data)
            elif anomaly_type == AnomalyType.NETWORK:
                features = self._create_network_features(data)
            elif anomaly_type == AnomalyType.SECURITY:
                features = self._create_security_features(data)
            elif anomaly_type == AnomalyType.PERFORMANCE:
                features = self._create_performance_features(data)
            elif anomaly_type == AnomalyType.DATA_QUALITY:
                features = self._create_data_quality_features(data)
            elif anomaly_type == AnomalyType.SYSTEM:
                features = self._create_system_features(data)
            else:
                features = self._create_generic_features(data)
            
            return features.reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating anomaly features: {e}")
            return np.zeros((1, 20))  # Default feature vector
    
    def _create_statistical_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for statistical anomaly detection"""
        try:
            features = []
            
            # Basic statistical measures
            values = data.get('values', [])
            if values:
                features.extend([
                    np.mean(values),
                    np.std(values),
                    np.min(values),
                    np.max(values),
                    np.median(values),
                    np.percentile(values, 25),
                    np.percentile(values, 75),
                    stats.skew(values),
                    stats.kurtosis(values),
                    len(values)
                ])
            else:
                features.extend([0] * 10)
            
            # Z-score based features
            if values and len(values) > 1:
                z_scores = np.abs(zscore(values))
                features.extend([
                    np.max(z_scores),
                    np.mean(z_scores),
                    np.std(z_scores),
                    np.sum(z_scores > 2),
                    np.sum(z_scores > 3)
                ])
            else:
                features.extend([0] * 5)
            
            # IQR based features
            if values and len(values) > 3:
                q1 = np.percentile(values, 25)
                q3 = np.percentile(values, 75)
                iqr = q3 - q1
                features.extend([
                    iqr,
                    np.sum((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)),
                    np.sum((values < q1 - 3 * iqr) | (values > q3 + 3 * iqr))
                ])
            else:
                features.extend([0] * 3)
            
            # Distribution features
            if values and len(values) > 1:
                features.extend([
                    len(set(values)) / len(values),  # Uniqueness ratio
                    np.var(values),
                    np.ptp(values)  # Range
                ])
            else:
                features.extend([0] * 3)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating statistical features: {e}")
            return np.zeros(21)
    
    def _create_behavioral_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for behavioral anomaly detection"""
        try:
            features = []
            
            # User behavior patterns
            features.extend([
                data.get('login_frequency', 0),
                data.get('session_duration_avg', 0),
                data.get('page_views_avg', 0),
                data.get('click_rate', 0),
                data.get('form_completion_rate', 0),
                data.get('time_on_site_avg', 0)
            ])
            
            # Interaction patterns
            features.extend([
                data.get('mouse_movements', 0),
                data.get('keyboard_activity', 0),
                data.get('scroll_behavior', 0),
                data.get('focus_changes', 0),
                data.get('click_patterns', 0),
                data.get('navigation_patterns', 0)
            ])
            
            # Temporal patterns
            features.extend([
                data.get('hour_of_day', 0),
                data.get('day_of_week', 0),
                data.get('month', 0),
                data.get('is_weekend', 0),
                data.get('is_business_hours', 0),
                data.get('activity_consistency', 0)
            ])
            
            # Device and location patterns
            features.extend([
                data.get('device_type_encoded', 0),
                data.get('browser_encoded', 0),
                data.get('os_encoded', 0),
                data.get('location_encoded', 0),
                data.get('ip_address_encoded', 0),
                data.get('user_agent_encoded', 0)
            ])
            
            # Anomaly indicators
            features.extend([
                data.get('unusual_activity_score', 0),
                data.get('suspicious_pattern_score', 0),
                data.get('deviation_from_norm', 0),
                data.get('risk_level', 0),
                data.get('threat_level', 0),
                data.get('vulnerability_score', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating behavioral features: {e}")
            return np.zeros(30)
    
    def _create_temporal_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for temporal anomaly detection"""
        try:
            features = []
            
            # Time-based features
            timestamp = data.get('timestamp', datetime.now(timezone.utc))
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            features.extend([
                timestamp.hour,
                timestamp.day,
                timestamp.month,
                timestamp.weekday(),
                timestamp.isoweekday(),
                timestamp.timestamp()
            ])
            
            # Seasonal features
            features.extend([
                int(timestamp.month in [12, 1, 2]),  # Winter
                int(timestamp.month in [3, 4, 5]),   # Spring
                int(timestamp.month in [6, 7, 8]),   # Summer
                int(timestamp.month in [9, 10, 11]), # Fall
                int(timestamp.weekday() < 5),        # Weekday
                int(timestamp.weekday() >= 5)        # Weekend
            ])
            
            # Time series features
            time_series = data.get('time_series', [])
            if time_series and len(time_series) > 1:
                features.extend([
                    np.mean(time_series),
                    np.std(time_series),
                    np.max(time_series) - np.min(time_series),
                    len(time_series),
                    np.corrcoef(time_series[:-1], time_series[1:])[0, 1] if len(time_series) > 1 else 0
                ])
            else:
                features.extend([0] * 5)
            
            # Frequency features
            features.extend([
                data.get('event_frequency', 0),
                data.get('time_since_last_event', 0),
                data.get('event_interval_avg', 0),
                data.get('event_interval_std', 0),
                data.get('burst_activity', 0),
                data.get('quiet_periods', 0)
            ])
            
            # Trend features
            features.extend([
                data.get('trend_direction', 0),
                data.get('trend_strength', 0),
                data.get('seasonality_strength', 0),
                data.get('cyclical_patterns', 0),
                data.get('change_points', 0),
                data.get('volatility', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating temporal features: {e}")
            return np.zeros(30)
    
    def _create_network_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for network anomaly detection"""
        try:
            features = []
            
            # IP address features
            ip_address = data.get('ip_address', '')
            features.extend([
                data.get('ip_country_encoded', 0),
                data.get('ip_region_encoded', 0),
                data.get('ip_city_encoded', 0),
                data.get('is_vpn', 0),
                data.get('is_proxy', 0),
                data.get('is_tor', 0),
                data.get('ip_reputation_score', 0)
            ])
            
            # Network traffic features
            features.extend([
                data.get('bytes_sent', 0),
                data.get('bytes_received', 0),
                data.get('packets_sent', 0),
                data.get('packets_received', 0),
                data.get('connection_count', 0),
                data.get('unique_connections', 0),
                data.get('connection_duration_avg', 0)
            ])
            
            # Protocol features
            features.extend([
                data.get('http_requests', 0),
                data.get('https_requests', 0),
                data.get('dns_queries', 0),
                data.get('tcp_connections', 0),
                data.get('udp_connections', 0),
                data.get('icmp_packets', 0),
                data.get('protocol_diversity', 0)
            ])
            
            # Geographic features
            features.extend([
                data.get('latitude', 0),
                data.get('longitude', 0),
                data.get('timezone_offset', 0),
                data.get('language_encoded', 0),
                data.get('currency_encoded', 0),
                data.get('country_risk_score', 0),
                data.get('region_risk_score', 0)
            ])
            
            # Network topology features
            features.extend([
                data.get('hop_count', 0),
                data.get('rtt_avg', 0),
                data.get('packet_loss', 0),
                data.get('bandwidth_utilization', 0),
                data.get('network_congestion', 0),
                data.get('jitter', 0),
                data.get('latency_variance', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating network features: {e}")
            return np.zeros(35)
    
    def _create_security_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for security anomaly detection"""
        try:
            features = []
            
            # Security indicators
            features.extend([
                data.get('failed_login_attempts', 0),
                data.get('suspicious_activity_count', 0),
                data.get('unauthorized_access_attempts', 0),
                data.get('privilege_escalation_attempts', 0),
                data.get('data_exfiltration_attempts', 0),
                data.get('malware_detection_count', 0),
                data.get('phishing_attempts', 0)
            ])
            
            # Threat intelligence features
            features.extend([
                data.get('threat_intelligence_score', 0),
                data.get('known_malicious_ip', 0),
                data.get('known_malicious_domain', 0),
                data.get('known_malicious_file_hash', 0),
                data.get('reputation_score', 0),
                data.get('threat_level', 0),
                data.get('attack_sophistication', 0)
            ])
            
            # Vulnerability features
            features.extend([
                data.get('vulnerability_count', 0),
                data.get('critical_vulnerabilities', 0),
                data.get('high_vulnerabilities', 0),
                data.get('medium_vulnerabilities', 0),
                data.get('low_vulnerabilities', 0),
                data.get('exploit_availability', 0),
                data.get('patch_status', 0)
            ])
            
            # Access control features
            features.extend([
                data.get('access_control_violations', 0),
                data.get('permission_escalation', 0),
                data.get('unusual_access_patterns', 0),
                data.get('off_hours_access', 0),
                data.get('geographic_anomaly', 0),
                data.get('device_anomaly', 0),
                data.get('behavioral_anomaly', 0)
            ])
            
            # Incident response features
            features.extend([
                data.get('incident_count', 0),
                data.get('incident_severity_avg', 0),
                data.get('response_time_avg', 0),
                data.get('containment_success_rate', 0),
                data.get('recovery_time_avg', 0),
                data.get('lessons_learned_count', 0),
                data.get('prevention_measures', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating security features: {e}")
            return np.zeros(35)
    
    def _create_performance_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for performance anomaly detection"""
        try:
            features = []
            
            # System performance metrics
            features.extend([
                data.get('cpu_usage', 0),
                data.get('memory_usage', 0),
                data.get('disk_usage', 0),
                data.get('network_usage', 0),
                data.get('io_usage', 0),
                data.get('load_average', 0),
                data.get('process_count', 0)
            ])
            
            # Application performance metrics
            features.extend([
                data.get('response_time', 0),
                data.get('throughput', 0),
                data.get('error_rate', 0),
                data.get('success_rate', 0),
                data.get('availability', 0),
                data.get('latency', 0),
                data.get('queue_length', 0)
            ])
            
            # Database performance metrics
            features.extend([
                data.get('db_connections', 0),
                data.get('db_query_time', 0),
                data.get('db_lock_wait_time', 0),
                data.get('db_cache_hit_ratio', 0),
                data.get('db_deadlocks', 0),
                data.get('db_slow_queries', 0),
                data.get('db_transaction_rate', 0)
            ])
            
            # Network performance metrics
            features.extend([
                data.get('bandwidth_utilization', 0),
                data.get('packet_loss', 0),
                data.get('jitter', 0),
                data.get('rtt', 0),
                data.get('connection_errors', 0),
                data.get('timeout_errors', 0),
                data.get('retry_attempts', 0)
            ])
            
            # Resource utilization trends
            features.extend([
                data.get('cpu_trend', 0),
                data.get('memory_trend', 0),
                data.get('disk_trend', 0),
                data.get('network_trend', 0),
                data.get('performance_degradation', 0),
                data.get('capacity_utilization', 0),
                data.get('scalability_issues', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating performance features: {e}")
            return np.zeros(35)
    
    def _create_data_quality_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for data quality anomaly detection"""
        try:
            features = []
            
            # Completeness features
            features.extend([
                data.get('completeness_ratio', 0),
                data.get('missing_values_count', 0),
                data.get('null_values_count', 0),
                data.get('empty_values_count', 0),
                data.get('required_fields_missing', 0),
                data.get('optional_fields_missing', 0),
                data.get('data_coverage', 0)
            ])
            
            # Consistency features
            features.extend([
                data.get('consistency_score', 0),
                data.get('format_errors', 0),
                data.get('type_errors', 0),
                data.get('range_errors', 0),
                data.get('constraint_violations', 0),
                data.get('duplicate_records', 0),
                data.get('referential_integrity_violations', 0)
            ])
            
            # Accuracy features
            features.extend([
                data.get('accuracy_score', 0),
                data.get('validation_errors', 0),
                data.get('business_rule_violations', 0),
                data.get('logical_errors', 0),
                data.get('calculation_errors', 0),
                data.get('data_anomalies', 0),
                data.get('outlier_count', 0)
            ])
            
            # Timeliness features
            features.extend([
                data.get('timeliness_score', 0),
                data.get('data_age', 0),
                data.get('update_frequency', 0),
                data.get('latency', 0),
                data.get('freshness', 0),
                data.get('staleness', 0),
                data.get('synchronization_issues', 0)
            ])
            
            # Uniqueness features
            features.extend([
                data.get('uniqueness_score', 0),
                data.get('duplicate_ratio', 0),
                data.get('unique_records', 0),
                data.get('duplicate_records', 0),
                data.get('key_violations', 0),
                data.get('identity_conflicts', 0),
                data.get('merge_issues', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating data quality features: {e}")
            return np.zeros(35)
    
    def _create_system_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for system anomaly detection"""
        try:
            features = []
            
            # System resource metrics
            features.extend([
                data.get('cpu_usage', 0),
                data.get('memory_usage', 0),
                data.get('disk_usage', 0),
                data.get('network_usage', 0),
                data.get('swap_usage', 0),
                data.get('load_average', 0),
                data.get('process_count', 0)
            ])
            
            # System health indicators
            features.extend([
                data.get('system_uptime', 0),
                data.get('service_availability', 0),
                data.get('error_count', 0),
                data.get('warning_count', 0),
                data.get('critical_count', 0),
                data.get('restart_count', 0),
                data.get('crash_count', 0)
            ])
            
            # Log analysis features
            features.extend([
                data.get('log_volume', 0),
                data.get('error_log_ratio', 0),
                data.get('warning_log_ratio', 0),
                data.get('critical_log_ratio', 0),
                data.get('log_pattern_anomalies', 0),
                data.get('log_frequency_anomalies', 0),
                data.get('log_content_anomalies', 0)
            ])
            
            # Configuration features
            features.extend([
                data.get('config_changes', 0),
                data.get('config_drifts', 0),
                data.get('compliance_violations', 0),
                data.get('security_violations', 0),
                data.get('policy_violations', 0),
                data.get('standard_deviations', 0),
                data.get('baseline_deviations', 0)
            ])
            
            # Dependency features
            features.extend([
                data.get('dependency_failures', 0),
                data.get('service_dependencies', 0),
                data.get('network_dependencies', 0),
                data.get('database_dependencies', 0),
                data.get('external_dependencies', 0),
                data.get('cascade_failures', 0),
                data.get('dependency_health', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating system features: {e}")
            return np.zeros(35)
    
    def _create_generic_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create generic features for any anomaly type"""
        try:
            features = []
            
            # Basic numerical features
            numerical_features = ['value', 'count', 'rate', 'score', 'level', 'frequency', 'duration']
            for feature in numerical_features:
                features.append(data.get(feature, 0))
            
            # Basic categorical features (encoded)
            categorical_features = ['type', 'category', 'status', 'severity', 'priority']
            for feature in categorical_features:
                features.append(data.get(f'{feature}_encoded', 0))
            
            # Basic temporal features
            features.extend([
                data.get('hour_of_day', 0),
                data.get('day_of_week', 0),
                data.get('month', 0),
                data.get('is_weekend', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating generic features: {e}")
            return np.zeros(20)
    
    def detect_anomalies(self, data: List[Dict[str, Any]], 
                        anomaly_type: AnomalyType = AnomalyType.BEHAVIORAL) -> List[AnomalyDetection]:
        """Detect anomalies in data"""
        try:
            anomalies = []
            
            # Prepare data
            X = []
            for data_point in data:
                features = self.create_anomaly_features(data_point, anomaly_type)
                X.append(features.flatten())
            
            X = np.array(X)
            X_scaled = self.scalers[anomaly_type].fit_transform(X)
            
            # Detect anomalies using multiple methods
            for detector_name, detector in self.detectors[anomaly_type].items():
                if detector is None:
                    continue
                
                try:
                    if detector_name == 'dbscan':
                        labels = detector.fit_predict(X_scaled)
                        anomaly_indices = np.where(labels == -1)[0]
                        anomaly_scores = np.full(len(X_scaled), 0.0)
                    elif detector_name == 'kmeans':
                        labels = detector.fit_predict(X_scaled)
                        # Calculate distance to cluster centers
                        distances = np.min(detector.transform(X_scaled), axis=1)
                        threshold = np.percentile(distances, 95)
                        anomaly_indices = np.where(distances > threshold)[0]
                        anomaly_scores = distances
                    elif detector_name == 'optics':
                        labels = detector.fit_predict(X_scaled)
                        anomaly_indices = np.where(labels == -1)[0]
                        anomaly_scores = np.full(len(X_scaled), 0.0)
                    else:
                        # Isolation Forest or One-Class SVM
                        anomaly_scores = detector.decision_function(X_scaled)
                        threshold = np.percentile(anomaly_scores, 5)  # Bottom 5% as anomalies
                        anomaly_indices = np.where(anomaly_scores < threshold)[0]
                    
                    # Create anomaly objects
                    for idx in anomaly_indices:
                        anomaly_id = f"anomaly_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                        
                        # Calculate severity
                        severity = self._calculate_anomaly_severity(anomaly_scores[idx], anomaly_type)
                        
                        # Generate description
                        description = self._generate_anomaly_description(
                            data[idx], anomaly_type, detector_name, anomaly_scores[idx]
                        )
                        
                        # Generate recommendations
                        recommendations = self._generate_anomaly_recommendations(
                            data[idx], anomaly_type, severity
                        )
                        
                        anomaly = AnomalyDetection(
                            anomaly_id=anomaly_id,
                            anomaly_type=anomaly_type,
                            severity=severity,
                            score=float(anomaly_scores[idx]),
                            confidence=self._calculate_anomaly_confidence(anomaly_scores[idx], anomaly_type),
                            description=description,
                            detected_at=datetime.now(timezone.utc),
                            features=data[idx],
                            context=self._extract_anomaly_context(data[idx], anomaly_type),
                            recommendations=recommendations,
                            metadata={
                                'detector': detector_name,
                                'threshold': float(threshold) if 'threshold' in locals() else 0.0,
                                'feature_count': len(X_scaled[0])
                            }
                        )
                        
                        anomalies.append(anomaly)
                        
                except Exception as e:
                    logger.error(f"Error with {detector_name} detector: {e}")
                    continue
            
            # Remove duplicates
            unique_anomalies = self._deduplicate_anomalies(anomalies)
            
            # Store anomalies
            for anomaly in unique_anomalies:
                self._store_anomaly(anomaly)
            
            logger.info(f"Detected {len(unique_anomalies)} anomalies using {anomaly_type.value}")
            return unique_anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _calculate_anomaly_severity(self, score: float, anomaly_type: AnomalyType) -> AnomalySeverity:
        """Calculate anomaly severity based on score and type"""
        try:
            # Normalize score to 0-1 range
            normalized_score = abs(score)
            
            # Adjust thresholds based on anomaly type
            threshold_multiplier = 1.0
            if anomaly_type == AnomalyType.SECURITY:
                threshold_multiplier = 0.5  # Lower threshold for security
            elif anomaly_type == AnomalyType.PERFORMANCE:
                threshold_multiplier = 1.5  # Higher threshold for performance
            
            if normalized_score > 0.8 * threshold_multiplier:
                return AnomalySeverity.CRITICAL
            elif normalized_score > 0.6 * threshold_multiplier:
                return AnomalySeverity.HIGH
            elif normalized_score > 0.4 * threshold_multiplier:
                return AnomalySeverity.MEDIUM
            elif normalized_score > 0.2 * threshold_multiplier:
                return AnomalySeverity.LOW
            else:
                return AnomalySeverity.INFO
                
        except Exception as e:
            logger.error(f"Error calculating anomaly severity: {e}")
            return AnomalySeverity.MEDIUM
    
    def _calculate_anomaly_confidence(self, score: float, anomaly_type: AnomalyType) -> float:
        """Calculate anomaly confidence based on score and type"""
        try:
            # Normalize score to 0-1 range
            normalized_score = abs(score)
            
            # Adjust confidence based on anomaly type
            if anomaly_type == AnomalyType.SECURITY:
                return min(1.0, normalized_score * 1.5)  # Higher confidence for security
            elif anomaly_type == AnomalyType.PERFORMANCE:
                return min(1.0, normalized_score * 0.8)  # Lower confidence for performance
            else:
                return min(1.0, normalized_score)
                
        except Exception as e:
            logger.error(f"Error calculating anomaly confidence: {e}")
            return 0.5
    
    def _generate_anomaly_description(self, data: Dict[str, Any], anomaly_type: AnomalyType, 
                                    detector_name: str, score: float) -> str:
        """Generate human-readable anomaly description"""
        try:
            descriptions = {
                AnomalyType.STATISTICAL: f"Statistical anomaly detected in data distribution",
                AnomalyType.BEHAVIORAL: f"Behavioral anomaly detected in user activity patterns",
                AnomalyType.TEMPORAL: f"Temporal anomaly detected in time-based patterns",
                AnomalyType.NETWORK: f"Network anomaly detected in traffic patterns",
                AnomalyType.SECURITY: f"Security anomaly detected in system behavior",
                AnomalyType.PERFORMANCE: f"Performance anomaly detected in system metrics",
                AnomalyType.DATA_QUALITY: f"Data quality anomaly detected in dataset",
                AnomalyType.SYSTEM: f"System anomaly detected in operational metrics"
            }
            
            base_description = descriptions.get(anomaly_type, "Anomaly detected in data pattern")
            
            # Add specific details based on data
            if 'timestamp' in data:
                base_description += f" (Time: {data['timestamp']})"
            if 'user_id' in data:
                base_description += f" (User: {data['user_id']})"
            if 'ip_address' in data:
                base_description += f" (IP: {data['ip_address']})"
            if 'value' in data:
                base_description += f" (Value: {data['value']})"
            
            # Add detector information
            base_description += f" [Detected by: {detector_name}]"
            
            return base_description
            
        except Exception as e:
            logger.error(f"Error generating anomaly description: {e}")
            return "Anomaly detected in data pattern"
    
    def _generate_anomaly_recommendations(self, data: Dict[str, Any], anomaly_type: AnomalyType, 
                                        severity: AnomalySeverity) -> List[str]:
        """Generate recommendations for anomaly handling"""
        try:
            recommendations = []
            
            if anomaly_type == AnomalyType.SECURITY:
                recommendations.extend([
                    "Investigate potential security threat immediately",
                    "Review access logs for suspicious activity",
                    "Consider implementing additional security controls",
                    "Notify security team for further analysis",
                    "Check for indicators of compromise"
                ])
            elif anomaly_type == AnomalyType.BEHAVIORAL:
                recommendations.extend([
                    "Monitor user behavior patterns closely",
                    "Check for account compromise indicators",
                    "Review recent activity for unusual patterns",
                    "Consider additional authentication requirements",
                    "Analyze user session data for anomalies"
                ])
            elif anomaly_type == AnomalyType.NETWORK:
                recommendations.extend([
                    "Check network connectivity and performance",
                    "Review firewall and security rules",
                    "Monitor for DDoS or other network attacks",
                    "Verify network configuration changes",
                    "Analyze network traffic patterns"
                ])
            elif anomaly_type == AnomalyType.PERFORMANCE:
                recommendations.extend([
                    "Review system performance metrics",
                    "Check for resource bottlenecks",
                    "Monitor application performance",
                    "Verify system configuration",
                    "Consider scaling resources"
                ])
            elif anomaly_type == AnomalyType.DATA_QUALITY:
                recommendations.extend([
                    "Review data validation rules",
                    "Check data source integrity",
                    "Verify data processing pipeline",
                    "Implement additional data quality checks",
                    "Monitor data completeness and accuracy"
                ])
            else:
                recommendations.extend([
                    "Investigate anomaly for further analysis",
                    "Review system logs and metrics",
                    "Check for configuration changes",
                    "Monitor for recurring anomalies",
                    "Document findings and actions taken"
                ])
            
            # Add severity-specific recommendations
            if severity == AnomalySeverity.CRITICAL:
                recommendations.insert(0, "URGENT: Immediate action required")
            elif severity == AnomalySeverity.HIGH:
                recommendations.insert(0, "HIGH PRIORITY: Address within 1 hour")
            elif severity == AnomalySeverity.MEDIUM:
                recommendations.insert(0, "MEDIUM PRIORITY: Address within 4 hours")
            elif severity == AnomalySeverity.LOW:
                recommendations.insert(0, "LOW PRIORITY: Address within 24 hours")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating anomaly recommendations: {e}")
            return ["Investigate anomaly for further analysis"]
    
    def _extract_anomaly_context(self, data: Dict[str, Any], anomaly_type: AnomalyType) -> Dict[str, Any]:
        """Extract context information for anomaly"""
        try:
            context = {}
            
            # Extract relevant context based on anomaly type
            if anomaly_type == AnomalyType.SECURITY:
                context.update({
                    'security_indicators': data.get('security_indicators', []),
                    'threat_level': data.get('threat_level', 'unknown'),
                    'attack_vectors': data.get('attack_vectors', []),
                    'vulnerabilities': data.get('vulnerabilities', [])
                })
            elif anomaly_type == AnomalyType.BEHAVIORAL:
                context.update({
                    'user_behavior': data.get('user_behavior', {}),
                    'session_info': data.get('session_info', {}),
                    'device_info': data.get('device_info', {}),
                    'location_info': data.get('location_info', {})
                })
            elif anomaly_type == AnomalyType.NETWORK:
                context.update({
                    'network_traffic': data.get('network_traffic', {}),
                    'connection_info': data.get('connection_info', {}),
                    'protocol_info': data.get('protocol_info', {}),
                    'geographic_info': data.get('geographic_info', {})
                })
            elif anomaly_type == AnomalyType.PERFORMANCE:
                context.update({
                    'performance_metrics': data.get('performance_metrics', {}),
                    'resource_usage': data.get('resource_usage', {}),
                    'system_health': data.get('system_health', {}),
                    'application_status': data.get('application_status', {})
                })
            else:
                context.update({
                    'general_context': data.get('context', {}),
                    'metadata': data.get('metadata', {}),
                    'tags': data.get('tags', []),
                    'categories': data.get('categories', [])
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting anomaly context: {e}")
            return {}
    
    def _deduplicate_anomalies(self, anomalies: List[AnomalyDetection]) -> List[AnomalyDetection]:
        """Remove duplicate anomalies"""
        try:
            unique_anomalies = []
            seen_features = set()
            
            for anomaly in anomalies:
                # Create a feature signature for deduplication
                feature_signature = tuple(sorted(anomaly.features.items()))
                
                if feature_signature not in seen_features:
                    unique_anomalies.append(anomaly)
                    seen_features.add(feature_signature)
            
            return unique_anomalies
            
        except Exception as e:
            logger.error(f"Error deduplicating anomalies: {e}")
            return anomalies
    
    def _store_anomaly(self, anomaly: AnomalyDetection):
        """Store anomaly detection result"""
        try:
            if self.mongodb:
                collection = self.mongodb.anomaly_detections
                doc = asdict(anomaly)
                doc["detected_at"] = anomaly.detected_at
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing anomaly: {e}")

# Global anomaly detector instance
anomaly_detector = None

def initialize_anomaly_detector(mongodb_connection=None, redis_client=None) -> AnomalyDetector:
    """Initialize anomaly detector"""
    global anomaly_detector
    anomaly_detector = AnomalyDetector(mongodb_connection, redis_client)
    return anomaly_detector

def get_anomaly_detector() -> AnomalyDetector:
    """Get anomaly detector instance"""
    global anomaly_detector
    if anomaly_detector is None:
        anomaly_detector = AnomalyDetector()
    return anomaly_detector
