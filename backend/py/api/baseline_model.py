#!/usr/bin/env python3
"""
FastAPI router for baseline churn prediction model endpoints.
Provides REST API for training, loading, and evaluating the baseline ML model.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncpg
import logging
import os

from ..core.db import get_db_connection
from ..analysis.baseline_model import (
    load_or_train,
    train_and_save,
    get_model_info
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/api/model",
    tags=["ml-model"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/baseline", 
            response_model=Dict[str, Any],
            summary="Get Baseline Churn Prediction Model",
            description="Load pre-trained baseline model or train new one if it doesn't exist. Returns model performance metrics and top features.")
async def get_baseline_model(
    conn: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """
    Get baseline churn prediction model (Logistic Regression).
    
    This endpoint loads a pre-trained model from cache if available, otherwise
    trains a new model and caches it for future use.
    
    Model Features:
    - Numeric: tenure, MonthlyCharges (missing = median)
    - Categorical: Contract, PaymentMethod (one-hot encoded, missing = "Unknown")  
    - Boolean: OnlineSecurity, TechSupport (Yes=1, No/NULL=0)
    - Target: churn (Yes=1, No=0)
    
    Model Configuration:
    - Algorithm: LogisticRegression(solver="liblinear", class_weight="balanced")
    - Split: 80% train, 20% test (stratified, random_state=42)
    - Evaluation: ROC AUC score
    - Feature Selection: Top 10 by absolute coefficient weight
    
    Returns:
        JSON response with model performance and top features
        
    Raises:
        HTTPException: 500 for training errors or missing dependencies
        
    Example Response:
        {
            "status": "loaded",
            "message": "Model loaded from cache (trained: 2024-01-15T10:30:00Z)",
            "model": {
                "auc": 0.8456,
                "top_features": [
                    {"feature": "Contract_Month-to-month", "weight": 1.2345},
                    {"feature": "tenure", "weight": -0.9876},
                    {"feature": "OnlineSecurity", "weight": -0.7654},
                    ...
                ]
            },
            "training_info": {
                "total_samples": 7043,
                "total_features": 12,
                "train_samples": 5634,
                "test_samples": 1409,
                "positive_rate": 0.2654
            }
        }
    """
    try:
        logger.info("Loading or training baseline churn prediction model")
        
        # Get model directory path (relative to project root)
        model_dir = os.path.join(os.getcwd(), "models")
        
        # Load existing model or train new one
        result = await load_or_train(conn, model_dir)
        
        logger.info(f"Baseline model {result['status']}: AUC = {result['model']['auc']}")
        
        return result
        
    except ImportError as e:
        logger.error(f"Missing ML dependencies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Machine learning dependencies not installed. Please install scikit-learn: pip install scikit-learn"
        )
    except ValueError as e:
        logger.error(f"Model training/loading error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_baseline_model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/baseline/retrain",
             response_model=Dict[str, Any],
             summary="Retrain Baseline Model",
             description="Force retrain the baseline model with fresh data and save to cache.")
async def retrain_baseline_model(
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """
    Force retrain the baseline churn prediction model.
    
    This endpoint forces retraining of the model with the latest data,
    overwriting any existing cached model.
    
    Returns:
        JSON response with new model performance metrics
        
    Example Response:
        {
            "status": "success",
            "message": "Model trained and saved successfully",
            "model": {
                "auc": 0.8456,
                "top_features": [...]
            },
            "training_info": {...}
        }
    """
    try:
        logger.info("Forcing retrain of baseline churn prediction model")
        
        # Get model directory path
        model_dir = os.path.join(os.getcwd(), "models")
        
        # Force retrain model
        result = await train_and_save(conn, model_dir)
        
        logger.info(f"Model retrained successfully: AUC = {result['model']['auc']}")
        
        return result
        
    except ImportError as e:
        logger.error(f"Missing ML dependencies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Machine learning dependencies not installed. Please install scikit-learn"
        )
    except ValueError as e:
        logger.error(f"Model training error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in retrain_baseline_model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/baseline/info",
            response_model=Dict[str, Any],
            summary="Get Model Information",
            description="Get information about the cached baseline model without loading it.")
async def get_baseline_model_info() -> Dict[str, Any]:
    """
    Get information about the cached baseline model.
    
    Returns basic information about the saved model without actually loading it,
    which is faster for checking model status.
    
    Returns:
        JSON response with model information
        
    Example Response:
        {
            "model_exists": true,
            "training_date": "2024-01-15T10:30:00Z",
            "model_type": "LogisticRegression",
            "auc": 0.8456,
            "total_features": 12
        }
    """
    try:
        logger.info("Getting baseline model information")
        
        # Get model directory path
        model_dir = os.path.join(os.getcwd(), "models")
        
        # Get model info
        info = await get_model_info(model_dir)
        
        logger.info(f"Model info retrieved: exists = {info.get('model_exists', False)}")
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model information: {str(e)}"
        )


@router.get("/baseline/health",
            response_model=Dict[str, Any],
            summary="Model API Health Check",
            description="Check if the model API and ML dependencies are working properly.")
async def baseline_model_health_check(
    conn: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """
    Health check endpoint for baseline model functionality.
    
    Tests database connectivity, ML dependencies, and data availability.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "baseline-model",
            "database_connected": true,
            "ml_dependencies": true,
            "data_available": true,
            "model_cached": true,
            "sample_count": 7043
        }
    """
    try:
        # Test basic database connectivity
        db_result = await conn.fetchval("SELECT 1")
        db_connected = db_result == 1
        
        # Test ML dependencies
        try:
            import sklearn
            ml_available = True
        except ImportError:
            ml_available = False
        
        # Test data availability
        try:
            data_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM churn_customers
                WHERE tenure IS NOT NULL 
                  AND "MonthlyCharges" IS NOT NULL
            """)
            data_available = data_count is not None and data_count > 0
        except Exception:
            data_available = False
            data_count = 0
        
        # Check if model is cached
        try:
            model_dir = os.path.join(os.getcwd(), "models")
            info = await get_model_info(model_dir)
            model_cached = info.get("model_exists", False)
        except Exception:
            model_cached = False
        
        # Determine overall status
        can_function = db_connected and ml_available and data_available
        status = "healthy" if can_function else "degraded"
        
        return {
            "status": status,
            "service": "baseline-model",
            "database_connected": db_connected,
            "ml_dependencies": ml_available,
            "data_available": data_available,
            "model_cached": model_cached,
            "sample_count": int(data_count) if data_count else 0
        }
        
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "baseline-model",
            "database_connected": False,
            "ml_dependencies": False,
            "data_available": False,
            "model_cached": False,
            "error": str(e)
        }


