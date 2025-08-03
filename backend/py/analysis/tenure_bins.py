#!/usr/bin/env python3
"""
Tenure bins analysis for churned customers.
Analyzes tenure distribution of churned customers in fixed bins: 0–3, 4–6, 7–12, 13–24, 25+.
"""

from typing import List, Dict, Any, Optional
import asyncpg
from ..core.db import fetch_df
from ..core.utils import (
    safe_div, 
    round_fp, 
    get_tenure_bins_definition,
    ensure_tenure_bins_order,
    create_complete_tenure_bins
)


async def compute_tenure_bins(conn: Optional[asyncpg.Connection] = None) -> List[Dict[str, Any]]:
    """
    Compute tenure distribution for churned customers in fixed bins.
    
    This function analyzes churned customers only (WHERE Churn = 'Yes') and bins
    their tenure into fixed ranges: 0–3, 4–6, 7–12, 13–24, 25+ months.
    
    Args:
        conn: Optional asyncpg connection (uses global db if None)
        
    Returns:
        List of dictionaries with tenure bin analysis in fixed order:
        [
            {"range": "0–3", "count": 245, "pct": 0.1311},
            {"range": "4–6", "count": 178, "pct": 0.0952},
            {"range": "7–12", "count": 342, "pct": 0.1830},
            {"range": "13–24", "count": 287, "pct": 0.1536},
            {"range": "25+", "count": 817, "pct": 0.4371}
        ]
        
    Raises:
        asyncpg.PostgresError: For database connection/query errors
        ValueError: For invalid data or computation errors
    """
    
    # Get tenure bins configuration
    tenure_config = get_tenure_bins_definition()
    
    # SQL query to bin churned customers by tenure
    # Only analyze customers who have churned (Churn = 'Yes')
    sql = """
    SELECT 
        CASE 
            WHEN tenure <= 3 THEN '0–3'
            WHEN tenure <= 6 THEN '4–6'
            WHEN tenure <= 12 THEN '7–12'
            WHEN tenure <= 24 THEN '13–24'
            ELSE '25+'
        END as tenure_range,
        COUNT(*) as count
    FROM churn_customers
    WHERE "Churn" = 'Yes' AND tenure IS NOT NULL
    GROUP BY 
        CASE 
            WHEN tenure <= 3 THEN '0–3'
            WHEN tenure <= 6 THEN '4–6'
            WHEN tenure <= 12 THEN '7–12'
            WHEN tenure <= 24 THEN '13–24'
            ELSE '25+'
        END;
    """
    
    try:
        # Get total churned customers for percentage calculation
        total_churned_sql = """
        SELECT COUNT(*) as total_churned
        FROM churn_customers
        WHERE "Churn" = 'Yes' AND tenure IS NOT NULL;
        """
        
        # Fetch data using the global fetch_df function or connection-specific query
        if conn:
            # Use provided connection directly
            rows = await conn.fetch(sql)
            total_result = await conn.fetchval(total_churned_sql)
            
            if not rows:
                # Return empty bins with all ranges having zero counts
                return create_complete_tenure_bins([])
            
            # Convert asyncpg Records to list of dicts
            data = [dict(row) for row in rows]
            total_churned = int(total_result) if total_result else 0
        else:
            # Use global db manager
            df = await fetch_df(sql)
            total_df = await fetch_df(total_churned_sql)
            
            if df.empty:
                # Return empty bins with all ranges having zero counts
                return create_complete_tenure_bins([])
            
            # Convert DataFrame to list of dicts
            data = df.to_dict('records')
            total_churned = int(total_df.iloc[0]['total_churned']) if not total_df.empty else 0
        
        # Process results and calculate percentages
        results = []
        
        for row in data:
            tenure_range = row.get('tenure_range', '')
            count = int(row.get('count', 0))
            
            # Calculate percentage of total churned customers
            pct = round_fp(safe_div(count, total_churned), 4) or 0.0
            
            # Format according to required schema
            result_item = {
                "range": str(tenure_range),
                "count": count,
                "pct": pct
            }
            
            results.append(result_item)
        
        # Ensure all expected tenure ranges are present and in correct order
        complete_results = create_complete_tenure_bins(results)
        
        return complete_results
        
    except asyncpg.PostgresError as e:
        raise asyncpg.PostgresError(f"Database error in compute_tenure_bins: {e}")
    except Exception as e:
        raise ValueError(f"Failed to compute tenure bins: {e}")


