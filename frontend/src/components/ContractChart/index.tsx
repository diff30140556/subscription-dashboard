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
  ArcElement,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface ContractDataItem {
  key: string;
  churn_rate: number;
  n: number;
}

interface ContractApiResponse {
  churn_rate_by_contract: ContractDataItem[];
}

const ContractChart: React.FC = () => {
  const [data, setData] = useState<ContractDataItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/churn/contract`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result: ContractApiResponse = await response.json();
        setData(result.churn_rate_by_contract || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error('Failed to fetch contract data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const barChartData = {
    labels: data.map(item => item.key),
    datasets: [
      {
        label: 'Churn Rate (%)',
        data: data.map(item => (item.churn_rate * 100).toFixed(2)),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',  // Blue
          'rgba(16, 185, 129, 0.8)',  // Green
          'rgba(245, 158, 11, 0.8)',  // Amber
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const pieChartData = {
    labels: data.map(item => item.key),
    datasets: [
      {
        label: 'User Count',
        data: data.map(item => item.n),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            return `${context.parsed.y}%`;
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
          text: 'Contract Type'
        }
      }
    },
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value.toLocaleString()} users (${percentage}%)`;
          }
        }
      }
    },
  };

  const renderChartContent = (title: string, isBarChart: boolean) => {
    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <div className="text-red-600 font-medium mb-2">Error Loading Chart Data</div>
          <div className="text-red-500 text-sm">{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-md text-sm transition-colors cursor-pointer"
          >
            Retry
          </button>
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
          <Bar data={barChartData} options={barOptions} />
        ) : (
          <Pie data={pieChartData} options={pieOptions} />
        )}
      </div>
    );
  };

  return (
    <div className="w-full space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Churn Rate by Contract Type
          </h3>
          {renderChartContent("Churn Rate by Contract Type", true)}
        </div>

        {/* Pie Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            User Distribution by Contract Type
          </h3>
          {renderChartContent("User Distribution by Contract Type", false)}
        </div>
      </div>
    </div>
  );
};

export default ContractChart;