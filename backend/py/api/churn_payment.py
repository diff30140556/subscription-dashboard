#!/usr/bin/env python3
"""
FastAPI router for churn by payment method endpoints.
Provides REST API for analyzing churn rates grouped by payment method.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import asyncpg
import logging

from ..core.db import get_db_connection
from ..analysis.churn_by_payment import (
    compute_churn_by_payment,
    compute_churn_by_payment_with_metadata,
    get_payment_summary_stats,
    compare_payment_vs_contract_churn
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/api/churn",
    tags=["churn-analysis"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/payment", 
            response_model=Dict[str, List[Dict[str, Any]]],
            summary="Get Churn Rate by Payment Method",
            description="Retrieve churn rates grouped by payment method, sorted by churn rate descending.")
async def get_churn_by_payment(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get churn rates grouped by payment method.
    
    Analyzes customer churn patterns by payment method:
    - Groups customers by payment method (Electronic check, Mailed check, Bank transfer, Credit card)
    - Handles NULL/empty payment methods as "Unknown"
    - Calculates churn rate = churned_customers / total_customers
    - Returns results sorted by churn_rate DESC
    - Rounds churn_rate to 4 decimal places
    
    Returns:
        JSON response with churn_rate_by_payment array
        
    Raises:
        HTTPException: 500 for database or computation errors
        
    Example Response:
        {
            "churn_rate_by_payment": [
                {"key": "Electronic check", "churn_rate": 0.4522, "n": 2365},
                {"key": "Mailed check", "churn_rate": 0.1916, "n": 1612},
                {"key": "Bank transfer (automatic)", "churn_rate": 0.1680, "n": 1544},
                {"key": "Credit card (automatic)", "churn_rate": 0.1522, "n": 1522}
            ]
        }
    """
    try:
        logger.info("Computing churn rates by payment method")
        
        # Compute churn analysis using the provided database connection
        payment_analysis = await compute_churn_by_payment(conn)
        
        logger.info(f"Payment method analysis computed successfully: {len(payment_analysis)} payment methods found")
        
        # Format response according to required schema
        response = {
            "churn_rate_by_payment": payment_analysis
        }
        
        return response
        
    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_churn_by_payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Computation error in get_churn_by_payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_churn_by_payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/payment/metadata",
            response_model=Dict[str, Any],
            summary="Get Churn by Payment Method with Metadata",
            description="Get churn rates by payment method with additional metadata and computation details.")
async def get_churn_by_payment_with_metadata(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get churn rates by payment method with additional metadata.
    
    Includes the same payment method analysis as /api/churn/payment but adds metadata about
    the computation including timestamp, total customers, and payment method count.
    
    Returns:
        JSON response with payment method analysis and metadata
        
    Example Response:
        {
            "churn_rate_by_payment": [
                {"key": "Electronic check", "churn_rate": 0.4522, "n": 2365}
            ],
            "metadata": {
                "total_customers": 7043,
                "total_payment_methods": 4,
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        logger.info("Computing churn rates by payment method with metadata")
        
        result = await compute_churn_by_payment_with_metadata(conn)
        
        logger.info(f"Payment method analysis with metadata computed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_churn_by_payment_with_metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute churn by payment method with metadata: {str(e)}"
        )


@router.get("/payment/summary",
            response_model=Dict[str, Any],
            summary="Get Payment Method Churn Summary Statistics",
            description="Get summary statistics for payment method churn analysis including highest/lowest rates.")
async def get_payment_churn_summary(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get summary statistics for payment method churn analysis.
    
    Provides insights like:
    - Payment method with highest churn rate
    - Payment method with lowest churn rate  
    - Weighted average churn rate across all payment methods
    - Total number of payment methods
    
    Returns:
        JSON response with payment method summary statistics
        
    Example Response:
        {
            "highest_churn_payment": {"key": "Electronic check", "churn_rate": 0.4522, "n": 2365},
            "lowest_churn_payment": {"key": "Credit card (automatic)", "churn_rate": 0.1522, "n": 1522},
            "average_churn_rate": 0.2654,
            "total_payment_methods": 4
        }
    """
    try:
        logger.info("Computing payment method churn summary statistics")
        
        summary_stats = await get_payment_summary_stats(conn)
        
        logger.info("Payment method summary statistics computed successfully")
        
        return summary_stats
        
    except Exception as e:
        logger.error(f"Error in get_payment_churn_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute payment method churn summary: {str(e)}"
        )


@router.get("/payment/compare",
            response_model=Dict[str, Any],
            summary="Compare Payment vs Contract Churn Analysis",
            description="Compare churn rate patterns between payment methods and contract types.")
async def get_payment_vs_contract_comparison(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Compare churn patterns between payment methods and contract types.
    
    Provides comparative analysis to understand which segmentation approach
    shows greater variation in churn rates and other insights.
    
    Returns:
        JSON response with comparative analysis
        
    Example Response:
        {
            "payment_method_analysis": {
                "highest_rate": 0.4522,
                "lowest_rate": 0.1522,
                "rate_spread": 0.3000,
                "method_count": 4
            },
            "contract_analysis": {
                "highest_rate": 0.4273,
                "lowest_rate": 0.0283,
                "rate_spread": 0.3990,
                "contract_count": 3
            },
            "comparison": {
                "higher_spread_segment": "contract",
                "payment_vs_contract_spread_ratio": 0.7519
            }
        }
    """
    try:
        logger.info("Computing payment vs contract churn comparison")
        
        comparison_result = await compare_payment_vs_contract_churn(conn)
        
        logger.info("Payment vs contract comparison computed successfully")
        
        return comparison_result
        
    except Exception as e:
        logger.error(f"Error in get_payment_vs_contract_comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute payment vs contract comparison: {str(e)}"
        )


@router.get("/payment/health",
            response_model=Dict[str, Any],
            summary="Payment Method Analysis Health Check", 
            description="Check if payment method churn analysis is working properly.")
async def payment_health_check(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Health check endpoint for payment method churn analysis functionality.
    
    Tests database connectivity and payment method analysis computation.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "churn-by-payment",
            "database_connected": true,
            "can_analyze_payments": true,
            "sample_payment_count": 4
        }
    """
    try:
        # Test basic database connectivity
        result = await conn.fetchval("SELECT 1")
        db_connected = result == 1
        
        # Test if we can access payment method data
        payment_count = await conn.fetchval("""
            SELECT COUNT(DISTINCT 
                CASE 
                    WHEN "PaymentMethod" IS NULL OR TRIM("PaymentMethod") = '' THEN 'Unknown'
                    ELSE "PaymentMethod"
                END
            )
            FROM churn_customers
        """)
        
        can_analyze = db_connected and payment_count is not None
        
        status = "healthy" if can_analyze else "degraded"
        
        return {
            "status": status,
            "service": "churn-by-payment",
            "database_connected": db_connected,
            "can_analyze_payments": can_analyze,
            "sample_payment_count": int(payment_count) if payment_count else 0
        }
        
    except Exception as e:
        logger.error(f"Payment method health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "churn-by-payment",
            "database_connected": False,
            "can_analyze_payments": False,
            "error": str(e)
        }