async def compute_tenure_bins_with_metadata(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Compute tenure bins with additional metadata.
    
    Args:
        conn: Optional asyncpg connection
        
    Returns:
        Dict with tenure bins analysis and metadata:
        {
            "tenure_ranges": [...],
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
        tenure_analysis = await compute_tenure_bins(conn)
        
        # Calculate metadata
        total_churned = sum(item["count"] for item in tenure_analysis)
        tenure_config = get_tenure_bins_definition()
        
        return {
            "tenure_ranges": tenure_analysis,
            "metadata": {
                "total_churned_customers": total_churned,
                "bins_definition": tenure_config,
                "computed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute tenure bins with metadata: {e}")


async def get_tenure_summary_stats(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Get summary statistics for tenure analysis.
    
    Returns:
        Dict with summary stats like highest/lowest bins, median range, etc.
    """
    try:
        tenure_data = await compute_tenure_bins(conn)
        
        if not tenure_data:
            return {
                "highest_count_range": None,
                "lowest_count_range": None,
                "most_common_tenure_range": None,
                "total_churned_analyzed": 0
            }
        
        # Find ranges with highest and lowest counts
        highest_count = max(tenure_data, key=lambda x: x["count"])
        lowest_count = min(tenure_data, key=lambda x: x["count"])
        
        # Find most common tenure range (highest percentage)
        most_common = max(tenure_data, key=lambda x: x["pct"])
        
        # Calculate total churned customers
        total_churned = sum(item["count"] for item in tenure_data)
        
        return {
            "highest_count_range": highest_count,
            "lowest_count_range": lowest_count,
            "most_common_tenure_range": most_common,
            "total_churned_analyzed": total_churned
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute tenure summary stats: {e}")


async def get_tenure_distribution_insights(conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
    """
    Get insights about tenure distribution patterns.
    
    Returns:
        Dict with analytical insights about tenure patterns
    """
    try:
        tenure_data = await compute_tenure_bins(conn)
        
        if not tenure_data:
            return {"insights": []}
        
        insights = []
        
        # Analyze early vs late tenure churn
        early_ranges = ["0–3", "4–6", "7–12"]  # 0-12 months
        late_ranges = ["13–24", "25+"]         # 13+ months
        
        early_count = sum(item["count"] for item in tenure_data if item["range"] in early_ranges)
        late_count = sum(item["count"] for item in tenure_data if item["range"] in late_ranges)
        total_count = early_count + late_count
        
        if total_count > 0:
            early_pct = round_fp(safe_div(early_count, total_count) * 100, 1)
            late_pct = round_fp(safe_div(late_count, total_count) * 100, 1)
            
            insights.append({
                "type": "early_vs_late_churn",
                "early_churn_pct": early_pct,
                "late_churn_pct": late_pct,
                "insight": f"{early_pct}% of churned customers left within first year, {late_pct}% after first year"
            })
        
        # Find dominant tenure range
        most_common = max(tenure_data, key=lambda x: x["pct"])
        if most_common["pct"] > 0:
            insights.append({
                "type": "dominant_range",
                "range": most_common["range"],
                "percentage": most_common["pct"] * 100,
                "insight": f"Most churned customers ({most_common['pct']*100:.1f}%) are in the {most_common['range']} months tenure range"
            })
        
        return {
            "insights": insights,
            "tenure_distribution": tenure_data
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute tenure distribution insights: {e}")