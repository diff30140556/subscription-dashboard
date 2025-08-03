#!/usr/bin/env python3
"""
Service features churn analysis.
Analyzes churn rates by service add-ons and features like OnlineSecurity, TechSupport, etc.
"""

from typing import Dict, Any, List, Optional
import asyncpg
from ..core.db import fetch_df
from ..core.utils import safe_div, round_fp


# Whitelist of allowed feature columns for security (prevents SQL injection)
ALLOWED_FEATURES = {
    "OnlineSecurity": "OnlineSecurity",
    "TechSupport": "TechSupport", 
    "OnlineBackup": "OnlineBackup",
    "DeviceProtection": "DeviceProtection",
    "StreamingTV": "StreamingTV",
    "StreamingMovies": "StreamingMovies",
    "InternetService": "InternetService",
    "PhoneService": "PhoneService",
    "MultipleLines": "MultipleLines",
    "PaperlessBilling": "PaperlessBilling"
}

DEFAULT_FEATURES = ["OnlineSecurity", "TechSupport"]


def validate_features(features: List[str]) -> List[str]:
    """
    Validate and filter feature names against whitelist.
    
    Args:
        features: List of feature names to validate
        
    Returns:
        List of valid feature names from whitelist
        
    Raises:
        ValueError: If no valid features provided
    """
    if not features:
        return DEFAULT_FEATURES
    
    valid_features = [f for f in features if f in ALLOWED_FEATURES]
    
    if not valid_features:
        raise ValueError(f"No valid features provided. Allowed features: {list(ALLOWED_FEATURES.keys())}")
    
    return valid_features


async def compute_feature_churn(conn: Optional[asyncpg.Connection] = None, features: List[str] = None) -> Dict[str, Any]:
    """
    Compute churn rates by service features/add-ons.
    
    Analyzes churn rates for different service features, treating NULL values as "No".
    Returns churn rates for each feature value (Yes/No) in fixed order.
    
    Args:
        conn: Optional asyncpg connection (uses global db if None)
        features: List of feature column names to analyze (default: OnlineSecurity, TechSupport)
        
    Returns:
        Dict with churn analysis by feature:
        {
            "churn_rate_by_feature": {
                "OnlineSecurity": [
                    {"key": "Yes", "churn_rate": 0.1500, "n": 200},
                    {"key": "No", "churn_rate": 0.3200, "n": 1500}
                ],
                "TechSupport": [
                    {"key": "Yes", "churn_rate": 0.1200, "n": 180},
                    {"key": "No", "churn_rate": 0.2800, "n": 1520}
                ]
            }
        }
        
    Raises:
        ValueError: For invalid features or computation errors
        asyncpg.PostgresError: For database connection/query errors
    """
    
    # Validate and filter features
    if features is None:
        features = DEFAULT_FEATURES
    
    valid_features = validate_features(features)
    
    result = {"churn_rate_by_feature": {}}
    
    try:
        # Process each feature separately to avoid complex dynamic SQL
        for feature in valid_features:
            column_name = ALLOWED_FEATURES[feature]
            
            # SQL query to analyze churn by feature value
            # Treat NULL as "No" using COALESCE
            # Use quoted column names for case sensitivity
            sql = f"""
            SELECT 
                COALESCE("{column_name}", 'No') as feature_value,
                COUNT(*) as total_customers,
                SUM(CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END) as churned_customers
            FROM churn_customers
            WHERE "{column_name}" IS NOT NULL OR "{column_name}" IS NULL
            GROUP BY COALESCE("{column_name}", 'No')
            ORDER BY COALESCE("{column_name}", 'No');
            """
            
            # Fetch data using the global fetch_df function or connection-specific query
            if conn:
                # Use provided connection directly
                rows = await conn.fetch(sql)
                
                if not rows:
                    # Return empty result for this feature
                    result["churn_rate_by_feature"][feature] = [
                        {"key": "Yes", "churn_rate": 0.0, "n": 0},
                        {"key": "No", "churn_rate": 0.0, "n": 0}
                    ]
                    continue
                
                # Convert asyncpg Records to list of dicts
                data = [dict(row) for row in rows]
            else:
                # Use global db manager
                df = await fetch_df(sql)
                
                if df.empty:
                    # Return empty result for this feature
                    result["churn_rate_by_feature"][feature] = [
                        {"key": "Yes", "churn_rate": 0.0, "n": 0},
                        {"key": "No", "churn_rate": 0.0, "n": 0}
                    ]
                    continue
                
                # Convert DataFrame to list of dicts
                data = df.to_dict('records')
            
            # Process results and calculate churn rates
            feature_results = {}
            
            for row in data:
                feature_value = row.get('feature_value', 'No')
                total_customers = int(row.get('total_customers', 0))
                churned_customers = int(row.get('churned_customers', 0))
                
                # Calculate churn rate
                churn_rate = round_fp(safe_div(churned_customers, total_customers), 4) or 0.0
                
                feature_results[feature_value] = {
                    "key": feature_value,
                    "churn_rate": churn_rate,
                    "n": total_customers
                }
            
            # Ensure both "Yes" and "No" are present in fixed order
            ordered_results = []
            
            # Always return "Yes" first, then "No"
            for key in ["Yes", "No"]:
                if key in feature_results:
                    ordered_results.append(feature_results[key])
                else:
                    # Add missing key with zero values
                    ordered_results.append({
                        "key": key,
                        "churn_rate": 0.0,
                        "n": 0
                    })
            
            result["churn_rate_by_feature"][feature] = ordered_results
            
    except asyncpg.PostgresError as e:
        raise asyncpg.PostgresError(f"Database error in compute_feature_churn: {e}")
    except Exception as e:
        raise ValueError(f"Failed to compute feature churn analysis: {e}")
    
    return result


