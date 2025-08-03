#!/usr/bin/env python3
"""
Monthly charges bins analysis for churned customers.
Analyzes monthly charges distribution of churned customers in fixed bins: 0–35, 36–65, 66–95, 96+.
"""

from typing import List, Dict, Any, Optional
import asyncpg
from ..core.db import fetch_df
from ..core.utils import (
    safe_div, 
    round_fp, 
    get_monthly_bins_definition,
    ensure_monthly_bins_order,
    create_complete_monthly_bins
)


async def compute_monthly_bins(conn: Optional[asyncpg.Connection] = None) -> List[Dict[str, Any]]:
    """
    Compute monthly charges distribution for churned customers in fixed bins.
    
    This function analyzes churned customers only (WHERE Churn = 'Yes') and bins
    their monthly charges into fixed ranges: 0–35, 36–65, 66–95, 96+.
    
    Args:
        conn: Optional asyncpg connection (uses global db if None)
        
    Returns:
        List of dictionaries with monthly charge bin analysis in fixed order:
        [
            {"range": "0–35", "count": 245, "pct": 0.1311},
            {"range": "36–65", "count": 420, "pct": 0.2248},
            {"range": "66–95", "count": 680, "pct": 0.3639},
            {"range": "96+", "count": 524, "pct": 0.2802}
        ]
        
    Raises:
        asyncpg.PostgresError: For database connection/query errors
        ValueError: For invalid data or computation errors
    """
    
    # Get monthly bins configuration
    monthly_config = get_monthly_bins_definition()
    
    # SQL query to bin churned customers by monthly charges
    # Only analyze customers who have churned (Churn = 'Yes')
    sql = """
    SELECT 
        CASE 
            WHEN "MonthlyCharges" <= 35 THEN '0–35'
            WHEN "MonthlyCharges" <= 65 THEN '36–65'
            WHEN "MonthlyCharges" <= 95 THEN '66–95'
            ELSE '96+'
        END as charge_range,
        COUNT(*) as count
    FROM churn_customers
    WHERE "Churn" = 'Yes' AND "MonthlyCharges" IS NOT NULL
    GROUP BY 
        CASE 
            WHEN "MonthlyCharges" <= 35 THEN '0–35'
            WHEN "MonthlyCharges" <= 65 THEN '36–65'
            WHEN "MonthlyCharges" <= 95 THEN '66–95'
            ELSE '96+'
        END;
    """
    
    try:
        # Get total churned customers for percentage calculation
        total_churned_sql = """
        SELECT COUNT(*) as total_churned
        FROM churn_customers
        WHERE "Churn" = 'Yes' AND "MonthlyCharges" IS NOT NULL;
        """
        
        # Fetch data using the global fetch_df function or connection-specific query
        if conn:
            # Use provided connection directly
            rows = await conn.fetch(sql)
            total_result = await conn.fetchval(total_churned_sql)
            
            if not rows:
                # Return empty bins with all ranges having zero counts
                return create_complete_monthly_bins([])
            
            # Convert asyncpg Records to list of dicts
            data = [dict(row) for row in rows]
            total_churned = int(total_result) if total_result else 0
        else:
            # Use global db manager
            df = await fetch_df(sql)
            total_df = await fetch_df(total_churned_sql)
            
            if df.empty:
                # Return empty bins with all ranges having zero counts
                return create_complete_monthly_bins([])
            
            # Convert DataFrame to list of dicts
            data = df.to_dict('records')
            total_churned = int(total_df.iloc[0]['total_churned']) if not total_df.empty else 0
        
        # Process results and calculate percentages
        results = []
        
        for row in data:
            charge_range = row.get('charge_range', '')
            count = int(row.get('count', 0))
            
            # Calculate percentage of total churned customers
            pct = round_fp(safe_div(count, total_churned), 4) or 0.0
            
            # Format according to required schema
            result_item = {
                "range": str(charge_range),
                "count": count,
                "pct": pct
            }
            
            results.append(result_item)
        
        # Ensure all expected monthly charge ranges are present and in correct order
        complete_results = create_complete_monthly_bins(results)
        
        return complete_results
        
    except asyncpg.PostgresError as e:
        raise asyncpg.PostgresError(f"Database error in compute_monthly_bins: {e}")
    except Exception as e:
        raise ValueError(f"Failed to compute monthly bins: {e}")


