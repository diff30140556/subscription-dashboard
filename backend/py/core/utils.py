#!/usr/bin/env python3
"""
Core utility functions for safe mathematical operations and data processing.
Production-ready with comprehensive error handling and type safety.
"""

from typing import Union, Optional, Any, List, Dict
import math
import pandas as pd


def safe_div(
    numerator: Union[int, float, None],
    denominator: Union[int, float, None],
    default: float = 0.0,
) -> float:
    """
    Safely divide two numbers, handling division by zero and null values.

    Args:
        numerator: The dividend (can be None)
        denominator: The divisor (can be None)
        default: Default value to return for invalid operations

    Returns:
        Result of division or default value

    Examples:
        >>> safe_div(10, 2)
        5.0
        >>> safe_div(10, 0)
        0.0
        >>> safe_div(None, 5)
        0.0
        >>> safe_div(10, None, -1.0)
        -1.0
    """
    if numerator is None or denominator is None:
        return default

    try:
        num = float(numerator)
        den = float(denominator)

        # Check for division by zero or very small numbers
        if abs(den) < 1e-10:
            return default

        result = num / den

        # Check for invalid results (inf, -inf, nan)
        if not math.isfinite(result):
            return default

        return result

    except (ValueError, TypeError, OverflowError):
        return default


def round_fp(value: Union[int, float, None], decimals: int = 4) -> Optional[float]:
    """
    Round floating point number to specified decimal places with null safety.

    Args:
        value: Number to round (can be None)
        decimals: Number of decimal places (default: 4)

    Returns:
        Rounded number or None if input was None/invalid

    Examples:
        >>> round_fp(3.14159, 2)
        3.14
        >>> round_fp(None)
        None
        >>> round_fp(float('inf'))
        None
    """
    if value is None:
        return None

    try:
        num = float(value)

        # Check for invalid numbers
        if not math.isfinite(num):
            return None

        return round(num, decimals)

    except (ValueError, TypeError, OverflowError):
        return None


def safe_mean(
    values: List[Union[int, float, None]], skip_nulls: bool = True
) -> Optional[float]:
    """
    Calculate mean of a list with null safety and optional null handling.

    Args:
        values: List of numeric values (may contain None)
        skip_nulls: Whether to skip None values (default: True)

    Returns:
        Mean value or None if no valid values

    Examples:
        >>> safe_mean([1, 2, 3, 4, 5])
        3.0
        >>> safe_mean([1, None, 3, None, 5])
        3.0
        >>> safe_mean([None, None])
        None
    """
    if not values:
        return None

    if skip_nulls:
        valid_values = [v for v in values if v is not None]
    else:
        valid_values = values

    if not valid_values:
        return None

    try:
        numeric_values = [float(v) for v in valid_values if v is not None]
        finite_values = [v for v in numeric_values if math.isfinite(v)]

        if not finite_values:
            return None

        return sum(finite_values) / len(finite_values)

    except (ValueError, TypeError):
        return None


def safe_sum(values: List[Union[int, float, None]], skip_nulls: bool = True) -> float:
    """
    Calculate sum of a list with null safety.

    Args:
        values: List of numeric values (may contain None)
        skip_nulls: Whether to skip None values (default: True)

    Returns:
        Sum of valid values (0.0 if no valid values)

    Examples:
        >>> safe_sum([1, 2, 3, None, 5])
        11.0
        >>> safe_sum([None, None])
        0.0
    """
    if not values:
        return 0.0

    if skip_nulls:
        valid_values = [v for v in values if v is not None]
    else:
        valid_values = values

    try:
        numeric_values = [float(v) for v in valid_values if v is not None]
        finite_values = [v for v in numeric_values if math.isfinite(v)]

        return sum(finite_values)

    except (ValueError, TypeError):
        return 0.0


def safe_count(values: List[Any], condition_func: Optional[callable] = None) -> int:
    """
    Count values in a list with optional condition function.

    Args:
        values: List of values to count
        condition_func: Optional function to filter values

    Returns:
        Count of values meeting condition

    Examples:
        >>> safe_count([1, 2, None, 4, 5])
        5
        >>> safe_count([1, 2, None, 4, 5], lambda x: x is not None)
        4
        >>> safe_count(['Yes', 'No', 'Yes'], lambda x: x == 'Yes')
        2
    """
    if not values:
        return 0

    if condition_func is None:
        return len(values)

    try:
        return len([v for v in values if condition_func(v)])
    except Exception:
        return 0


def clean_numeric_column(
    df: pd.DataFrame,
    column: str,
    errors: str = "coerce",
    fill_value: Optional[float] = None,
) -> pd.Series:
    """
    Clean and convert a DataFrame column to numeric with error handling.

    Args:
        df: Input DataFrame
        column: Column name to clean
        errors: How to handle errors ('coerce', 'raise', 'ignore')
        fill_value: Value to fill NaN with (None to keep NaN)

    Returns:
        Cleaned numeric Series

    Examples:
        >>> df = pd.DataFrame({'col': ['1', '2.5', 'invalid', None]})
        >>> clean_numeric_column(df, 'col', fill_value=0)
        0    1.0
        1    2.5
        2    0.0
        3    0.0
        Name: col, dtype: float64
    """
    if column not in df.columns:
        return pd.Series(dtype=float)

    try:
        # Convert to numeric
        series = pd.to_numeric(df[column], errors=errors)

        # Fill NaN values if requested
        if fill_value is not None:
            series = series.fillna(fill_value)

        return series

    except Exception:
        # Return series of NaN if conversion fails
        return pd.Series([float("nan")] * len(df))


