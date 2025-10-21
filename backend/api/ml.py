"""
Machine Learning API Endpoints
REST API for ML pattern analysis, behavior prediction, and anomaly detection
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ml", tags=["machine-learning"])

# Pydantic models
class MLPredictionRequest(BaseModel):
    pattern_type: str
    input_data: Dict[str, Any]
    model_type: str = "classifier"

class BehaviorPredictionRequest(BaseModel):
    behavior_type: str
    input_data: Dict[str, Any]
    prediction_horizon: str = "immediate"

class AnomalyDetectionRequest(BaseModel):
    anomaly_type: str
    data: List[Dict[str, Any]]

class ModelTrainingRequest(BaseModel):
    pattern_type: str
    training_data: List[Dict[str, Any]]
    target_column: str
    model_type: str = "classifier"

class BehaviorModelTrainingRequest(BaseModel):
    behavior_type: str
    training_data: List[Dict[str, Any]]
    target_column: str
    prediction_horizon: str = "immediate"

# Dependency to get ML components
def get_ml_components():
    from engines.ml.pattern_analyzer import get_pattern_analyzer, PatternType, LogLevel
    from engines.ml.behavior_predictor import get_behavior_predictor, BehaviorType, PredictionHorizon
    from engines.ml.anomaly_detector import get_anomaly_detector, AnomalyType, AnomalySeverity
    return get_pattern_analyzer(), get_behavior_predictor(), get_anomaly_detector(), PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity

@router.post("/predict")
async def make_prediction(
    request: MLPredictionRequest,
    ml_components = Depends(get_ml_components)
):
    """Make a prediction using trained model"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Convert pattern type string to enum
        try:
            pattern_type = PatternType(request.pattern_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid pattern type: {request.pattern_type}")
        
        # Make prediction
        result = pattern_analyzer.predict(
            pattern_type=pattern_type,
            input_data=request.input_data,
            model_type=request.model_type
        )
        
        return JSONResponse(content={
            "success": True,
            "prediction": {
                "prediction_id": result.prediction_id,
                "prediction": result.prediction,
                "confidence": result.confidence,
                "probability": result.probability,
                "timestamp": result.timestamp.isoformat(),
                "metadata": result.metadata
            }
        })
        
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to make prediction")

@router.post("/behavior/predict")
async def predict_behavior(
    request: BehaviorPredictionRequest,
    ml_components = Depends(get_ml_components)
):
    """Predict behavior using trained model"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Convert behavior type and horizon to enums
        try:
            behavior_type = BehaviorType(request.behavior_type)
            prediction_horizon = PredictionHorizon(request.prediction_horizon)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
        
        # Make behavior prediction
        result = behavior_predictor.predict_behavior(
            behavior_type=behavior_type,
            input_data=request.input_data,
            prediction_horizon=prediction_horizon
        )
        
        return JSONResponse(content={
            "success": True,
            "prediction": {
                "prediction_id": result.prediction_id,
                "behavior_type": result.behavior_type.value,
                "prediction_horizon": result.prediction_horizon.value,
                "predicted_value": result.predicted_value,
                "confidence": result.confidence,
                "probability_distribution": result.probability_distribution,
                "feature_importance": result.feature_importance,
                "timestamp": result.timestamp.isoformat(),
                "metadata": result.metadata
            }
        })
        
    except Exception as e:
        logger.error(f"Error predicting behavior: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict behavior")

@router.post("/anomaly/detect")
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    ml_components = Depends(get_ml_components)
):
    """Detect anomalies in data"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Convert anomaly type to enum
        try:
            anomaly_type = AnomalyType(request.anomaly_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid anomaly type: {request.anomaly_type}")
        
        # Detect anomalies
        anomalies = anomaly_detector.detect_anomalies(
            data=request.data,
            anomaly_type=anomaly_type
        )
        
        # Convert anomalies to response format
        anomalies_data = []
        for anomaly in anomalies:
            anomalies_data.append({
                "anomaly_id": anomaly.anomaly_id,
                "anomaly_type": anomaly.anomaly_type.value,
                "severity": anomaly.severity.value,
                "score": anomaly.score,
                "confidence": anomaly.confidence,
                "description": anomaly.description,
                "detected_at": anomaly.detected_at.isoformat(),
                "features": anomaly.features,
                "context": anomaly.context,
                "recommendations": anomaly.recommendations,
                "metadata": anomaly.metadata
            })
        
        return JSONResponse(content={
            "success": True,
            "anomalies": anomalies_data,
            "total_detected": len(anomalies_data)
        })
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect anomalies")

@router.post("/train")
async def train_model(
    request: ModelTrainingRequest,
    ml_components = Depends(get_ml_components)
):
    """Train a machine learning model"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Convert pattern type to enum
        try:
            pattern_type = PatternType(request.pattern_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid pattern type: {request.pattern_type}")
        
        # Train model
        model = pattern_analyzer.train_model(
            pattern_type=pattern_type,
            training_data=request.training_data,
            target_column=request.target_column
        )
        
        return JSONResponse(content={
            "success": True,
            "model": {
                "model_id": model.model_id,
                "model_type": model.model_type,
                "pattern_type": model.pattern_type.value,
                "version": model.version,
                "accuracy": model.accuracy,
                "precision": model.precision,
                "recall": model.recall,
                "f1_score": model.f1_score,
                "created_at": model.created_at.isoformat(),
                "last_trained": model.last_trained.isoformat(),
                "features": model.features,
                "hyperparameters": model.hyperparameters
            }
        })
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail="Failed to train model")

@router.post("/behavior/train")
async def train_behavior_model(
    request: BehaviorModelTrainingRequest,
    ml_components = Depends(get_ml_components)
):
    """Train a behavior prediction model"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Convert behavior type and horizon to enums
        try:
            behavior_type = BehaviorType(request.behavior_type)
            prediction_horizon = PredictionHorizon(request.prediction_horizon)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
        
        # Train behavior model
        results = behavior_predictor.train_behavior_model(
            behavior_type=behavior_type,
            training_data=request.training_data,
            target_column=request.target_column,
            prediction_horizon=prediction_horizon
        )
        
        return JSONResponse(content={
            "success": True,
            "model": results
        })
        
    except Exception as e:
        logger.error(f"Error training behavior model: {e}")
        raise HTTPException(status_code=500, detail="Failed to train behavior model")

@router.post("/patterns/analyze")
async def analyze_patterns(
    pattern_type: str = Body(..., description="Pattern type to analyze"),
    data: List[Dict[str, Any]] = Body(..., description="Data to analyze"),
    ml_components = Depends(get_ml_components)
):
    """Analyze patterns in data"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Convert pattern type to enum
        try:
            pattern_type_enum = PatternType(pattern_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid pattern type: {pattern_type}")
        
        # Analyze patterns
        results = pattern_analyzer.analyze_patterns(
            data=data,
            pattern_type=pattern_type_enum
        )
        
        return JSONResponse(content={
            "success": True,
            "analysis": results
        })
        
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze patterns")

@router.post("/behavior/patterns")
async def analyze_behavior_patterns(
    behavior_type: str = Body(..., description="Behavior type to analyze"),
    data: List[Dict[str, Any]] = Body(..., description="Data to analyze"),
    ml_components = Depends(get_ml_components)
):
    """Analyze behavior patterns in data"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Convert behavior type to enum
        try:
            behavior_type_enum = BehaviorType(behavior_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid behavior type: {behavior_type}")
        
        # Analyze behavior patterns
        patterns = behavior_predictor.analyze_behavior_patterns(
            behavior_type=behavior_type_enum,
            data=data
        )
        
        # Convert patterns to response format
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                "pattern_id": pattern.pattern_id,
                "behavior_type": pattern.behavior_type.value,
                "pattern_name": pattern.pattern_name,
                "description": pattern.description,
                "frequency": pattern.frequency,
                "confidence": pattern.confidence,
                "conditions": pattern.conditions,
                "outcomes": pattern.outcomes,
                "created_at": pattern.created_at.isoformat(),
                "last_seen": pattern.last_seen.isoformat()
            })
        
        return JSONResponse(content={
            "success": True,
            "patterns": patterns_data,
            "total_patterns": len(patterns_data)
        })
        
    except Exception as e:
        logger.error(f"Error analyzing behavior patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze behavior patterns")

@router.get("/models")
async def list_models(
    pattern_type: str = Query(None, description="Filter by pattern type"),
    model_type: str = Query(None, description="Filter by model type"),
    ml_components = Depends(get_ml_components)
):
    """List available models"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Get models from pattern analyzer
        models = []
        
        # Add pattern analyzer models
        for pattern_type_enum in PatternType:
            if pattern_type and pattern_type_enum.value != pattern_type:
                continue
            
            for model_type_name, model in pattern_analyzer.models[pattern_type_enum].items():
                if model_type and model_type_name != model_type:
                    continue
                
                models.append({
                    "model_id": f"pattern_{pattern_type_enum.value}_{model_type_name}",
                    "pattern_type": pattern_type_enum.value,
                    "model_type": model_type_name,
                    "status": "available",
                    "description": f"{pattern_type_enum.value} {model_type_name} model"
                })
        
        # Add behavior predictor models
        for behavior_type_enum in BehaviorType:
            for horizon_enum in PredictionHorizon:
                models.append({
                    "model_id": f"behavior_{behavior_type_enum.value}_{horizon_enum.value}",
                    "pattern_type": "behavior_prediction",
                    "model_type": "behavior",
                    "behavior_type": behavior_type_enum.value,
                    "prediction_horizon": horizon_enum.value,
                    "status": "available",
                    "description": f"{behavior_type_enum.value} behavior prediction for {horizon_enum.value}"
                })
        
        # Add anomaly detector models
        for anomaly_type_enum in AnomalyType:
            for detector_name in anomaly_detector.detectors[anomaly_type_enum].keys():
                models.append({
                    "model_id": f"anomaly_{anomaly_type_enum.value}_{detector_name}",
                    "pattern_type": "anomaly_detection",
                    "model_type": "anomaly_detector",
                    "anomaly_type": anomaly_type_enum.value,
                    "detector_name": detector_name,
                    "status": "available",
                    "description": f"{anomaly_type_enum.value} anomaly detection using {detector_name}"
                })
        
        return JSONResponse(content={
            "success": True,
            "models": models,
            "total_models": len(models)
        })
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")

@router.get("/health")
async def ml_health_check(ml_components = Depends(get_ml_components)):
    """Check ML system health"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Check component availability
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "pattern_analyzer": "available",
                "behavior_predictor": "available",
                "anomaly_detector": "available"
            },
            "models": {
                "pattern_types": len(PatternType),
                "behavior_types": len(BehaviorType),
                "anomaly_types": len(AnomalyType),
                "total_models": sum(len(pattern_analyzer.models[pt]) for pt in PatternType) + 
                              sum(len(behavior_predictor.models[bt]) for bt in BehaviorType) + 
                              sum(len(anomaly_detector.detectors[at]) for at in AnomalyType)
            },
            "cache": {
                "prediction_cache_size": len(behavior_predictor.prediction_cache),
                "anomaly_cache_size": len(anomaly_detector.anomaly_cache)
            }
        }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Error checking ML health: {e}")
        return JSONResponse(content={
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }, status_code=500)

