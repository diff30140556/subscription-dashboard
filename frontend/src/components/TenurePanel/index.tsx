'use client';

import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import { useDashboardStore } from '@/store/dashboardStore';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

interface TenureRangeItem {
  range: string;
  count: number;
  pct: number;
}

interface TenureApiResponse {
  tenure_ranges: TenureRangeItem[];
}

const TenurePanel: React.FC = () => {
  const { isLoading, setLoading } = useDashboardStore();
  const [data, setData] = useState<TenureRangeItem[]>([]);
  const loading = isLoading.tenure;
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading('tenure', true);
        setError(null);

        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/tenure/bins`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result: TenureApiResponse = await response.json();
        setData(result.tenure_ranges || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error('Failed to fetch tenure data:', err);
        setData([]);
      } finally {
        setLoading('tenure', false);
      }
    };

    fetchData();
  }, [setLoading]);

  // Chart data configuration
  const chartData = {
    labels: data.map(item => `${item.range} months`),
    datasets: [
      {
        label: 'Churn Rate (%)',
        data: data.map(item => (item.pct * 100).toFixed(2)),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        fill: false,
        tension: 0.1,
      },
    ],
  };

  // Shared chart options
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const dataIndex = context.dataIndex;
            const item = data[dataIndex];
            return [
              `Churn Rate: ${context.parsed.y}%`,
              `Users: ${item?.count?.toLocaleString() || 0}`
            ];
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
          text: 'Tenure Range (Months)'
        }
      }
    },
  };

  const renderChartContent = (isBarChart: boolean) => {
    if (error || !data || data.length === 0) {
      return (
        <div className="h-80 flex items-center justify-center bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="text-lg font-medium text-gray-600 mb-1">No Data Found</div>
            <div className="text-sm text-gray-500">
              {error ? 'Failed to load tenure data' : 'No tenure range data available'}
            </div>
          </div>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="h-80 bg-gray-200 rounded animate-pulse"></div>
      );
    }

    return (
      <div className="h-80">
        {isBarChart ? (
          <Bar data={chartData} options={baseOptions} />
        ) : (
          <Line data={chartData} options={baseOptions} />
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6 opacity-0 animate-fade-in">
        {/* Title - ALWAYS visible */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Churn Rate by Tenure Range</h1>
        </div>
        
        <LoadingSkeleton title="Tenure Data" rows={3} hasChart={true} />
      </div>
    );
  }

  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      {/* Title - ALWAYS visible */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Churn Rate by Tenure Range</h1>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Bar Chart View
          </h3>
          {renderChartContent(true)}
        </div>
        
        {/* Line Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Trend Line View
          </h3>
          {renderChartContent(false)}
        </div>
      </div>

      {/* Summary Statistics */}
      {data && data.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tenure Range Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {data.map((item) => (
              <div key={item.range} className="text-center p-3 border rounded-lg">
                <div className="text-sm font-medium text-gray-700 mb-1">{item.range} months</div>
                <div className="text-xl font-bold text-blue-600 mb-1">
                  {(item.pct * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">
                  {item.count.toLocaleString()} users
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TenurePanel;