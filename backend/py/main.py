#!/usr/bin/env python3
"""
FastAPI main application for churn analysis backend.
Production-ready with proper error handling, logging, and database lifecycle management.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.db import db_manager, health_check
from .api.kpis import router as kpis_router
from .api.churn_contract import router as churn_contract_router
from .api.churn_payment import router as churn_payment_router
from .api.tenure_bins import router as tenure_bins_router
from .api.monthly_bins import router as monthly_bins_router
from .api.feature_churn import router as feature_churn_router
from .api.baseline_model import router as baseline_model_router
from .api.insights import router as insights_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for startup and shutdown.
    Manages database connection pool lifecycle.
    """
    # Startup
    logger.info("🚀 Starting churn analysis backend...")
    
    try:
        # Initialize database connection pool with timeout
        import asyncio
        await asyncio.wait_for(db_manager.create_pool(), timeout=10.0)
        logger.info("✅ Database connection pool initialized")
        
        # Test database connectivity with timeout
        health = await asyncio.wait_for(health_check(), timeout=5.0)
        if health["status"] == "healthy":
            logger.info("✅ Database connectivity verified")
        else:
            logger.warning(f"⚠️ Database health check failed: {health}")
            
    except asyncio.TimeoutError:
        logger.error("❌ Database initialization timed out - continuing without DB")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        # Continue startup even if DB is not available (for health checks)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down churn analysis backend...")
    
    try:
        await db_manager.close_pool()
        logger.info("✅ Database connection pool closed")
    except Exception as e:
        logger.error(f"❌ Error closing database pool: {e}")


# Create FastAPI application
app = FastAPI(
    title="Churn Analysis API",
    description="Production-ready FastAPI backend for customer churn analysis with PostgreSQL/Supabase integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:8000",  # FastAPI dev server
        "https://yourdomain.com", # Production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(kpis_router)
app.include_router(churn_contract_router)
app.include_router(churn_payment_router)
app.include_router(tenure_bins_router)
app.include_router(monthly_bins_router)
app.include_router(feature_churn_router)
app.include_router(baseline_model_router)
app.include_router(insights_router)


@app.get("/healthz", 
         response_model=Dict[str, Any],
         tags=["health"],
         summary="Health Check",
         description="Basic health check endpoint that returns 200 OK")
async def healthz() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns 200 OK with basic service information.
    Does not test database connectivity (use /health for full health check).
    
    Returns:
        JSON response with service status
    """
    return {
        "status": "ok",
        "service": "churn-analysis-api",
        "version": "1.0.0"
    }


@app.get("/health",
         response_model=Dict[str, Any], 
         tags=["health"],
         summary="Full Health Check",
         description="Comprehensive health check including database connectivity")
async def health() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    Tests service status and database connectivity.
    
    Returns:
        JSON response with detailed health information
        
    Example Response:
        {
            "status": "healthy",
            "service": "churn-analysis-api",
            "version": "1.0.0",
            "database": {
                "status": "healthy",
                "database": "connected",
                "test_query": true,
                "postgres_version": "14.9"
            }
        }
    """
    try:
        # Get database health status
        db_health = await health_check()
        
        # Determine overall status
        overall_status = "healthy" if db_health["status"] == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "service": "churn-analysis-api",
            "version": "1.0.0",
            "database": db_health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "churn-analysis-api", 
                "version": "1.0.0",
                "error": str(e)
            }
        )


@app.get("/",
         response_model=Dict[str, Any],
         tags=["info"],
         summary="API Information",
         description="Basic API information and available endpoints")
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.
    
    Returns:
        JSON response with API metadata and available endpoints
    """
    return {
        "name": "Churn Analysis API",
        "version": "1.0.0",
        "description": "Production-ready FastAPI backend for customer churn analysis",
        "endpoints": {
            "health": "/healthz - Basic health check",
            "full_health": "/health - Comprehensive health check",
            "churn_kpis": "/api/churn/kpis - Get churn KPI metrics",
            "churn_kpis_health": "/api/churn/kpis/health - KPI service health",
            "churn_kpis_summary": "/api/churn/kpis/summary - KPI metrics with metadata",
            "churn_contract": "/api/churn/contract - Churn rates by contract type",
            "churn_contract_metadata": "/api/churn/contract/metadata - Contract analysis with metadata",
            "churn_contract_summary": "/api/churn/contract/summary - Contract summary statistics",
            "churn_payment": "/api/churn/payment - Churn rates by payment method",
            "churn_payment_metadata": "/api/churn/payment/metadata - Payment analysis with metadata",
            "churn_payment_summary": "/api/churn/payment/summary - Payment summary statistics",
            "churn_payment_compare": "/api/churn/payment/compare - Compare payment vs contract analysis",
            "tenure_bins": "/api/tenure/bins - Tenure distribution for churned customers",
            "tenure_bins_metadata": "/api/tenure/bins/metadata - Tenure analysis with metadata",
            "tenure_bins_summary": "/api/tenure/bins/summary - Tenure summary statistics",
            "tenure_bins_insights": "/api/tenure/bins/insights - Tenure distribution insights",
            "tenure_bins_health": "/api/tenure/bins/health - Tenure analysis health check",
            "monthly_bins": "/api/monthly/bins - Monthly charges distribution for churned customers",
            "monthly_bins_metadata": "/api/monthly/bins/metadata - Monthly analysis with metadata",
            "monthly_bins_summary": "/api/monthly/bins/summary - Monthly summary statistics",
            "monthly_bins_insights": "/api/monthly/bins/insights - Monthly charges distribution insights",
            "monthly_bins_health": "/api/monthly/bins/health - Monthly analysis health check",
            "feature_churn": "/api/features/churn - Churn rates by service features (supports ?names= query param)",
            "feature_churn_metadata": "/api/features/churn/metadata - Feature churn analysis with metadata",
            "feature_churn_summary": "/api/features/churn/summary - Feature impact summary and best/worst performers",
            "available_features": "/api/features/available - List of available service features for analysis",
            "feature_churn_health": "/api/features/churn/health - Feature churn analysis health check",
            "baseline_model": "/api/model/baseline - Baseline churn prediction model (Logistic Regression)",
            "baseline_model_retrain": "/api/model/baseline/retrain - Force retrain baseline model",
            "baseline_model_info": "/api/model/baseline/info - Get cached model information",
            "baseline_model_features": "/api/model/baseline/features - Get model feature configuration",
            "baseline_model_health": "/api/model/baseline/health - ML model health check",
            "ai_insights": "/api/insights - AI-powered strategic churn insights (POST with churn data)",
            "ai_insights_health": "/api/insights/health - AI insights service health check",
            "ai_insights_sample": "/api/insights/sample - Get sample request data for testing AI insights",
            "docs": "/docs - Interactive API documentation",
            "redoc": "/redoc - Alternative API documentation"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    
    Logs errors and returns generic error response to avoid exposing internals.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


# Development server runner
def run_dev_server():
    """Run development server with auto-reload."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    # Load environment variables if running directly
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run development server
    run_dev_server()