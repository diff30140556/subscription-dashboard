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
import LoadingSkeleton from '@/components/LoadingSkeleton';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface PaymentDataItem {
  key: string;
  churn_rate: number;
  n: number;
}

interface PaymentApiResponse {
  churn_rate_by_payment: PaymentDataItem[];
}

const PaymentChart: React.FC = () => {
  const [data, setData] = useState<PaymentDataItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/churn/payment`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result: PaymentApiResponse = await response.json();
        setData(result.churn_rate_by_payment || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error('Failed to fetch payment data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const chartData = {
    labels: data.map(item => item.key),
    datasets: [
      {
        label: 'Churn Rate (%)',
        data: data.map(item => (item.churn_rate * 100).toFixed(2)),
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',   // Red
          'rgba(59, 130, 246, 0.8)',  // Blue
          'rgba(16, 185, 129, 0.8)',  // Green
          'rgba(245, 158, 11, 0.8)',  // Amber
          'rgba(139, 92, 246, 0.8)',  // Purple
        ],
        borderColor: [
          'rgba(239, 68, 68, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(139, 92, 246, 1)',
        ],
        borderWidth: 1,
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
            const item = data[dataIndex];
            return [
              `Churn Rate: ${context.parsed.y}%`,
              `Users: ${item?.n?.toLocaleString() || 0}`
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
          text: 'Payment Method'
        }
      }
    },
  };

  const renderContent = () => {
    if (error || !data || data.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Churn Rate by Payment Method
          </h3>
          <div className="h-80 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-gray-400 mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="text-lg font-medium text-gray-600 mb-1">No Data Found</div>
              <div className="text-sm text-gray-500">
                {error ? 'Failed to load payment data' : 'No payment method data available'}
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Churn Rate by Payment Method
          </h3>
          <div className="h-80 bg-gray-200 rounded animate-pulse"></div>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Churn Rate by Payment Method
        </h3>
        <div className="h-80">
          <Bar data={chartData} options={chartOptions} />
        </div>
      </div>
    );
  };

  return (
    <div className="w-full">
      {renderContent()}
    </div>
  );
};

export default PaymentChart;