'use client';

import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface KpiCardProps {
  title: string;
  value: number | string;
  unit?: string;
  prefix?: string;
  trend?: 'up' | 'down' | 'neutral';
  sparklineData?: number[];
  formatter?: (val: number | string) => string;
}

const KpiCard: React.FC<KpiCardProps> = ({ 
  title, 
  value, 
  unit = '', 
  prefix = '', 
  trend = 'neutral', 
  sparklineData = [], 
  formatter = (val) => String(val)
}) => {
  // Chart.js sparkline configuration
  const chartData = {
    labels: sparklineData.map((_, index) => `Point ${index + 1}`),
    datasets: [
      {
        data: sparklineData,
        borderColor: trend === 'up' ? '#10b981' : trend === 'down' ? '#ef4444' : '#6b7280',
        backgroundColor: trend === 'up' ? '#10b98120' : trend === 'down' ? '#ef444420' : '#6b728020',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 0,
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
        enabled: false,
      },
    },
    scales: {
      x: {
        display: false,
      },
      y: {
        display: false,
      },
    },
    elements: {
      point: {
        radius: 0,
      },
    },
    interaction: {
      intersect: false,
    },
  };

  // Trend indicator
  const getTrendIcon = () => {
    if (trend === 'up') {
      return (
        <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7m0 0H7" />
        </svg>
      );
    }
    if (trend === 'down') {
      return (
        <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10m0 0h10" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
      </svg>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow duration-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
          {title}
        </h3>
        {getTrendIcon()}
      </div>

      {/* Main Value */}
      <div className="flex items-baseline space-x-1 mb-4">
        <span className="text-3xl font-bold text-gray-900">
          {prefix}{formatter(value)}{unit}
        </span>
      </div>

      {/* Sparkline Chart */}
      {sparklineData.length > 0 && (
        <div className="h-12 w-full">
          <Line data={chartData} options={chartOptions} />
        </div>
      )}
    </div>
  );
};

export default KpiCard;