async def compute_monthly_bins_with_metadata(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Compute monthly bins with additional metadata.
    
    Args:
        conn: Optional asyncpg connection
        
    Returns:
        Dict with monthly bins analysis and metadata:
        {
            "monthly_charge_ranges": [...],
            "metadata": {
                "total_churned_customers": 1869,
                "bins_definition": {...},
                "computed_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        from datetime import datetime
        
        # Get main analysis
        monthly_analysis = await compute_monthly_bins(conn)
        
        # Calculate metadata
        total_churned = sum(item["count"] for item in monthly_analysis)
        monthly_config = get_monthly_bins_definition()
        
        return {
            "monthly_charge_ranges": monthly_analysis,
            "metadata": {
                "total_churned_customers": total_churned,
                "bins_definition": monthly_config,
                "computed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute monthly bins with metadata: {e}")


async def get_monthly_summary_stats(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Get summary statistics for monthly charges analysis.
    
    Returns:
        Dict with summary stats like highest/lowest bins, dominant range, etc.
    """
    try:
        monthly_data = await compute_monthly_bins(conn)
        
        if not monthly_data:
            return {
                "highest_count_range": None,
                "lowest_count_range": None,
                "most_common_charge_range": None,
                "total_churned_analyzed": 0
            }
        
        # Find ranges with highest and lowest counts
        highest_count = max(monthly_data, key=lambda x: x["count"])
        lowest_count = min(monthly_data, key=lambda x: x["count"])
        
        # Find most common charge range (highest percentage)
        most_common = max(monthly_data, key=lambda x: x["pct"])
        
        # Calculate total churned customers
        total_churned = sum(item["count"] for item in monthly_data)
        
        return {
            "highest_count_range": highest_count,
            "lowest_count_range": lowest_count,
            "most_common_charge_range": most_common,
            "total_churned_analyzed": total_churned
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute monthly summary stats: {e}")


async def get_monthly_distribution_insights(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Get insights about monthly charges distribution patterns.
    
    Returns:
        Dict with analytical insights about monthly charge patterns
    """
    try:
        monthly_data = await compute_monthly_bins(conn)
        
        if not monthly_data:
            return {"insights": []}
        
        insights = []
        
        # Analyze low vs high charge churn
        low_ranges = ["0–35", "36–65"]      # Low charges: 0-65
        high_ranges = ["66–95", "96+"]      # High charges: 66+
        
        low_count = sum(item["count"] for item in monthly_data if item["range"] in low_ranges)
        high_count = sum(item["count"] for item in monthly_data if item["range"] in high_ranges)
        total_count = low_count + high_count
        
        if total_count > 0:
            low_pct = round_fp(safe_div(low_count, total_count) * 100, 1)
            high_pct = round_fp(safe_div(high_count, total_count) * 100, 1)
            
            insights.append({
                "type": "low_vs_high_charges_churn",
                "low_charges_pct": low_pct,
                "high_charges_pct": high_pct,
                "insight": f"{low_pct}% of churned customers have low charges ($0-65), {high_pct}% have high charges ($66+)"
            })
        
        # Find dominant charge range
        most_common = max(monthly_data, key=lambda x: x["pct"])
        if most_common["pct"] > 0:
            insights.append({
                "type": "dominant_range",
                "range": most_common["range"],
                "percentage": most_common["pct"] * 100,
                "insight": f"Most churned customers ({most_common['pct']*100:.1f}%) are in the ${most_common['range']} monthly charges range"
            })
        
        return {
            "insights": insights,
            "monthly_charge_distribution": monthly_data
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute monthly distribution insights: {e}")