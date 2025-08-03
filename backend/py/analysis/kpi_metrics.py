#!/usr/bin/env python3
"""
KPI metrics computation for churn analysis.
Computes key performance indicators from customer data using safe SQL operations.
"""

from typing import Dict, Any, Optional
import asyncpg
import pandas as pd
from ..core.db import fetch_df
from ..core.utils import safe_div, round_fp, safe_sum


async def compute_kpis(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Compute KPI metrics for all customers in the database.
    
    This function calculates:
    - churned_users: Count of customers with churn = TRUE
    - churn_rate_overall: Ratio of churned to total customers (0-1, 4 decimals)
    - avg_tenure: Average tenure across all customers (1 decimal)
    - avg_monthly: Average monthly charges across all customers (1 decimal)
    
    Args:
        conn: Optional asyncpg connection (uses global db if None)
        
    Returns:
        Dict containing 'kpis' key with computed metrics
        
    Raises:
        asyncpg.PostgresError: For database connection/query errors
        ValueError: For invalid data or computation errors
        
    Example:
        {
            "kpis": {
                "churned_users": 1869,
                "churn_rate_overall": 0.2663,
                "avg_tenure": 32.4,
                "avg_monthly": 64.8
            }
        }
    """
    # SQL query to get all required metrics in a single query
    # Using NULLIF to prevent division by zero
    # Assumes table: churn_customers with columns: Churn (STRING "Yes"/"No"), tenure (NUMERIC), MonthlyCharges (NUMERIC)
    sql = """
    WITH metrics AS (
        SELECT 
            COUNT(*) as total_customers,
            SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) as churned_count,
            AVG(CASE WHEN tenure IS NOT NULL THEN tenure END) as avg_tenure_raw,
            AVG(CASE WHEN "MonthlyCharges" IS NOT NULL THEN "MonthlyCharges" END) as avg_monthly_raw
        FROM churn_customers
    )
    SELECT 
        total_customers,
        churned_count,
        avg_tenure_raw,
        avg_monthly_raw,
        CASE 
            WHEN total_customers > 0 THEN churned_count::FLOAT / NULLIF(total_customers, 0)
            ELSE 0.0
        END as churn_rate_raw
    FROM metrics;
    """
    
    try:
        # Fetch data using the global fetch_df function or connection-specific query
        if conn:
            # Use provided connection directly
            row = await conn.fetchrow(sql)
            if not row:
                raise ValueError("No data returned from churn_customers table")
            
            # Convert asyncpg Record to dict
            data = dict(row)
        else:
            # Use global db manager
            df = await fetch_df(sql)
            if df.empty:
                raise ValueError("No data returned from churn_customers table")
            
            # Convert first row to dict
            data = df.iloc[0].to_dict()
        
        # Extract raw values with null safety
        total_customers = int(data.get('total_customers', 0))
        churned_count = int(data.get('churned_count', 0))
        avg_tenure_raw = data.get('avg_tenure_raw')
        avg_monthly_raw = data.get('avg_monthly_raw')
        churn_rate_raw = data.get('churn_rate_raw')
        
        # Validate we have customers
        if total_customers == 0:
            return {
                "kpis": {
                    "churned_users": 0,
                    "churn_rate_overall": 0.0,
                    "avg_tenure": 0.0,
                    "avg_monthly": 0.0
                }
            }
        
        # Calculate KPIs with proper rounding and null handling
        churned_users = churned_count
        
        # Churn rate: Use database calculation or safe_div as fallback
        if churn_rate_raw is not None:
            churn_rate_overall = round_fp(float(churn_rate_raw), 4) or 0.0
        else:
            churn_rate_overall = round_fp(safe_div(churned_count, total_customers), 4) or 0.0
        
        # Average tenure: 1 decimal place
        avg_tenure = round_fp(avg_tenure_raw, 1) if avg_tenure_raw is not None else 0.0
        
        # Average monthly charges: 1 decimal place  
        avg_monthly = round_fp(avg_monthly_raw, 1) if avg_monthly_raw is not None else 0.0
        
        return {
            "kpis": {
                "churned_users": churned_users,
                "churn_rate_overall": churn_rate_overall,
                "avg_tenure": avg_tenure,
                "avg_monthly": avg_monthly
            }
        }
        
    except asyncpg.PostgresError as e:
        raise asyncpg.PostgresError(f"Database error in compute_kpis: {e}")
    except Exception as e:
        raise ValueError(f"Failed to compute KPIs: {e}")


async def compute_kpis_alternative_table(table_name: str = "customers") -> Dict[str, Any]:
    """
    Alternative KPI computation for different table schemas.
    
    Assumes a more generic table structure:
    - customers(customer_id, churn BOOL, tenure NUMERIC, monthly_charges NUMERIC)
    
    Args:
        table_name: Name of the customer table (default: "customers")
        
    Returns:
        Dict containing 'kpis' key with computed metrics
    """
    # Parameterized query with table name (note: in production, validate table_name against allowlist)
    sql = f"""
    WITH metrics AS (
        SELECT 
            COUNT(*) as total_customers,
            SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) as churned_count,
            AVG(CASE WHEN tenure IS NOT NULL THEN tenure END) as avg_tenure_raw,
            AVG(CASE WHEN "MonthlyCharges" IS NOT NULL THEN "MonthlyCharges" END) as avg_monthly_raw
        FROM {table_name}
    )
    SELECT 
        total_customers,
        churned_count,
        avg_tenure_raw,
        avg_monthly_raw,
        CASE 
            WHEN total_customers > 0 THEN churned_count::FLOAT / NULLIF(total_customers, 0)
            ELSE 0.0
        END as churn_rate_raw
    FROM metrics;
    """
    
    # Validate table name to prevent SQL injection
    allowed_tables = {'customers', 'churn_customers', 'customer_data'}
    if table_name not in allowed_tables:
        raise ValueError(f"Table '{table_name}' not in allowed list: {allowed_tables}")
    
    try:
        df = await fetch_df(sql)
        if df.empty:
            raise ValueError(f"No data returned from {table_name} table")
        
        data = df.iloc[0].to_dict()
        
        # Same processing as main compute_kpis function
        total_customers = int(data.get('total_customers', 0))
        churned_count = int(data.get('churned_count', 0))
        avg_tenure_raw = data.get('avg_tenure_raw')
        avg_monthly_raw = data.get('avg_monthly_raw')
        churn_rate_raw = data.get('churn_rate_raw')
        
        if total_customers == 0:
            return {
                "kpis": {
                    "churned_users": 0,
                    "churn_rate_overall": 0.0,
                    "avg_tenure": 0.0,
                    "avg_monthly": 0.0
                }
            }
        
        churned_users = churned_count
        churn_rate_overall = round_fp(float(churn_rate_raw) if churn_rate_raw is not None else 0.0, 4) or 0.0
        avg_tenure = round_fp(avg_tenure_raw, 1) if avg_tenure_raw is not None else 0.0
        avg_monthly = round_fp(avg_monthly_raw, 1) if avg_monthly_raw is not None else 0.0
        
        return {
            "kpis": {
                "churned_users": churned_users,
                "churn_rate_overall": churn_rate_overall,
                "avg_tenure": avg_tenure,
                "avg_monthly": avg_monthly
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute KPIs for table {table_name}: {e}")