async def compute_feature_churn_with_metadata(conn: Optional[asyncpg.Connection] = None, features: List[str] = None) -> Dict[str, Any]:
    """
    Compute feature churn analysis with additional metadata.
    
    Args:
        conn: Optional asyncpg connection
        features: List of feature names to analyze
        
    Returns:
        Dict with feature churn analysis and metadata
    """
    try:
        from datetime import datetime
        
        # Get main analysis
        churn_analysis = await compute_feature_churn(conn, features)
        
        # Calculate metadata
        analyzed_features = list(churn_analysis["churn_rate_by_feature"].keys())
        total_combinations = sum([
            sum([item["n"] for item in feature_data])
            for feature_data in churn_analysis["churn_rate_by_feature"].values()
        ])
        
        return {
            **churn_analysis,
            "metadata": {
                "analyzed_features": analyzed_features,
                "total_feature_combinations": total_combinations,
                "available_features": list(ALLOWED_FEATURES.keys()),
                "computed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute feature churn with metadata: {e}")


async def get_feature_churn_summary(conn: Optional[asyncpg.Connection] = None, features: List[str] = None) -> Dict[str, Any]:
    """
    Get summary statistics for feature churn analysis.
    
    Returns:
        Dict with summary stats like best/worst performing features
    """
    try:
        churn_data = await compute_feature_churn(conn, features)
        
        if not churn_data["churn_rate_by_feature"]:
            return {
                "best_feature_for_retention": None,
                "worst_feature_for_retention": None,
                "feature_impact_summary": []
            }
        
        feature_impacts = []
        
        # Analyze each feature's impact on churn
        for feature_name, feature_data in churn_data["churn_rate_by_feature"].items():
            yes_data = next((item for item in feature_data if item["key"] == "Yes"), None)
            no_data = next((item for item in feature_data if item["key"] == "No"), None)
            
            if yes_data and no_data and yes_data["n"] > 0 and no_data["n"] > 0:
                # Calculate the difference in churn rates (No churn rate - Yes churn rate)
                # Positive value means feature reduces churn (good)
                churn_reduction = no_data["churn_rate"] - yes_data["churn_rate"]
                
                feature_impacts.append({
                    "feature": feature_name,
                    "yes_churn_rate": yes_data["churn_rate"],
                    "no_churn_rate": no_data["churn_rate"],
                    "churn_reduction": round_fp(churn_reduction, 4),
                    "yes_customers": yes_data["n"],
                    "no_customers": no_data["n"]
                })
        
        # Sort by churn reduction (best retention features first)
        feature_impacts.sort(key=lambda x: x["churn_reduction"], reverse=True)
        
        return {
            "best_feature_for_retention": feature_impacts[0] if feature_impacts else None,
            "worst_feature_for_retention": feature_impacts[-1] if feature_impacts else None,
            "feature_impact_summary": feature_impacts
        }
        
    except Exception as e:
        raise ValueError(f"Failed to compute feature churn summary: {e}")


def get_allowed_features() -> List[str]:
    """
    Get list of allowed feature column names.
    
    Returns:
        List of allowed feature names for API validation
    """
    return list(ALLOWED_FEATURES.keys())