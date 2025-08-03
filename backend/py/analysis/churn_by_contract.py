#!/usr/bin/env python3
"""
Churn by contract type analysis.
Computes churn rates grouped by contract type with proper NULL handling.
"""

from typing import List, Dict, Any, Optional
import asyncpg
from ..core.db import fetch_df
from ..core.utils import safe_div, round_fp


async def compute_churn_by_contract(conn: Optional[asyncpg.Connection] = None) -> List[Dict[str, Any]]:
    """
    Compute churn rates grouped by contract type.
    
    This function calculates churn rate and sample size for each contract type:
    - Groups customers by contract type
    - Handles NULL/empty contract types as "Unknown"
    - Calculates churn_rate = churned_customers / total_customers per group
    - Returns results sorted by churn_rate DESC
    
    Args:
        conn: Optional asyncpg connection (uses global db if None)
        
    Returns:
        List of dictionaries with contract churn analysis:
        [
            {"key": "Month-to-month", "churn_rate": 0.4273, "n": 3875},
            {"key": "One year", "churn_rate": 0.1127, "n": 1473},
            {"key": "Two year", "churn_rate": 0.0283, "n": 1695}
        ]
        
    Raises:
        asyncpg.PostgresError: For database connection/query errors
        ValueError: For invalid data or computation errors
    """
    
    # SQL query to group by contract type and compute churn metrics
    # Handle NULL/empty contract types as "Unknown"
    # Calculate churn rate and total count per contract type
    sql = """
    SELECT 
        CASE 
            WHEN "Contract" IS NULL OR TRIM("Contract") = '' THEN 'Unknown'
            ELSE "Contract"
        END as contract_type,
        COUNT(*) as total_customers,
        SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) as churned_customers,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0)
            ELSE 0.0
        END as churn_rate_raw
    FROM churn_customers
    GROUP BY 
        CASE 
            WHEN "Contract" IS NULL OR TRIM("Contract") = '' THEN 'Unknown'
            ELSE "Contract"
        END
    ORDER BY churn_rate_raw DESC;
    """
    
    try:
        # Fetch data using the global fetch_df function or connection-specific query
        if conn:
            # Use provided connection directly
            rows = await conn.fetch(sql)
            if not rows:
                return []
            
            # Convert asyncpg Records to list of dicts
            data = [dict(row) for row in rows]
        else:
            # Use global db manager
            df = await fetch_df(sql)
            if df.empty:
                return []
            
            # Convert DataFrame to list of dicts
            data = df.to_dict('records')
        
        # Process results and format according to schema
        results = []
        
        for row in data:
            contract_type = row.get('contract_type', 'Unknown')
            total_customers = int(row.get('total_customers', 0))
            churned_customers = int(row.get('churned_customers', 0))
            churn_rate_raw = row.get('churn_rate_raw')
            
            # Calculate churn rate with safe division and proper rounding
            if churn_rate_raw is not None:
                churn_rate = round_fp(float(churn_rate_raw), 4) or 0.0
            else:
                churn_rate = round_fp(safe_div(churned_customers, total_customers), 4) or 0.0
            
            # Format according to required schema
            result_item = {
                "key": str(contract_type),
                "churn_rate": churn_rate,
                "n": total_customers
            }
            
            results.append(result_item)
        
        # Results should already be sorted by churn_rate DESC from SQL ORDER BY
        # But ensure sorting just in case
        results.sort(key=lambda x: x["churn_rate"], reverse=True)
        
        return results
        
    except asyncpg.PostgresError as e:
        raise asyncpg.PostgresError(f"Database error in compute_churn_by_contract: {e}")
    except Exception as e:
        raise ValueError(f"Failed to compute churn by contract: {e}")


async def compute_churn_by_contract_with_metadata(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Compute churn by contract with additional metadata.
    
    Args:
        conn: Optional asyncpg connection
        
    Returns:
        Dict with contract analysis and metadata:
        {
            "churn_rate_by_contract": [...],
            "metadata": {
                "total_customers": 7043,
                "total_contracts": 3,
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        from datetime import datetime
        
        # Get main analysis
        contract_analysis = await compute_churn_by_contract(conn)
        
        # Calculate metadata
        total_customers = sum(item["n"] for item in contract_analysis)
        total_contracts = len(contract_analysis)
        
        return {
            "churn_rate_by_contract": contract_analysis,
            "metadata": {
                "total_customers": total_customers,
                "total_contracts": total_contracts,
                "computed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute churn by contract with metadata: {e}")


async def get_contract_summary_stats(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Get summary statistics for contract analysis.
    
    Returns:
        Dict with summary stats like highest/lowest churn rates, etc.
    """
    try:
        contract_data = await compute_churn_by_contract(conn)
        
        if not contract_data:
            return {
                "highest_churn_contract": None,
                "lowest_churn_contract": None,
                "average_churn_rate": 0.0,
                "total_contract_types": 0
            }
        
        # Find highest and lowest churn rates
        highest_churn = max(contract_data, key=lambda x: x["churn_rate"])
        lowest_churn = min(contract_data, key=lambda x: x["churn_rate"])
        
        # Calculate weighted average churn rate
        total_customers = sum(item["n"] for item in contract_data)
        weighted_churn = sum(item["churn_rate"] * item["n"] for item in contract_data)
        avg_churn_rate = round_fp(safe_div(weighted_churn, total_customers), 4) or 0.0
        
        return {
            "highest_churn_contract": highest_churn,
            "lowest_churn_contract": lowest_churn,
            "average_churn_rate": avg_churn_rate,
            "total_contract_types": len(contract_data)
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute contract summary stats: {e}")