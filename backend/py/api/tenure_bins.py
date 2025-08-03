#!/usr/bin/env python3
"""
FastAPI router for tenure bins endpoints.
Provides REST API for analyzing tenure distribution of churned customers.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import asyncpg
import logging

from ..core.db import get_db_connection
from ..analysis.tenure_bins import (
    compute_tenure_bins,
    compute_tenure_bins_with_metadata,
    get_tenure_summary_stats,
    get_tenure_distribution_insights
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/api/tenure",
    tags=["tenure-analysis"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/bins", 
            response_model=Dict[str, List[Dict[str, Any]]],
            summary="Get Tenure Distribution for Churned Customers",
            description="Retrieve tenure distribution of churned customers in fixed bins: 0–3, 4–6, 7–12, 13–24, 25+ months.")
async def get_tenure_bins(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get tenure distribution for churned customers in fixed bins.
    
    Analyzes only customers who have churned (Churn = 'Yes') and bins their tenure
    into fixed ranges in the specified order:
    - 0–3 months
    - 4–6 months  
    - 7–12 months
    - 13–24 months
    - 25+ months
    
    Percentages are calculated as: count / total_churned_customers
    
    Returns:
        JSON response with tenure_ranges array in fixed order
        
    Raises:
        HTTPException: 500 for database or computation errors
        
    Example Response:
        {
            "tenure_ranges": [
                {"range": "0–3", "count": 245, "pct": 0.1311},
                {"range": "4–6", "count": 178, "pct": 0.0952},
                {"range": "7–12", "count": 342, "pct": 0.1830},
                {"range": "13–24", "count": 287, "pct": 0.1536},
                {"range": "25+", "count": 817, "pct": 0.4371}
            ]
        }
    """
    try:
        logger.info("Computing tenure bins for churned customers")
        
        # Compute tenure bins analysis using the provided database connection
        tenure_analysis = await compute_tenure_bins(conn)
        
        logger.info(f"Tenure bins analysis computed successfully: {len(tenure_analysis)} bins found")
        
        # Format response according to required schema
        response = {
            "tenure_ranges": tenure_analysis
        }
        
        return response
        
    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_tenure_bins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Computation error in get_tenure_bins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_tenure_bins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/bins/metadata",
            response_model=Dict[str, Any],
            summary="Get Tenure Bins with Metadata",
            description="Get tenure distribution with additional metadata and computation details.")
async def get_tenure_bins_with_metadata(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get tenure bins with additional metadata.
    
    Includes the same tenure bins analysis as /api/tenure/bins but adds metadata about
    the computation including timestamp, total churned customers, and bins definition.
    
    Returns:
        JSON response with tenure bins analysis and metadata
        
    Example Response:
        {
            "tenure_ranges": [
                {"range": "0–3", "count": 245, "pct": 0.1311}
            ],
            "metadata": {
                "total_churned_customers": 1869,
                "bins_definition": {
                    "edges": [0, 3, 6, 12, 24, 999],
                    "labels": ["0–3", "4–6", "7–12", "13–24", "25+"],
                    "order": ["0–3", "4–6", "7–12", "13–24", "25+"]
                },
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        logger.info("Computing tenure bins with metadata")
        
        result = await compute_tenure_bins_with_metadata(conn)
        
        logger.info("Tenure bins analysis with metadata computed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_tenure_bins_with_metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute tenure bins with metadata: {str(e)}"
        )


@router.get("/bins/summary",
            response_model=Dict[str, Any],
            summary="Get Tenure Bins Summary Statistics",
            description="Get summary statistics for tenure bins analysis including highest/lowest ranges.")
async def get_tenure_bins_summary(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get summary statistics for tenure bins analysis.
    
    Provides insights like:
    - Tenure range with highest churn count
    - Tenure range with lowest churn count
    - Most common tenure range (highest percentage)
    - Total churned customers analyzed
    
    Returns:
        JSON response with tenure bins summary statistics
        
    Example Response:
        {
            "highest_count_range": {"range": "25+", "count": 817, "pct": 0.4371},
            "lowest_count_range": {"range": "4–6", "count": 178, "pct": 0.0952},
            "most_common_tenure_range": {"range": "25+", "count": 817, "pct": 0.4371},
            "total_churned_analyzed": 1869
        }
    """
    try:
        logger.info("Computing tenure bins summary statistics")
        
        summary_stats = await get_tenure_summary_stats(conn)
        
        logger.info("Tenure bins summary statistics computed successfully")
        
        return summary_stats
        
    except Exception as e:
        logger.error(f"Error in get_tenure_bins_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute tenure bins summary: {str(e)}"
        )


@router.get("/bins/insights",
            response_model=Dict[str, Any],
            summary="Get Tenure Distribution Insights",
            description="Get analytical insights about tenure distribution patterns for churned customers.")
async def get_tenure_distribution_insights_endpoint(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get analytical insights about tenure distribution patterns.
    
    Provides business insights like:
    - Early vs late tenure churn analysis (0-12 months vs 13+ months)
    - Dominant tenure range identification
    - Percentage breakdowns and interpretations
    
    Returns:
        JSON response with tenure distribution insights
        
    Example Response:
        {
            "insights": [
                {
                    "type": "early_vs_late_churn",
                    "early_churn_pct": 65.1,
                    "late_churn_pct": 34.9,
                    "insight": "65.1% of churned customers left within first year, 34.9% after first year"
                },
                {
                    "type": "dominant_range",
                    "range": "25+",
                    "percentage": 43.71,
                    "insight": "Most churned customers (43.7%) are in the 25+ months tenure range"
                }
            ],
            "tenure_distribution": [...]
        }
    """
    try:
        logger.info("Computing tenure distribution insights")
        
        insights = await get_tenure_distribution_insights(conn)
        
        logger.info("Tenure distribution insights computed successfully")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error in get_tenure_distribution_insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute tenure distribution insights: {str(e)}"
        )


@router.get("/bins/health",
            response_model=Dict[str, Any],
            summary="Tenure Bins Analysis Health Check",
            description="Check if tenure bins analysis is working properly.")
async def tenure_bins_health_check(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Health check endpoint for tenure bins analysis functionality.
    
    Tests database connectivity and tenure bins computation.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "tenure-bins",
            "database_connected": true,
            "can_analyze_tenure": true,
            "sample_churned_count": 1869
        }
    """
    try:
        # Test basic database connectivity
        result = await conn.fetchval("SELECT 1")
        db_connected = result == 1
        
        # Test if we can access tenure data for churned customers
        churned_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM churn_customers
            WHERE "Churn" = 'Yes' AND tenure IS NOT NULL
        """)
        
        can_analyze = db_connected and churned_count is not None
        
        status = "healthy" if can_analyze else "degraded"
        
        return {
            "status": status,
            "service": "tenure-bins",
            "database_connected": db_connected,
            "can_analyze_tenure": can_analyze,
            "sample_churned_count": int(churned_count) if churned_count else 0
        }
        
    except Exception as e:
        logger.error(f"Tenure bins health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "tenure-bins",
            "database_connected": False,
            "can_analyze_tenure": False,
            "error": str(e)
        }