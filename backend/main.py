#!/usr/bin/env python3
"""
Backend entry point for churn analysis API.
This file allows running the backend from the backend/ directory.
"""

import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# More explicit CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://churn-insight.vercel.app",
        "https://*.vercel.app",  # Allow all Vercel subdomains
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
    ],
)

# Explicit OPTIONS handler
@app.options("/{path:path}")
async def options_handler(path: str):
    return {"status": "ok"}

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Add the py module to the Python path
backend_dir = Path(__file__).parent
py_dir = backend_dir / "py"
sys.path.insert(0, str(py_dir))

# Load environment variables first
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

# Import and run the main application
import uvicorn

if __name__ == "__main__":
    # Run development server
    uvicorn.run(
        "py.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )