#!/usr/bin/env python3
"""
FastAPI router for churn by contract endpoints.
Provides REST API for analyzing churn rates grouped by contract type.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import asyncpg
import logging

from ..core.db import get_db_connection
from ..analysis.churn_by_contract import (
    compute_churn_by_contract,
    compute_churn_by_contract_with_metadata,
    get_contract_summary_stats
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


@router.get("/contract", 
            response_model=Dict[str, List[Dict[str, Any]]],
            summary="Get Churn Rate by Contract Type",
            description="Retrieve churn rates grouped by contract type, sorted by churn rate descending.")
async def get_churn_by_contract(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get churn rates grouped by contract type.
    
    Analyzes customer churn patterns by contract type:
    - Groups customers by contract type (Month-to-month, One year, Two year)
    - Handles NULL/empty contract types as "Unknown"
    - Calculates churn rate = churned_customers / total_customers
    - Returns results sorted by churn_rate DESC
    - Rounds churn_rate to 4 decimal places
    
    Returns:
        JSON response with churn_rate_by_contract array
        
    Raises:
        HTTPException: 500 for database or computation errors
        
    Example Response:
        {
            "churn_rate_by_contract": [
                {"key": "Month-to-month", "churn_rate": 0.4273, "n": 3875},
                {"key": "One year", "churn_rate": 0.1127, "n": 1473},
                {"key": "Two year", "churn_rate": 0.0283, "n": 1695}
            ]
        }
    """
    try:
        logger.info("Computing churn rates by contract type")
        
        # Compute churn analysis using the provided database connection
        contract_analysis = await compute_churn_by_contract(conn)
        
        logger.info(f"Contract analysis computed successfully: {len(contract_analysis)} contract types found")
        
        # Format response according to required schema
        response = {
            "churn_rate_by_contract": contract_analysis
        }
        
        return response
        
    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_churn_by_contract: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Computation error in get_churn_by_contract: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_churn_by_contract: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/contract/metadata",
            response_model=Dict[str, Any],
            summary="Get Churn by Contract with Metadata",
            description="Get churn rates by contract type with additional metadata and computation details.")
async def get_churn_by_contract_with_metadata(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get churn rates by contract type with additional metadata.
    
    Includes the same contract analysis as /api/churn/contract but adds metadata about
    the computation including timestamp, total customers, and contract type count.
    
    Returns:
        JSON response with contract analysis and metadata
        
    Example Response:
        {
            "churn_rate_by_contract": [
                {"key": "Month-to-month", "churn_rate": 0.4273, "n": 3875}
            ],
            "metadata": {
                "total_customers": 7043,
                "total_contracts": 3,
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        logger.info("Computing churn rates by contract type with metadata")
        
        result = await compute_churn_by_contract_with_metadata(conn)
        
        logger.info(f"Contract analysis with metadata computed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_churn_by_contract_with_metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute churn by contract with metadata: {str(e)}"
        )


@router.get("/contract/summary",
            response_model=Dict[str, Any],
            summary="Get Contract Churn Summary Statistics",
            description="Get summary statistics for contract churn analysis including highest/lowest rates.")
async def get_contract_churn_summary(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Get summary statistics for contract churn analysis.
    
    Provides insights like:
    - Contract type with highest churn rate
    - Contract type with lowest churn rate  
    - Weighted average churn rate across all contracts
    - Total number of contract types
    
    Returns:
        JSON response with contract summary statistics
        
    Example Response:
        {
            "highest_churn_contract": {"key": "Month-to-month", "churn_rate": 0.4273, "n": 3875},
            "lowest_churn_contract": {"key": "Two year", "churn_rate": 0.0283, "n": 1695},
            "average_churn_rate": 0.2654,
            "total_contract_types": 3
        }
    """
    try:
        logger.info("Computing contract churn summary statistics")
        
        summary_stats = await get_contract_summary_stats(conn)
        
        logger.info("Contract summary statistics computed successfully")
        
        return summary_stats
        
    except Exception as e:
        logger.error(f"Error in get_contract_churn_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute contract churn summary: {str(e)}"
        )


@router.get("/contract/health",
            response_model=Dict[str, Any],
            summary="Contract Analysis Health Check", 
            description="Check if contract churn analysis is working properly.")
async def contract_health_check(conn: asyncpg.Connection = Depends(get_db_connection)) -> Dict[str, Any]:
    """
    Health check endpoint for contract churn analysis functionality.
    
    Tests database connectivity and contract analysis computation.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "churn-by-contract",
            "database_connected": true,
            "can_analyze_contracts": true,
            "sample_contract_count": 3
        }
    """
    try:
        # Test basic database connectivity
        result = await conn.fetchval("SELECT 1")
        db_connected = result == 1
        
        # Test if we can access contract data
        contract_count = await conn.fetchval("""
            SELECT COUNT(DISTINCT 
                CASE 
                    WHEN "Contract" IS NULL OR TRIM("Contract") = '' THEN 'Unknown'
                    ELSE "Contract"
                END
            )
            FROM churn_customers
        """)
        
        can_analyze = db_connected and contract_count is not None
        
        status = "healthy" if can_analyze else "degraded"
        
        return {
            "status": status,
            "service": "churn-by-contract",
            "database_connected": db_connected,
            "can_analyze_contracts": can_analyze,
            "sample_contract_count": int(contract_count) if contract_count else 0
        }
        
    except Exception as e:
        logger.error(f"Contract health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "churn-by-contract",
            "database_connected": False,
            "can_analyze_contracts": False,
            "error": str(e)
        }