def create_bins(
    values: pd.Series,
    bins: List[Union[int, float]],
    labels: Optional[List[str]] = None,
    include_lowest: bool = True,
) -> pd.Series:
    """
    Create bins from continuous values with error handling.

    Args:
        values: Series of numeric values to bin
        bins: List of bin edges
        labels: Optional list of bin labels
        include_lowest: Whether to include lowest value in first bin

    Returns:
        Series with binned categories

    Examples:
        >>> values = pd.Series([1, 15, 25, 50, 100])
        >>> bins = [0, 12, 24, 48, 120]
        >>> labels = ['0-12', '13-24', '25-48', '49+']
        >>> create_bins(values, bins, labels)
        0      0-12
        1     13-24
        2     25-48
        3       49+
        4       49+
        dtype: category
    """
    try:
        return pd.cut(
            values,
            bins=bins,
            labels=labels,
            include_lowest=include_lowest,
            duplicates="drop",
        )
    except Exception:
        # Return series of NaN if binning fails
        return pd.Series([None] * len(values), dtype="category")


def get_tenure_bins_definition() -> Dict[str, Any]:
    """
    Get the standard tenure bins definition for consistent use across the application.
    
    Returns:
        Dict with tenure bins configuration:
        {
            "edges": [0, 3, 6, 12, 24, 999],
            "labels": ["0–3", "4–6", "7–12", "13–24", "25+"],
            "order": ["0–3", "4–6", "7–12", "13–24", "25+"]
        }
    """
    return {
        "edges": [0, 3, 6, 12, 24, 999],  # 999 represents max tenure
        "labels": ["0–3", "4–6", "7–12", "13–24", "25+"],
        "order": ["0–3", "4–6", "7–12", "13–24", "25+"]
    }


def ensure_tenure_bins_order(bins_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure tenure bins are returned in the correct fixed order.
    
    Args:
        bins_data: List of dictionaries with 'range' key
        
    Returns:
        List sorted according to standard tenure bins order
        
    Examples:
        >>> data = [{"range": "25+", "count": 10}, {"range": "0–3", "count": 20}]
        >>> ensure_tenure_bins_order(data)
        [{"range": "0–3", "count": 20}, {"range": "25+", "count": 10}]
    """
    tenure_definition = get_tenure_bins_definition()
    expected_order = tenure_definition["order"]
    
    # Create a mapping of range to its position in expected order
    order_map = {range_name: idx for idx, range_name in enumerate(expected_order)}
    
    # Sort the bins_data according to the expected order
    # Missing ranges will be sorted to the end
    def sort_key(item):
        range_name = item.get("range", "")
        return order_map.get(range_name, len(expected_order))
    
    return sorted(bins_data, key=sort_key)


def create_complete_tenure_bins(bins_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create a complete tenure bins array with all expected ranges, filling missing ones.
    
    Args:
        bins_data: List of tenure bin dictionaries
        
    Returns:
        Complete list with all 5 tenure ranges in correct order
    """
    tenure_definition = get_tenure_bins_definition()
    expected_ranges = tenure_definition["order"]
    
    # Create a mapping from existing data
    data_map = {item.get("range"): item for item in bins_data}
    
    # Build complete result with all expected ranges
    complete_bins = []
    for range_name in expected_ranges:
        if range_name in data_map:
            complete_bins.append(data_map[range_name])
        else:
            # Add missing range with zero values
            complete_bins.append({
                "range": range_name,
                "count": 0,
                "pct": 0.0
            })
    
    return complete_bins


def get_monthly_bins_definition() -> Dict[str, Any]:
    """
    Get the standard monthly charges bins definition for consistent use across the application.
    
    Returns:
        Dict with monthly charges bins configuration:
        {
            "edges": [0, 35, 65, 95, 999],
            "labels": ["0–35", "36–65", "66–95", "96+"],
            "order": ["0–35", "36–65", "66–95", "96+"]
        }
    """
    return {
        "edges": [0, 35, 65, 95, 999],  # 999 represents max monthly charges
        "labels": ["0–35", "36–65", "66–95", "96+"],
        "order": ["0–35", "36–65", "66–95", "96+"]
    }


def ensure_monthly_bins_order(bins_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure monthly bins are returned in the correct fixed order.
    
    Args:
        bins_data: List of dictionaries with 'range' key
        
    Returns:
        List sorted according to standard monthly bins order
        
    Examples:
        >>> data = [{"range": "96+", "count": 10}, {"range": "0–35", "count": 20}]
        >>> ensure_monthly_bins_order(data)
        [{"range": "0–35", "count": 20}, {"range": "96+", "count": 10}]
    """
    monthly_definition = get_monthly_bins_definition()
    expected_order = monthly_definition["order"]
    
    # Create a mapping of range to its position in expected order
    order_map = {range_name: idx for idx, range_name in enumerate(expected_order)}
    
    # Sort the bins_data according to the expected order
    # Missing ranges will be sorted to the end
    def sort_key(item):
        range_name = item.get("range", "")
        return order_map.get(range_name, len(expected_order))
    
    return sorted(bins_data, key=sort_key)


def create_complete_monthly_bins(bins_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create a complete monthly bins array with all expected ranges, filling missing ones.
    
    Args:
        bins_data: List of monthly bin dictionaries
        
    Returns:
        Complete list with all 4 monthly charge ranges in correct order
    """
    monthly_definition = get_monthly_bins_definition()
    expected_ranges = monthly_definition["order"]
    
    # Create a mapping from existing data
    data_map = {item.get("range"): item for item in bins_data}
    
    # Build complete result with all expected ranges
    complete_bins = []
    for range_name in expected_ranges:
        if range_name in data_map:
            complete_bins.append(data_map[range_name])
        else:
            # Add missing range with zero values
            complete_bins.append({
                "range": range_name,
                "count": 0,
                "pct": 0.0
            })
    
    return complete_bins
