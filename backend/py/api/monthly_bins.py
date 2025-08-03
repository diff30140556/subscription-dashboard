#!/usr/bin/env python3
"""
FastAPI router for monthly charges bins endpoints.
Provides REST API for analyzing monthly charges distribution of churned customers.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import asyncpg
import logging

from ..core.db import get_db_connection
from ..analysis.monthly_bins import (
    compute_monthly_bins,
    compute_monthly_bins_with_metadata,
    get_monthly_summary_stats,
    get_monthly_distribution_insights
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/api/monthly",
    tags=["monthly-analysis"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/bins", 
            response_model=Dict[str, List[Dict[str, Any]]],
            summary="Get Monthly Charges Distribution for Churned Customers",
            description="Retrieve monthly charges distribution of churned customers in fixed bins: 0–35, 36–65, 66–95, 96+.")
async def get_monthly_bins(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get monthly charges distribution for churned customers in fixed bins.
    
    Analyzes only customers who have churned (Churn = 'Yes') and bins their monthly charges
    into fixed ranges in the specified order:
    - 0–35 dollars
    - 36–65 dollars  
    - 66–95 dollars
    - 96+ dollars
    
    Percentages are calculated as: count / total_churned_customers
    
    Returns:
        JSON response with monthly_charge_ranges array in fixed order
        
    Raises:
        HTTPException: 500 for database or computation errors
        
    Example Response:
        {
            "monthly_charge_ranges": [
                {"range": "0–35", "count": 245, "pct": 0.1311},
                {"range": "36–65", "count": 420, "pct": 0.2248},
                {"range": "66–95", "count": 680, "pct": 0.3639},
                {"range": "96+", "count": 524, "pct": 0.2802}
            ]
        }
    """
    try:
        logger.info("Computing monthly bins for churned customers")
        
        # Compute monthly bins analysis using the provided database connection
        monthly_analysis = await compute_monthly_bins(conn)
        
        logger.info(f"Monthly bins analysis computed successfully: {len(monthly_analysis)} bins found")
        
        # Format response according to required schema
        response = {
            "monthly_charge_ranges": monthly_analysis
        }
        
        return response
        
    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_monthly_bins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Computation error in get_monthly_bins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_monthly_bins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/bins/metadata",
            response_model=Dict[str, Any],
            summary="Get Monthly Bins with Metadata",
            description="Get monthly charges distribution with additional metadata and computation details.")
async def get_monthly_bins_with_metadata(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get monthly bins with additional metadata.
    
    Includes the same monthly bins analysis as /api/monthly/bins but adds metadata about
    the computation including timestamp, total churned customers, and bins definition.
    
    Returns:
        JSON response with monthly bins analysis and metadata
        
    Example Response:
        {
            "monthly_charge_ranges": [
                {"range": "0–35", "count": 245, "pct": 0.1311}
            ],
            "metadata": {
                "total_churned_customers": 1869,
                "bins_definition": {
                    "edges": [0, 35, 65, 95, 999],
                    "labels": ["0–35", "36–65", "66–95", "96+"],
                    "order": ["0–35", "36–65", "66–95", "96+"]
                },
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        logger.info("Computing monthly bins with metadata")
        
        result = await compute_monthly_bins_with_metadata(conn)
        
        logger.info("Monthly bins analysis with metadata computed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_monthly_bins_with_metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute monthly bins with metadata: {str(e)}"
        )


@router.get("/bins/summary",
            response_model=Dict[str, Any],
            summary="Get Monthly Bins Summary Statistics",
            description="Get summary statistics for monthly bins analysis including highest/lowest ranges.")
async def get_monthly_bins_summary(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get summary statistics for monthly bins analysis.
    
    Provides insights like:
    - Monthly charge range with highest churn count
    - Monthly charge range with lowest churn count
    - Most common charge range (highest percentage)
    - Total churned customers analyzed
    
    Returns:
        JSON response with monthly bins summary statistics
        
    Example Response:
        {
            "highest_count_range": {"range": "66–95", "count": 680, "pct": 0.3639},
            "lowest_count_range": {"range": "0–35", "count": 245, "pct": 0.1311},
            "most_common_charge_range": {"range": "66–95", "count": 680, "pct": 0.3639},
            "total_churned_analyzed": 1869
        }
    """
    try:
        logger.info("Computing monthly bins summary statistics")
        
        summary_stats = await get_monthly_summary_stats(conn)
        
        logger.info("Monthly bins summary statistics computed successfully")
        
        return summary_stats
        
    except Exception as e:
        logger.error(f"Error in get_monthly_bins_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute monthly bins summary: {str(e)}"
        )


@router.get("/bins/insights",
            response_model=Dict[str, Any],
            summary="Get Monthly Charges Distribution Insights",
            description="Get analytical insights about monthly charges distribution patterns for churned customers.")
async def get_monthly_distribution_insights_endpoint(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get analytical insights about monthly charges distribution patterns.
    
    Provides business insights like:
    - Low vs high charges churn analysis (0-65 vs 66+)
    - Dominant charge range identification
    - Percentage breakdowns and interpretations
    
    Returns:
        JSON response with monthly charges distribution insights
        
    Example Response:
        {
            "insights": [
                {
                    "type": "low_vs_high_charges_churn",
                    "low_charges_pct": 35.6,
                    "high_charges_pct": 64.4,
                    "insight": "35.6% of churned customers have low charges ($0-65), 64.4% have high charges ($66+)"
                },
                {
                    "type": "dominant_range",
                    "range": "66–95",
                    "percentage": 36.39,
                    "insight": "Most churned customers (36.4%) are in the $66–95 monthly charges range"
                }
            ],
            "monthly_charge_distribution": [...]
        }
    """
    try:
        logger.info("Computing monthly charges distribution insights")
        
        insights = await get_monthly_distribution_insights(conn)
        
        logger.info("Monthly charges distribution insights computed successfully")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error in get_monthly_distribution_insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute monthly distribution insights: {str(e)}"
        )


@router.get("/bins/health",
            response_model=Dict[str, Any],
            summary="Monthly Bins Analysis Health Check",
            description="Check if monthly bins analysis is working properly.")
async def monthly_bins_health_check(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Health check endpoint for monthly bins analysis functionality.
    
    Tests database connectivity and monthly bins computation.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "monthly-bins",
            "database_connected": true,
            "can_analyze_monthly": true,
            "sample_churned_count": 1869
        }
    """
    try:
        # Test basic database connectivity
        result = await conn.fetchval("SELECT 1")
        db_connected = result == 1
        
        # Test if we can access monthly charges data for churned customers
        churned_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM churn_customers
            WHERE "Churn" = 'Yes' AND "MonthlyCharges" IS NOT NULL
        """)
        
        can_analyze = db_connected and churned_count is not None
        
        status = "healthy" if can_analyze else "degraded"
        
        return {
            "status": status,
            "service": "monthly-bins",
            "database_connected": db_connected,
            "can_analyze_monthly": can_analyze,
            "sample_churned_count": int(churned_count) if churned_count else 0
        }
        
    except Exception as e:
        logger.error(f"Monthly bins health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "monthly-bins",
            "database_connected": False,
            "can_analyze_monthly": False,
            "error": str(e)
        }