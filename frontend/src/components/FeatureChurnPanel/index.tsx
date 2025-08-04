'use client';

import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface FeatureChurnItem {
  key: string;
  churn_rate: number;
  n: number;
}

interface FeatureChurnData {
  churn_rate_by_feature: {
    [feature: string]: FeatureChurnItem[];
  };
}

interface FeatureSummaryData {
  best_feature_for_retention: {
    feature: string;
    churn_reduction: number;
    yes_churn_rate: number;
    no_churn_rate: number;
    yes_count: number;
    no_count: number;
  };
  worst_feature_for_retention: {
    feature: string;
    churn_reduction: number;
    yes_churn_rate: number;
    no_churn_rate: number;
    yes_count: number;
    no_count: number;
  };
  feature_impact_summary: Array<{
    feature: string;
    churn_reduction: number;
    yes_churn_rate: number;
    no_churn_rate: number;
    yes_count: number;
    no_count: number;
  }>;
}

const FeatureChurnPanel: React.FC = () => {
  const [featureData, setFeatureData] = useState<FeatureChurnData | null>(null);
  const [summaryData, setSummaryData] = useState<FeatureSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        // Fetch both APIs simultaneously
        const [featureResponse, summaryResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/features/churn`),
          fetch(`${API_BASE_URL}/api/features/churn/summary`)
        ]);

        if (!featureResponse.ok) {
          throw new Error(`Features API error! status: ${featureResponse.status}`);
        }
        if (!summaryResponse.ok) {
          throw new Error(`Summary API error! status: ${summaryResponse.status}`);
        }

        const featureResult: FeatureChurnData = await featureResponse.json();
        const summaryResult: FeatureSummaryData = await summaryResponse.json();

        setFeatureData(featureResult);
        setSummaryData(summaryResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error('Failed to fetch feature churn data:', err);
        setFeatureData(null);
        setSummaryData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Prepare chart data
  const prepareChartData = () => {
    if (!featureData?.churn_rate_by_feature) return null;

    const features = Object.keys(featureData.churn_rate_by_feature);
    const yesData: number[] = [];
    const noData: number[] = [];
    const yesCountsData: number[] = [];
    const noCountsData: number[] = [];

    features.forEach(feature => {
      const featureItems = featureData.churn_rate_by_feature[feature];
      const yesItem = featureItems.find(item => item.key === 'Yes');
      const noItem = featureItems.find(item => item.key === 'No');
      
      yesData.push(yesItem ? (yesItem.churn_rate * 100) : 0);
      noData.push(noItem ? (noItem.churn_rate * 100) : 0);
      yesCountsData.push(yesItem ? yesItem.n : 0);
      noCountsData.push(noItem ? noItem.n : 0);
    });

    return {
      labels: features,
      datasets: [
        {
          label: 'With Feature (Yes)',
          data: yesData,
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          borderColor: 'rgba(34, 197, 94, 1)',
          borderWidth: 2,
          counts: yesCountsData,
        },
        {
          label: 'Without Feature (No)',
          data: noData,
          backgroundColor: 'rgba(239, 68, 68, 0.8)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 2,
          counts: noCountsData,
        },
      ],
    };
  };

  const chartData = prepareChartData();

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const datasetLabel = context.dataset.label;
            const value = context.parsed.y;
            const count = context.dataset.counts[context.dataIndex];
            const featureName = context.label;
            const hasFeature = datasetLabel.includes('Yes') ? 'Yes' : 'No';
            
            return `${hasFeature}: ${value.toFixed(1)}% churn from ${count.toLocaleString()} customers`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value: any) {
            return value + '%';
          }
        },
        title: {
          display: true,
          text: 'Churn Rate (%)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Features'
        }
      }
    },
  };

  const renderChartContent = () => {
    if (loading) {
      return (
        <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
      );
    }

    if (error || !chartData) {
      return (
        <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="text-lg font-medium text-gray-600 mb-1">No Data Found</div>
            <div className="text-sm text-gray-500">
              {error ? 'Failed to load feature churn data' : 'No feature data available'}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="h-96">
        <Bar data={chartData} options={chartOptions} />
      </div>
    );
  };

  const renderSummaryContent = () => {
    if (loading) {
      return (
        <div className="space-y-4">
          {[...Array(3)].map((_, index) => (
            <div key={index} className="bg-gray-200 rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-300 rounded mb-2"></div>
              <div className="h-6 bg-gray-300 rounded mb-1"></div>
              <div className="h-3 bg-gray-300 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      );
    }

    if (!summaryData) {
      return (
        <div className="text-center text-gray-500 py-8">
          No summary data available
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {/* Best Feature for Retention */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm font-medium text-green-700 mb-1">🏆 Best Feature for Retention</div>
              <div className="text-xl font-bold text-green-900 mb-2">
                {summaryData.best_feature_for_retention.feature}
              </div>
              <div className="text-sm text-green-600">
                Reduces churn by <strong>{((summaryData.best_feature_for_retention.churn_reduction || 0) * 100).toFixed(1)}%</strong>
              </div>
              <div className="text-xs text-green-500 mt-1">
                With: {((summaryData.best_feature_for_retention.yes_churn_rate || 0) * 100).toFixed(1)}% churn ({summaryData.best_feature_for_retention.yes_count?.toLocaleString() || 'N/A'} customers) • 
                Without: {((summaryData.best_feature_for_retention.no_churn_rate || 0) * 100).toFixed(1)}% churn ({summaryData.best_feature_for_retention.no_count?.toLocaleString() || 'N/A'} customers)
              </div>
            </div>
          </div>
        </div>

        {/* Worst Feature for Retention */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm font-medium text-red-700 mb-1">⚠️ Worst Feature for Retention</div>
              <div className="text-xl font-bold text-red-900 mb-2">
                {summaryData.worst_feature_for_retention.feature}
              </div>
              <div className="text-sm text-red-600">
                Reduces churn by only <strong>{((summaryData.worst_feature_for_retention.churn_reduction || 0) * 100).toFixed(1)}%</strong>
              </div>
              <div className="text-xs text-red-500 mt-1">
                With: {((summaryData.worst_feature_for_retention.yes_churn_rate || 0) * 100).toFixed(1)}% churn ({summaryData.worst_feature_for_retention.yes_count?.toLocaleString() || 'N/A'} customers) • 
                Without: {((summaryData.worst_feature_for_retention.no_churn_rate || 0) * 100).toFixed(1)}% churn ({summaryData.worst_feature_for_retention.no_count?.toLocaleString() || 'N/A'} customers)
              </div>
            </div>
          </div>
        </div>

        {/* All Features Summary */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-700 mb-3">All Features Impact</div>
          <div className="space-y-2">
            {summaryData.feature_impact_summary.map((feature, index) => (
              <div key={index} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0">
                <div className="font-medium text-gray-900">{feature.feature}</div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-gray-700">
                    -{((feature.churn_reduction || 0) * 100).toFixed(1)}% churn reduction
                  </div>
                  <div className="text-xs text-gray-500">
                    {((feature.yes_count || 0) + (feature.no_count || 0)).toLocaleString()} total customers
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6 opacity-0 animate-fade-in">
        {/* Title - ALWAYS visible */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Feature Impact on Churn</h1>
        </div>
        
        {/* Chart Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Churn Rate by Feature Availability
          </h3>
          <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
        </div>

        {/* Summary Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Retention Analysis</h3>
          {renderSummaryContent()}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      {/* Title - ALWAYS visible */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Feature Impact on Churn</h1>
      </div>

      {/* Chart Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Churn Rate by Feature Availability
        </h3>
        {renderChartContent()}
      </div>

      {/* Summary Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Retention Analysis</h3>
        {renderSummaryContent()}
      </div>
    </div>
  );
};

export default FeatureChurnPanel;