@router.get("/statistics")
async def get_ml_statistics(
    days: int = Query(30, description="Number of days to analyze"),
    ml_components = Depends(get_ml_components)
):
    """Get ML system statistics"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Calculate statistics
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        statistics = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "models": {
                "total_pattern_models": sum(len(pattern_analyzer.models[pt]) for pt in PatternType),
                "total_behavior_models": sum(len(behavior_predictor.models[bt]) for bt in BehaviorType),
                "total_anomaly_detectors": sum(len(anomaly_detector.detectors[at]) for at in AnomalyType)
            },
            "predictions": {
                "cache_hits": len(behavior_predictor.prediction_cache),
                "cache_ttl": behavior_predictor.cache_ttl
            },
            "anomalies": {
                "cache_hits": len(anomaly_detector.anomaly_cache),
                "cache_ttl": anomaly_detector.cache_ttl
            },
            "data_processing": {
                "historical_data_size": sum(len(behavior_predictor.historical_data[key]) for key in behavior_predictor.historical_data),
                "max_history_size": behavior_predictor.max_history_size
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "statistics": statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting ML statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ML statistics")

@router.post("/clear-cache")
async def clear_ml_cache(ml_components = Depends(get_ml_components)):
    """Clear ML system cache"""
    try:
        pattern_analyzer, behavior_predictor, anomaly_detector, PatternType, LogLevel, BehaviorType, PredictionHorizon, AnomalyType, AnomalySeverity = ml_components
        
        # Clear caches
        behavior_predictor.prediction_cache.clear()
        anomaly_detector.anomaly_cache.clear()
        
        return JSONResponse(content={
            "success": True,
            "message": "ML cache cleared successfully"
        })
        
    except Exception as e:
        logger.error(f"Error clearing ML cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear ML cache")
