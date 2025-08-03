#!/usr/bin/env python3
"""
FastAPI router for service features churn analysis endpoints.
Provides REST API for analyzing churn rates by service add-ons and features.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
import asyncpg
import logging

from ..core.db import get_db_connection
from ..analysis.feature_churn import (
    compute_feature_churn,
    compute_feature_churn_with_metadata,
    get_feature_churn_summary,
    get_allowed_features,
    DEFAULT_FEATURES
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/api/features",
    tags=["features-analysis"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/churn", 
            response_model=Dict[str, Any],
            summary="Get Churn Rates by Service Features",
            description="Analyze churn rates by service add-ons like OnlineSecurity, TechSupport. Supports query parameter ?names=OnlineSecurity,TechSupport")
async def get_feature_churn(
    names: Optional[str] = Query(None, description="Comma-separated list of feature names (e.g., 'OnlineSecurity,TechSupport'). If not provided, defaults to OnlineSecurity and TechSupport."),
    conn: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """
    Get churn rates by service features/add-ons.
    
    Analyzes churn rates for different service features, with each feature showing
    churn rates for "Yes" and "No" values. NULL values are treated as "No".
    
    Query Parameters:
        names (optional): Comma-separated feature names (e.g., "OnlineSecurity,TechSupport")
                         If not provided, defaults to ["OnlineSecurity", "TechSupport"]
    
    Returns:
        JSON response with churn rates by feature in fixed Yes/No order
        
    Raises:
        HTTPException: 400 for invalid feature names, 500 for database/computation errors
        
    Example Response:
        {
            "churn_rate_by_feature": {
                "OnlineSecurity": [
                    {"key": "Yes", "churn_rate": 0.1500, "n": 200},
                    {"key": "No", "churn_rate": 0.3200, "n": 1500}
                ],
                "TechSupport": [
                    {"key": "Yes", "churn_rate": 0.1200, "n": 180},
                    {"key": "No", "churn_rate": 0.2800, "n": 1520}
                ]
            }
        }
    """
    try:
        logger.info(f"Computing feature churn analysis with names parameter: {names}")
        
        # Parse feature names from query parameter
        if names:
            # Split by comma and strip whitespace
            features_list = [name.strip() for name in names.split(",") if name.strip()]
        else:
            # Use default features
            features_list = DEFAULT_FEATURES
        
        logger.info(f"Analyzing features: {features_list}")
        
        # Compute feature churn analysis using the provided database connection
        churn_analysis = await compute_feature_churn(conn, features_list)
        
        logger.info(f"Feature churn analysis computed successfully for {len(churn_analysis['churn_rate_by_feature'])} features")
        
        return churn_analysis
        
    except ValueError as e:
        logger.error(f"Validation error in get_feature_churn: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feature names: {str(e)}"
        )
    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_feature_churn: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_feature_churn: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/churn/metadata",
            response_model=Dict[str, Any],
            summary="Get Feature Churn Analysis with Metadata",
            description="Get churn rates by features with additional metadata and computation details.")
async def get_feature_churn_with_metadata(
    names: Optional[str] = Query(None, description="Comma-separated list of feature names"),
    conn: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """
    Get feature churn analysis with additional metadata.
    
    Includes the same churn analysis as /api/features/churn but adds metadata about
    the computation including timestamp, analyzed features, and available features.
    
    Returns:
        JSON response with feature churn analysis and metadata
        
    Example Response:
        {
            "churn_rate_by_feature": {...},
            "metadata": {
                "analyzed_features": ["OnlineSecurity", "TechSupport"],
                "total_feature_combinations": 3400,
                "available_features": ["OnlineSecurity", "TechSupport", "OnlineBackup", ...],
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        logger.info("Computing feature churn analysis with metadata")
        
        # Parse feature names
        if names:
            features_list = [name.strip() for name in names.split(",") if name.strip()]
        else:
            features_list = DEFAULT_FEATURES
        
        result = await compute_feature_churn_with_metadata(conn, features_list)
        
        logger.info("Feature churn analysis with metadata computed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_feature_churn_with_metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute feature churn with metadata: {str(e)}"
        )


@router.get("/churn/summary",
            response_model=Dict[str, Any],
            summary="Get Feature Churn Summary Statistics",
            description="Get summary statistics showing which features have the best/worst impact on customer retention.")
async def get_feature_churn_summary_endpoint(
    names: Optional[str] = Query(None, description="Comma-separated list of feature names"),
    conn: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    """
    Get summary statistics for feature churn analysis.
    
    Provides insights like:
    - Best feature for customer retention (lowest churn when enabled)
    - Worst feature for customer retention
    - Feature impact analysis showing churn reduction for each feature
    
    Returns:
        JSON response with feature churn summary statistics
        
    Example Response:
        {
            "best_feature_for_retention": {
                "feature": "TechSupport",
                "yes_churn_rate": 0.1200,
                "no_churn_rate": 0.2800,
                "churn_reduction": 0.1600,
                "yes_customers": 180,
                "no_customers": 1520
            },
            "worst_feature_for_retention": {...},
            "feature_impact_summary": [...]
        }
    """
    try:
        logger.info("Computing feature churn summary statistics")
        
        # Parse feature names
        if names:
            features_list = [name.strip() for name in names.split(",") if name.strip()]
        else:
            features_list = DEFAULT_FEATURES
        
        summary_stats = await get_feature_churn_summary(conn, features_list)
        
        logger.info("Feature churn summary statistics computed successfully")
        
        return summary_stats
        
    except Exception as e:
        logger.error(f"Error in get_feature_churn_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute feature churn summary: {str(e)}"
        )


@router.get("/available",
            response_model=Dict[str, List[str]],
            summary="Get Available Service Features",
            description="Get list of available service features that can be analyzed.")
async def get_available_features() -> Dict[str, List[str]]:
    """
    Get list of available service features for analysis.
    
    Returns list of feature names that can be used in the ?names parameter
    for the /api/features/churn endpoint.
    
    Returns:
        JSON response with available feature names
        
    Example Response:
        {
            "available_features": [
                "OnlineSecurity",
                "TechSupport", 
                "OnlineBackup",
                "DeviceProtection",
                "StreamingTV",
                "StreamingMovies",
                "InternetService",
                "PhoneService",
                "MultipleLines",
                "PaperlessBilling"
            ],
            "default_features": ["OnlineSecurity", "TechSupport"]
        }
    """
    try:
        logger.info("Getting available features list")
        
        available = get_allowed_features()
        
        return {
            "available_features": available,
            "default_features": DEFAULT_FEATURES
        }
        
    except Exception as e:
        logger.error(f"Error in get_available_features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available features: {str(e)}"
        )


@router.get("/churn/health",
            response_model=Dict[str, Any],
            summary="Feature Churn Analysis Health Check",
            description="Check if feature churn analysis is working properly.")
async def feature_churn_health_check(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Health check endpoint for feature churn analysis functionality.
    
    Tests database connectivity and feature churn computation.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "feature-churn",
            "database_connected": true,
            "can_analyze_features": true,
            "sample_customers_count": 7043,
            "default_features": ["OnlineSecurity", "TechSupport"]
        }
    """
    try:
        # Test basic database connectivity
        result = await conn.fetchval("SELECT 1")
        db_connected = result == 1
        
        # Test if we can access customer data
        customers_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM churn_customers
        """)
        
        # Test if default features exist (basic schema validation)
        feature_test_sql = """
            SELECT COUNT(*) 
            FROM churn_customers 
            WHERE "OnlineSecurity" IS NOT NULL OR "OnlineSecurity" IS NULL
            LIMIT 1
        """
        
        try:
            await conn.fetchval(feature_test_sql)
            can_analyze = True
        except Exception:
            can_analyze = False
        
        can_analyze = can_analyze and db_connected and customers_count is not None
        
        status = "healthy" if can_analyze else "degraded"
        
        return {
            "status": status,
            "service": "feature-churn",
            "database_connected": db_connected,
            "can_analyze_features": can_analyze,
            "sample_customers_count": int(customers_count) if customers_count else 0,
            "default_features": DEFAULT_FEATURES,
            "available_features_count": len(get_allowed_features())
        }
        
    except Exception as e:
        logger.error(f"Feature churn health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "feature-churn",
            "database_connected": False,
            "can_analyze_features": False,
            "error": str(e)
        }