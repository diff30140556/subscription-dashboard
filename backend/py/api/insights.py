#!/usr/bin/env python3
"""
FastAPI router for AI-powered churn insights endpoints.
Provides REST API for generating strategic churn analysis insights using OpenAI GPT-4o.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

from ..analysis.ai_insights import (
    generate_churn_insights,
    validate_openai_connection
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/api",
    tags=["ai-insights"],
    responses={
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)


class ChurnInsightsRequest(BaseModel):
    """Request model for churn insights generation."""
    
    # Overall metrics
    overall_churn_rate: float = Field(None, description="Overall churn rate (0.0 to 1.0)")
    total_customers: int = Field(None, description="Total number of customers")
    churned_customers: int = Field(None, description="Number of churned customers")
    average_tenure: float = Field(None, description="Average customer tenure in months")
    average_monthly_charges: float = Field(None, description="Average monthly charges in dollars")
    
    # Churn by segments
    churn_by_contract: list = Field(None, description="List of contract churn analysis")
    churn_by_payment: list = Field(None, description="List of payment method churn analysis")
    churn_by_features: Dict[str, list] = Field(None, description="Dictionary of feature churn analysis")
    
    # Distributions
    tenure_distribution: list = Field(None, description="Tenure distribution of churned customers")
    monthly_charges_distribution: list = Field(None, description="Monthly charges distribution of churned customers")
    
    # ML insights
    model_insights: dict = Field(None, description="Machine learning model insights")
    
    class Config:
        schema_extra = {
            "example": {
                "overall_churn_rate": 0.2654,
                "total_customers": 7043,
                "churned_customers": 1869,
                "average_tenure": 32.4,
                "average_monthly_charges": 64.8,
                "churn_by_contract": [
                    {"key": "Month-to-month", "churn_rate": 0.4273, "n": 3875},
                    {"key": "One year", "churn_rate": 0.1127, "n": 1473},
                    {"key": "Two year", "churn_rate": 0.0283, "n": 1695}
                ],
                "churn_by_payment": [
                    {"key": "Electronic check", "churn_rate": 0.4528, "n": 2365},
                    {"key": "Mailed check", "churn_rate": 0.1911, "n": 1612},
                    {"key": "Bank transfer (automatic)", "churn_rate": 0.1671, "n": 1544},
                    {"key": "Credit card (automatic)", "churn_rate": 0.1524, "n": 1522}
                ]
            }
        }


class ChurnInsightsResponse(BaseModel):
    """Response model for churn insights."""
    
    insights: str = Field(description="AI-generated strategic insights and recommendations")
    metadata: dict = Field(description="Generation metadata including timestamp and model info")
    
    class Config:
        schema_extra = {
            "example": {
                "insights": "# KEY INSIGHTS\n\n1. **Critical Churn Rate**: At 26.5%, your churn rate indicates significant retention challenges...\n\n# STRATEGIC RECOMMENDATIONS\n\n1. **Target Month-to-Month Contracts**: With 42.7% churn rate, this segment needs immediate attention...",
                "metadata": {
                    "generated_at": "2024-01-15T10:30:00Z",
                    "model_used": "gpt-4o",
                    "data_points_analyzed": 12,
                    "prompt_length": 1256
                }
            }
        }


@router.post("/insights",
             response_model=ChurnInsightsResponse,
             summary="Generate AI-Powered Churn Insights",
             description="Generate strategic insights and recommendations from churn analysis data using OpenAI GPT-4o.")
async def generate_insights(request: ChurnInsightsRequest) -> Dict[str, Any]:
    """
    Generate AI-powered strategic insights from churn analysis data.
    
    This endpoint takes aggregated churn analysis metrics and uses OpenAI's GPT-4o
    to generate strategic insights, root cause analysis, and actionable recommendations
    for reducing customer churn.
    
    Request Body:
        ChurnInsightsRequest with churn analysis metrics including:
        - Overall churn rate and customer counts
        - Churn rates by contract type, payment method, service features
        - Tenure and monthly charges distributions
        - ML model insights (optional)
    
    Returns:
        JSON response with AI-generated insights and metadata
        
    Raises:
        HTTPException: 400 for invalid request data, 500 for AI generation errors
        
    Example Usage:
        ```python
        import requests
        
        data = {
            "overall_churn_rate": 0.2654,
            "total_customers": 7043,
            "churned_customers": 1869,
            "churn_by_contract": [
                {"key": "Month-to-month", "churn_rate": 0.4273, "n": 3875}
            ]
        }
        
        response = requests.post("/api/insights", json=data)
        insights = response.json()["insights"]
        ```
    """
    try:
        logger.info("Generating AI-powered churn insights")
        
        # Convert request to dictionary for processing
        churn_data = request.dict(exclude_none=True)
        
        if not churn_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body cannot be empty. Please provide churn analysis data."
            )
        
        logger.info(f"Processing churn data with {len(churn_data)} data fields")
        
        # Generate insights using AI
        result = await generate_churn_insights(churn_data)
        
        logger.info(f"AI insights generated successfully ({len(result['insights'])} characters)")
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in generate_insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/insights/health",
            response_model=Dict[str, Any],
            summary="AI Insights Health Check",
            description="Check if AI insights generation is working properly.")
async def insights_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for AI insights functionality.
    
    Tests OpenAI API connectivity, API key validation, and service availability.
    
    Returns:
        JSON response with health status
        
    Example Response:
        {
            "status": "healthy",
            "service": "ai-insights",
            "openai_available": true,
            "api_key_valid": true,
            "model_configured": "gpt-4o"
        }
    """
    try:
        logger.info("Running AI insights health check")
        
        # Validate OpenAI connection
        validation_result = await validate_openai_connection()
        
        # Determine overall status
        is_healthy = (
            validation_result.get("openai_available", False) and
            validation_result.get("api_key_valid", False)
        )
        
        status = "healthy" if is_healthy else "degraded"
        
        return {
            "status": status,
            "service": "ai-insights",
            **validation_result
        }
        
    except Exception as e:
        logger.error(f"AI insights health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "ai-insights",
            "openai_available": False,
            "api_key_valid": False,
            "error": str(e)
        }