@router.get("/baseline/features",
            response_model=Dict[str, Any],
            summary="Get Model Feature Information",
            description="Get detailed information about features used in the baseline model.")
async def get_baseline_features() -> Dict[str, Any]:
    """
    Get information about features used in the baseline model.
    
    Returns:
        JSON response with feature configuration
        
    Example Response:
        {
            "feature_groups": {
                "numeric": ["tenure", "MonthlyCharges"],
                "categorical": ["Contract", "PaymentMethod"], 
                "boolean": ["OnlineSecurity", "TechSupport"]
            },
            "preprocessing": {
                "numeric_imputation": "median",
                "categorical_imputation": "Unknown",
                "boolean_imputation": 0,
                "categorical_encoding": "one_hot_drop_first"
            },
            "model_config": {
                "algorithm": "LogisticRegression",
                "solver": "liblinear",
                "class_weight": "balanced",
                "test_size": 0.2,
                "random_state": 42
            }
        }
    """
    try:
        from ..analysis.baseline_model import ChurnModelTrainer
        
        trainer = ChurnModelTrainer()
        
        return {
            "feature_groups": {
                "numeric": trainer.numeric_features,
                "categorical": trainer.categorical_features,
                "boolean": trainer.boolean_features
            },
            "preprocessing": {
                "numeric_imputation": "median",
                "categorical_imputation": "Unknown", 
                "boolean_imputation": 0,
                "categorical_encoding": "one_hot_drop_first"
            },
            "model_config": {
                "algorithm": "LogisticRegression",
                **trainer.model_params,
                "test_size": trainer.test_size
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting feature info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feature information: {str(e)}"
        )