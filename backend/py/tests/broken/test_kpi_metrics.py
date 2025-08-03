#!/usr/bin/env python3
"""
Tests for KPI metrics computation.
Uses pytest with async support and mock data for testing compute_kpis function.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.kpi_metrics import compute_kpis
from core.utils import safe_div, round_fp


class TestKPIMetrics:
    """Test class for KPI metrics computation."""
    
    @pytest.mark.asyncio
    async def test_compute_kpis_with_valid_data(self):
        """Test compute_kpis with valid customer data."""
        # Mock data representing query results
        mock_data = {
            'total_customers': 1000,
            'churned_count': 250,
            'avg_tenure_raw': 32.456789,
            'avg_monthly_raw': 64.789123,
            'churn_rate_raw': 0.25
        }
        
        # Create mock connection
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_data
        
        # Call function
        result = await compute_kpis(mock_conn)
        
        # Assertions
        assert "kpis" in result
        kpis = result["kpis"]
        
        assert kpis["churned_users"] == 250
        assert kpis["churn_rate_overall"] == 0.25  # Should be rounded to 4 decimals
        assert kpis["avg_tenure"] == 32.5  # Should be rounded to 1 decimal
        assert kpis["avg_monthly"] == 64.8  # Should be rounded to 1 decimal
        
        # Verify mock was called correctly
        mock_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compute_kpis_with_zero_customers(self):
        """Test compute_kpis when no customers exist."""
        mock_data = {
            'total_customers': 0,
            'churned_count': 0,
            'avg_tenure_raw': None,
            'avg_monthly_raw': None,
            'churn_rate_raw': 0.0
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_data
        
        result = await compute_kpis(mock_conn)
        
        kpis = result["kpis"]
        assert kpis["churned_users"] == 0
        assert kpis["churn_rate_overall"] == 0.0
        assert kpis["avg_tenure"] == 0.0
        assert kpis["avg_monthly"] == 0.0
    
    @pytest.mark.asyncio
    async def test_compute_kpis_with_null_averages(self):
        """Test compute_kpis when average values are NULL."""
        mock_data = {
            'total_customers': 100,
            'churned_count': 30,
            'avg_tenure_raw': None,
            'avg_monthly_raw': None,
            'churn_rate_raw': 0.3
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_data
        
        result = await compute_kpis(mock_conn)
        
        kpis = result["kpis"]
        assert kpis["churned_users"] == 30
        assert kpis["churn_rate_overall"] == 0.3
        assert kpis["avg_tenure"] == 0.0  # Should default to 0.0 for NULL
        assert kpis["avg_monthly"] == 0.0  # Should default to 0.0 for NULL
    
    @pytest.mark.asyncio
    async def test_compute_kpis_with_high_precision_values(self):
        """Test compute_kpis with high precision floating point values."""
        mock_data = {
            'total_customers': 7043,
            'churned_count': 1869,
            'avg_tenure_raw': 32.421875,
            'avg_monthly_raw': 64.761904,
            'churn_rate_raw': 0.2654321098765432
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_data
        
        result = await compute_kpis(mock_conn)
        
        kpis = result["kpis"]
        assert kpis["churned_users"] == 1869
        assert kpis["churn_rate_overall"] == 0.2654  # Rounded to 4 decimals
        assert kpis["avg_tenure"] == 32.4  # Rounded to 1 decimal
        assert kpis["avg_monthly"] == 64.8  # Rounded to 1 decimal
    
    @pytest.mark.asyncio
    async def test_compute_kpis_database_error(self):
        """Test compute_kpis when database query fails."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = Exception("Database connection lost")
        
        with pytest.raises(ValueError, match="Failed to compute KPIs"):
            await compute_kpis(mock_conn)
    
    @pytest.mark.asyncio
    async def test_compute_kpis_no_data_returned(self):
        """Test compute_kpis when query returns no data."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        
        with pytest.raises(ValueError, match="No data returned from churn_customers table"):
            await compute_kpis(mock_conn)
    
    @pytest.mark.asyncio
    async def test_compute_kpis_without_connection(self):
        """Test compute_kpis using global db manager (no connection parameter)."""
        # Mock the global fetch_df function
        import analysis.kpi_metrics as kpi_module
        
        # Create mock DataFrame
        mock_df = pd.DataFrame([{
            'total_customers': 500,
            'churned_count': 125,
            'avg_tenure_raw': 28.5,
            'avg_monthly_raw': 55.0,
            'churn_rate_raw': 0.25
        }])
        
        # Patch the fetch_df function
        original_fetch_df = kpi_module.fetch_df
        kpi_module.fetch_df = AsyncMock(return_value=mock_df)
        
        try:
            result = await compute_kpis()
            
            kpis = result["kpis"]
            assert kpis["churned_users"] == 125
            assert kpis["churn_rate_overall"] == 0.25
            assert kpis["avg_tenure"] == 28.5
            assert kpis["avg_monthly"] == 55.0
            
        finally:
            # Restore original function
            kpi_module.fetch_df = original_fetch_df


class TestUtilityFunctions:
    """Test utility functions used in KPI computation."""
    
    def test_safe_div_normal_cases(self):
        """Test safe_div with normal division cases."""
        assert safe_div(10, 2) == 5.0
        assert safe_div(7, 3) == pytest.approx(2.333333, abs=1e-5)
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


# Pytest configuration and fixtures
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])