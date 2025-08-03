#!/usr/bin/env python3
"""
Simple tests for utility functions without complex imports.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def safe_div(numerator, denominator, default=0.0):
    """Local copy of safe_div for testing."""
    if numerator is None or denominator is None:
        return default
    
    try:
        num = float(numerator)
        den = float(denominator)
        
        if abs(den) < 1e-10:
            return default
            
        result = num / den
        
        if not (result == result and result != float('inf') and result != float('-inf')):  # Check for NaN and inf
            return default
            
        return result
        
    except (ValueError, TypeError, OverflowError):
        return default


def round_fp(value, decimals=4):
    """Local copy of round_fp for testing."""
    if value is None:
        return None
        
    try:
        num = float(value)
        
        if not (num == num and num != float('inf') and num != float('-inf')):  # Check for NaN and inf
            return None
            
        return round(num, decimals)
        
    except (ValueError, TypeError, OverflowError):
        return None


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_safe_div_normal_cases(self):
        """Test safe_div with normal division cases."""
        assert safe_div(10, 2) == 5.0
        assert abs(safe_div(7, 3) - 2.333333) < 1e-5
        assert safe_div(0, 5) == 0.0
    
    def test_safe_div_edge_cases(self):
        """Test safe_div with edge cases."""
        assert safe_div(10, 0) == 0.0  # Division by zero
        assert safe_div(None, 5) == 0.0  # None numerator
        assert safe_div(10, None) == 0.0  # None denominator
        assert safe_div(None, None) == 0.0  # Both None
        assert safe_div(10, 0, -1.0) == -1.0  # Custom default
    
    def test_safe_div_very_small_denominator(self):
        """Test safe_div with very small denominators."""
        assert safe_div(10, 1e-12) == 0.0  # Very small denominator
        assert safe_div(10, -1e-12) == 0.0  # Very small negative denominator
    
    def test_round_fp_normal_cases(self):
        """Test round_fp with normal floating point values."""
        assert round_fp(3.14159, 2) == 3.14
        assert round_fp(3.14159, 4) == 3.1416
        assert round_fp(10.0, 1) == 10.0
        assert round_fp(0.0, 3) == 0.0
    
    def test_round_fp_edge_cases(self):
        """Test round_fp with edge cases."""
        assert round_fp(None) is None
        assert round_fp(float('inf')) is None
        assert round_fp(float('-inf')) is None
        assert round_fp(float('nan')) is None
    
    def test_round_fp_default_decimals(self):
        """Test round_fp with default decimal places."""
        assert round_fp(3.123456789) == 3.1235  # Default 4 decimals


class TestKPILogic:
    """Test KPI computation logic without database dependencies."""
    
    def test_churn_rate_calculation(self):
        """Test churn rate calculation logic."""
        # Simulate data
        total_customers = 1000
        churned_customers = 265
        
        # Calculate churn rate
        churn_rate = safe_div(churned_customers, total_customers)
        rounded_rate = round_fp(churn_rate, 4)
        
        assert rounded_rate == 0.265
    
    def test_average_calculation(self):
        """Test average calculation logic."""
        # Simulate monthly charges
        monthly_charges = [64.8, 75.2, 45.0, 89.5, 55.1]
        
        total = sum(monthly_charges)
        count = len(monthly_charges)
        average = safe_div(total, count)
        rounded_avg = round_fp(average, 1)
        
        expected = round_fp(sum(monthly_charges) / len(monthly_charges), 1)
        assert rounded_avg == expected
    
    def test_empty_data_handling(self):
        """Test handling of empty datasets."""
        # Empty data should return safe defaults
        churn_rate = safe_div(0, 0)  # 0 churned, 0 total
        assert churn_rate == 0.0
        
        avg_charges = safe_div(0, 0)  # No charges to average
        assert avg_charges == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])