@router.get("/insights/sample",
            response_model=Dict[str, Any],
            summary="Get Sample Insights Request",
            description="Get a sample request payload for testing the insights endpoint.")
async def get_sample_insights_request() -> Dict[str, Any]:
    """
    Get a sample request payload for testing the insights endpoint.
    
    Returns a realistic example of churn analysis data that can be used
    to test the /api/insights endpoint.
    
    Returns:
        JSON response with sample request data
    """
    try:
        sample_data = {
            "overall_churn_rate": 0.2654,
            "total_customers": 7043,
            "churned_customers": 1869,
            "average_tenure": 32.4,
            "average_monthly_charges": 64.8,
            "churn_by_contract": [
                {"key": "Month-to-month", "churn_rate": 0.4273, "n": 3875},
                {"key": "One year", "churn_rate": 0.1127, "n": 1473},
                {"key": "Two year", "churn_rate": 0.0283, "n": 1695}
            ],
            "churn_by_payment": [
                {"key": "Electronic check", "churn_rate": 0.4528, "n": 2365},
                {"key": "Mailed check", "churn_rate": 0.1911, "n": 1612},
                {"key": "Bank transfer (automatic)", "churn_rate": 0.1671, "n": 1544},
                {"key": "Credit card (automatic)", "churn_rate": 0.1524, "n": 1522}
            ],
            "churn_by_features": {
                "OnlineSecurity": [
                    {"key": "Yes", "churn_rate": 0.1467, "n": 2019},
                    {"key": "No", "churn_rate": 0.4168, "n": 5024}
                ],
                "TechSupport": [
                    {"key": "Yes", "churn_rate": 0.1519, "n": 2044},
                    {"key": "No", "churn_rate": 0.4089, "n": 4999}
                ]
            },
            "tenure_distribution": [
                {"range": "0–3", "count": 245, "pct": 0.1311},
                {"range": "4–6", "count": 178, "pct": 0.0952},
                {"range": "7–12", "count": 342, "pct": 0.1830},
                {"range": "13–24", "count": 287, "pct": 0.1536},
                {"range": "25+", "count": 817, "pct": 0.4371}
            ],
            "monthly_charges_distribution": [
                {"range": "0–35", "count": 245, "pct": 0.1311},
                {"range": "36–65", "count": 420, "pct": 0.2248},
                {"range": "66–95", "count": 680, "pct": 0.3639},
                {"range": "96+", "count": 524, "pct": 0.2802}
            ],
            "model_insights": {
                "auc": 0.8456,
                "top_features": [
                    {"feature": "Contract_Month-to-month", "weight": 1.2345},
                    {"feature": "tenure", "weight": -0.9876},
                    {"feature": "OnlineSecurity", "weight": -0.7654},
                    {"feature": "TechSupport", "weight": -0.6543},
                    {"feature": "PaymentMethod_Electronic check", "weight": 0.5432}
                ]
            }
        }
        
        return {
            "sample_request": sample_data,
            "usage_instructions": {
                "endpoint": "POST /api/insights",
                "content_type": "application/json",
                "description": "Send this sample data as JSON in the request body to test AI insights generation"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating sample request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sample request: {str(e)}"
        )