#!/usr/bin/env python3
"""
FastAPI router for KPI endpoints.
Provides REST API for key performance indicators related to churn analysis.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import asyncpg
import logging

from ..core.db import get_db_connection
from ..analysis.kpi_metrics import compute_kpis

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


@router.get("/kpis", 
            response_model=Dict[str, Any],
            summary="Get KPI Metrics",
            description="Retrieve key performance indicators for churn analysis including churn rate, average tenure, and monthly charges.")
async def get_kpis(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get KPI metrics for all customers.
    
    Returns key performance indicators:
    - churned_users: Number of customers who churned
    - churn_rate_overall: Overall churn rate (0-1, 4 decimal places)
    - avg_tenure: Average customer tenure in months (1 decimal place)
    - avg_monthly: Average monthly charges (1 decimal place)
    
    Returns:
        JSON response with kpis object containing metrics
        
    Raises:
        HTTPException: 500 for database or computation errors
        
    Example Response:
        {
            "kpis": {
                "churned_users": 1869,
                "churn_rate_overall": 0.2663,
                "avg_tenure": 32.4,
                "avg_monthly": 64.8
            }
        }
    """
    try:
        logger.info("Computing KPI metrics")
        
        # Compute KPIs using the provided database connection
        result = await compute_kpis(conn)
        
        logger.info(f"KPI computation successful: {result['kpis']}")
        
        return result
        
    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_kpis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Computation error in get_kpis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_kpis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/kpis/health",
            response_model=Dict[str, Any], 
            summary="KPI Health Check",
            description="Check if KPI computation is working properly.")
async def kpis_health_check(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Health check endpoint for KPI functionality.
    
    Tests database connectivity and basic KPI computation without heavy processing.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "kpis",
            "database_connected": true,
            "can_compute": true
        }
    """
    try:
        # Test basic database connectivity
        result = await conn.fetchval("SELECT 1")
        db_connected = result == 1
        
        # Test if we can access the churn_customers table
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'churn_customers'
            )
        """)
        
        can_compute = db_connected and table_exists
        
        status = "healthy" if can_compute else "degraded"
        
        return {
            "status": status,
            "service": "kpis", 
            "database_connected": db_connected,
            "table_exists": bool(table_exists),
            "can_compute": can_compute
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "kpis",
            "database_connected": False,
            "can_compute": False,
            "error": str(e)
        }


@router.get("/kpis/summary",
            response_model=Dict[str, Any],
            summary="Get KPI Summary with Metadata", 
            description="Get KPIs with additional metadata and computation details.")
async def get_kpis_summary(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get KPI metrics with additional metadata.
    
    Includes the same KPI metrics as /api/kpis but adds metadata about
    the computation including timestamp and data source information.
    
    Returns:
        JSON response with kpis and metadata
        
    Example Response:
        {
            "kpis": {
                "churned_users": 1869,
                "churn_rate_overall": 0.2663,
                "avg_tenure": 32.4,
                "avg_monthly": 64.8
            },
            "metadata": {
                "computed_at": "2024-01-15T10:30:00Z",
                "table_name": "churn_customers",
                "total_records": 7043
            }
        }
    """
    try:
        from datetime import datetime
        
        # Get basic KPIs
        result = await compute_kpis(conn)
        
        # Add metadata
        total_records = await conn.fetchval("SELECT COUNT(*) FROM churn_customers")
        
        result["metadata"] = {
            "computed_at": datetime.utcnow().isoformat() + "Z",
            "table_name": "churn_customers",
            "total_records": int(total_records) if total_records else 0
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_kpis_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute KPI summary: {str(e)}"
        )