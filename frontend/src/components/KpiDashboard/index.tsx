'use client';

import React, { useState, useEffect } from 'react';
import KpiCard from '../KpiCard';
import KpiSkeleton from '../KpiSkeleton';

interface KpiData {
  churned_users: number;
  churn_rate_overall: number;
  avg_tenure: number;
  avg_monthly: number;
}

interface KpiResponse {
  kpis: KpiData;
}

const KpiDashboard: React.FC = () => {
  const [kpiData, setKpiData] = useState<KpiData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generate placeholder sparkline data (replace with real historical data later)
  const generateSparklineData = (baseValue: number, variance: number = 0.1): number[] => {
    return Array.from({ length: 12 }, (_, i) => {
      const trend = Math.sin(i * 0.5) * variance;
      const noise = (Math.random() - 0.5) * variance * 0.5;
      return baseValue * (1 + trend + noise);
    });
  };

  // Fetch KPI data from your backend API
  useEffect(() => {
    const fetchKpiData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Your API endpoint - this matches your FastAPI backend
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/churn/kpis`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: KpiResponse = await response.json();
        setKpiData(data.kpis);
      } catch (err) {
        console.error('Error fetching KPI data:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch KPI data');
        setKpiData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchKpiData();

    // Optional: Set up polling for real-time updates
    const interval = setInterval(fetchKpiData, 300000); // 5 minutes
    return () => clearInterval(interval);
  }, []);

  // Formatters for different value types
  const formatters = {
    currency: (value: number | string): string => parseFloat(String(value)).toFixed(2),
    percentage: (value: number | string): string => (parseFloat(String(value)) * 100).toFixed(1),
    number: (value: number | string): string => parseInt(String(value)).toLocaleString(),
    decimal: (value: number | string): string => parseFloat(String(value)).toFixed(1),
  };

  const renderContent = () => {
    // Loading state - FIRST priority (while fetching)
    if (loading) {
      return <KpiSkeleton />;
    }

    // Error or empty state - ONLY after loading completes
    if (error || !kpiData) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, index) => (
            <div key={index} className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="h-32 flex items-center justify-center bg-gray-50 rounded">
                <div className="text-center">
                  <div className="text-gray-400 mb-2">
                    <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="text-sm font-medium text-gray-600">No Data</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      );
    }

    // Loaded data - show actual KPI cards
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard
          title="Churned Users"
          value={kpiData.churned_users}
          formatter={formatters.number}
          trend="down"
          sparklineData={generateSparklineData(kpiData.churned_users, 0.15)}
        />

        <KpiCard
          title="Churn Rate"
          value={kpiData.churn_rate_overall}
          unit="%"
          formatter={formatters.percentage}
          trend="down"
          sparklineData={generateSparklineData(kpiData.churn_rate_overall, 0.2)}
        />

        <KpiCard
          title="Avg Tenure"
          value={kpiData.avg_tenure}
          unit=" months"
          formatter={formatters.decimal}
          trend="up"
          sparklineData={generateSparklineData(kpiData.avg_tenure, 0.1)}
        />

        <KpiCard
          title="Avg Monthly Revenue"
          value={kpiData.avg_monthly}
          prefix="$"
          formatter={formatters.currency}
          trend="up"
          sparklineData={generateSparklineData(kpiData.avg_monthly, 0.12)}
        />
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header - ALWAYS visible */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Key Performance Indicators</h2>
        <div className="text-sm text-gray-500">
          {loading ? (
            <div className="h-4 bg-gray-200 rounded animate-pulse w-32"></div>
          ) : (
            `Last updated: ${new Date().toLocaleTimeString()}`
          )}
        </div>
      </div>

      {/* Dynamic Content */}
      {renderContent()}
    </div>
  );
};

export default KpiDashboard;