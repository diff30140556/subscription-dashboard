#!/usr/bin/env python3
"""
Churn by payment method analysis.
Computes churn rates grouped by payment method with proper NULL handling.
"""

from typing import List, Dict, Any, Optional
import asyncpg
from ..core.db import fetch_df
from ..core.utils import safe_div, round_fp


async def compute_churn_by_payment(conn: Optional[asyncpg.Connection] = None) -> List[Dict[str, Any]]:
    """
    Compute churn rates grouped by payment method.
    
    This function calculates churn rate and sample size for each payment method:
    - Groups customers by payment method
    - Handles NULL/empty payment methods as "Unknown"
    - Calculates churn_rate = churned_customers / total_customers per group
    - Returns results sorted by churn_rate DESC
    
    Args:
        conn: Optional asyncpg connection (uses global db if None)
        
    Returns:
        List of dictionaries with payment method churn analysis:
        [
            {"key": "Electronic check", "churn_rate": 0.4522, "n": 2365},
            {"key": "Mailed check", "churn_rate": 0.1916, "n": 1612},
            {"key": "Bank transfer (automatic)", "churn_rate": 0.1680, "n": 1544},
            {"key": "Credit card (automatic)", "churn_rate": 0.1522, "n": 1522}
        ]
        
    Raises:
        asyncpg.PostgresError: For database connection/query errors
        ValueError: For invalid data or computation errors
    """
    
    # SQL query to group by payment method and compute churn metrics
    # Handle NULL/empty payment methods as "Unknown"
    # Calculate churn rate and total count per payment method
    sql = """
    SELECT 
        CASE 
            WHEN "PaymentMethod" IS NULL OR TRIM("PaymentMethod") = '' THEN 'Unknown'
            ELSE "PaymentMethod"
        END as payment_method,
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
            WHEN "PaymentMethod" IS NULL OR TRIM("PaymentMethod") = '' THEN 'Unknown'
            ELSE "PaymentMethod"
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
            payment_method = row.get('payment_method', 'Unknown')
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
                "key": str(payment_method),
                "churn_rate": churn_rate,
                "n": total_customers
            }
            
            results.append(result_item)
        
        # Results should already be sorted by churn_rate DESC from SQL ORDER BY
        # But ensure sorting just in case
        results.sort(key=lambda x: x["churn_rate"], reverse=True)
        
        return results
        
    except asyncpg.PostgresError as e:
        raise asyncpg.PostgresError(f"Database error in compute_churn_by_payment: {e}")
    except Exception as e:
        raise ValueError(f"Failed to compute churn by payment method: {e}")


async def compute_churn_by_payment_with_metadata(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Compute churn by payment method with additional metadata.
    
    Args:
        conn: Optional asyncpg connection
        
    Returns:
        Dict with payment method analysis and metadata:
        {
            "churn_rate_by_payment": [...],
            "metadata": {
                "total_customers": 7043,
                "total_payment_methods": 4,
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        from datetime import datetime
        
        # Get main analysis
        payment_analysis = await compute_churn_by_payment(conn)
        
        # Calculate metadata
        total_customers = sum(item["n"] for item in payment_analysis)
        total_payment_methods = len(payment_analysis)
        
        return {
            "churn_rate_by_payment": payment_analysis,
            "metadata": {
                "total_customers": total_customers,
                "total_payment_methods": total_payment_methods,
                "computed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute churn by payment method with metadata: {e}")


async def get_payment_summary_stats(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Get summary statistics for payment method analysis.
    
    Returns:
        Dict with summary stats like highest/lowest churn rates, etc.
    """
    try:
        payment_data = await compute_churn_by_payment(conn)
        
        if not payment_data:
            return {
                "highest_churn_payment": None,
                "lowest_churn_payment": None,
                "average_churn_rate": 0.0,
                "total_payment_methods": 0
            }
        
        # Find highest and lowest churn rates
        highest_churn = max(payment_data, key=lambda x: x["churn_rate"])
        lowest_churn = min(payment_data, key=lambda x: x["churn_rate"])
        
        # Calculate weighted average churn rate
        total_customers = sum(item["n"] for item in payment_data)
        weighted_churn = sum(item["churn_rate"] * item["n"] for item in payment_data)
        avg_churn_rate = round_fp(safe_div(weighted_churn, total_customers), 4) or 0.0
        
        return {
            "highest_churn_payment": highest_churn,
            "lowest_churn_payment": lowest_churn,
            "average_churn_rate": avg_churn_rate,
            "total_payment_methods": len(payment_data)
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute payment method summary stats: {e}")


async def compare_payment_vs_contract_churn(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Compare churn rates between payment methods and contract types.
    
    Returns comparative analysis between the two segmentation approaches.
    """
    try:
        # Import here to avoid circular imports
        from .churn_by_contract import compute_churn_by_contract
        
        # Get both analyses
        payment_data = await compute_churn_by_payment(conn)
        contract_data = await compute_churn_by_contract(conn)
        
        # Calculate ranges for comparison
        payment_rates = [item["churn_rate"] for item in payment_data] if payment_data else [0]
        contract_rates = [item["churn_rate"] for item in contract_data] if contract_data else [0]
        
        return {
            "payment_method_analysis": {
                "highest_rate": max(payment_rates),
                "lowest_rate": min(payment_rates),
                "rate_spread": max(payment_rates) - min(payment_rates),
                "method_count": len(payment_data)
            },
            "contract_analysis": {
                "highest_rate": max(contract_rates),
                "lowest_rate": min(contract_rates),
                "rate_spread": max(contract_rates) - min(contract_rates),
                "contract_count": len(contract_data)
            },
            "comparison": {
                "higher_spread_segment": "payment" if (max(payment_rates) - min(payment_rates)) > (max(contract_rates) - min(contract_rates)) else "contract",
                "payment_vs_contract_spread_ratio": round_fp(safe_div(max(payment_rates) - min(payment_rates), max(contract_rates) - min(contract_rates)), 4) or 0.0
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compare payment vs contract churn: {e}")