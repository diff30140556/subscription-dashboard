'use client';

import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

interface MonthlyChargeRange {
  range: string;
  count: number;
  pct: number;
}

interface MonthlyChargeData {
  monthly_charge_ranges: MonthlyChargeRange[];
}

interface SummaryData {
  highest_count_range: MonthlyChargeRange;
  lowest_count_range: MonthlyChargeRange;
  most_common_charge_range: MonthlyChargeRange;
  total_churned_analyzed: number;
}

const MonthlyChargesPanel: React.FC = () => {
  const [chargeData, setChargeData] = useState<MonthlyChargeRange[]>([]);
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

        // Fetch both APIs simultaneously
        const [chargeResponse, summaryResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/monthly/bins`),
          fetch(`${API_BASE_URL}/api/monthly/bins/summary`)
        ]);

        if (!chargeResponse.ok) {
          throw new Error(`Monthly bins API error! status: ${chargeResponse.status}`);
        }
        if (!summaryResponse.ok) {
          throw new Error(`Summary API error! status: ${summaryResponse.status}`);
        }

        const chargeResult: MonthlyChargeData = await chargeResponse.json();
        const summaryResult: SummaryData = await summaryResponse.json();

        setChargeData(chargeResult.monthly_charge_ranges || []);
        setSummaryData(summaryResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error('Failed to fetch monthly charges data:', err);
        setChargeData([]);
        setSummaryData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Chart data configuration
  const chartData = {
    labels: chargeData.map(item => `$${item.range}`),
    datasets: [
      {
        label: 'Churn Rate (%)',
        data: chargeData.map(item => (item.pct * 100).toFixed(2)),
        borderColor: 'rgba(99, 102, 241, 1)',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(99, 102, 241, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const dataIndex = context.dataIndex;
            const item = chargeData[dataIndex];
            return [
              `Churn Rate: ${context.parsed.y}%`,
              `Users: ${item?.count?.toLocaleString() || 0}`,
              `Range: $${item?.range || 'N/A'}`
            ];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function (value: any) {
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
          text: 'Monthly Charge Range'
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

    if (error || !chargeData || chargeData.length === 0) {
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
              {error ? 'Failed to load monthly charges data' : 'No monthly charge data available'}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="h-96">
        <Line data={chartData} options={chartOptions} />
      </div>
    );
  };

  const renderSummaryContent = () => {
    if (loading) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, index) => (
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm font-medium text-red-700 mb-1">Highest Churn Count</div>
          <div className="text-xl font-bold text-red-900 mb-1">
            ${summaryData.highest_count_range.range}
          </div>
          <div className="text-sm text-red-600">
            {summaryData.highest_count_range.count.toLocaleString()} users ({(summaryData.highest_count_range.pct * 100).toFixed(1)}%)
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm font-medium text-green-700 mb-1">Lowest Churn Count</div>
          <div className="text-xl font-bold text-green-900 mb-1">
            ${summaryData.lowest_count_range.range}
          </div>
          <div className="text-sm text-green-600">
            {summaryData.lowest_count_range.count.toLocaleString()} users ({(summaryData.lowest_count_range.pct * 100).toFixed(1)}%)
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm font-medium text-blue-700 mb-1">Most Common Range</div>
          <div className="text-xl font-bold text-blue-900 mb-1">
            ${summaryData.most_common_charge_range.range}
          </div>
          <div className="text-sm text-blue-600">
            {summaryData.most_common_charge_range.count.toLocaleString()} users ({(summaryData.most_common_charge_range.pct * 100).toFixed(1)}%)
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-700 mb-1">Total Analyzed</div>
          <div className="text-xl font-bold text-gray-900 mb-1">
            {summaryData.total_churned_analyzed.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">
            churned users
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
          <h1 className="text-3xl font-bold text-gray-900">Churn Rate by Monthly Charges</h1>
        </div>

        {/* Chart Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Monthly Charge Range Analysis
          </h3>
          <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
        </div>

        {/* Summary Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h3>
          {renderSummaryContent()}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      {/* Title - ALWAYS visible */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Churn Rate by Monthly Charges</h1>
      </div>

      {/* Chart Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Monthly Charge Range Analysis
        </h3>
        {renderChartContent()}
      </div>

      {/* Summary Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h3>
        {renderSummaryContent()}
      </div>
    </div>
  );
};

export default MonthlyChargesPanel;