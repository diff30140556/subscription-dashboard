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
import Toast from '@/components/Toast';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface FeatureWeight {
  feature: string;
  weight: number;
}

interface TrainingInfo {
  total_samples: number;
  total_features: number;
  train_samples: number;
  test_samples: number;
  positive_rate: number;
}

interface ModelData {
  auc: number;
  top_features: FeatureWeight[];
}

interface BaselineModelResponse {
  status: string;
  message: string;
  model: ModelData;
  training_info: TrainingInfo;
}

const ModelInsightsPanel: React.FC = () => {
  const [modelData, setModelData] = useState<BaselineModelResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRetraining, setIsRetraining] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error';
    isVisible: boolean;
  }>({
    message: '',
    type: 'success',
    isVisible: false,
  });

  useEffect(() => {
    fetchModelData();
  }, []);

  const fetchModelData = async () => {
    try {
      setLoading(true);
      setError(null);

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/model/baseline`);

      if (!response.ok) {
        throw new Error(`Model API error! status: ${response.status}`);
      }

      const result: BaselineModelResponse = await response.json();
      setModelData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch model data');
      console.error('Failed to fetch model data:', err);
      setModelData(null);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({
      message,
      type,
      isVisible: true,
    });
  };

  const hideToast = () => {
    setToast(prev => ({
      ...prev,
      isVisible: false,
    }));
  };

  const handleRetrainModel = async () => {
    try {
      setIsRetraining(true);
      setShowModal(false);

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/model/baseline/retrain`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Retrain API error! status: ${response.status}`);
      }

      // Show success toast
      showToast('Model retrained successfully!', 'success');
      
      // Refresh model data after successful retrain
      await fetchModelData();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to retrain model';
      showToast(errorMsg, 'error');
      console.error('Failed to retrain model:', err);
    } finally {
      setIsRetraining(false);
    }
  };

  // Prepare chart data
  const prepareChartData = () => {
    if (!modelData?.model?.top_features) return null;

    const features = modelData.model.top_features;
    const labels = features.map(f => f.feature);
    const weights = features.map(f => f.weight);

    // Color bars based on positive/negative weights
    const backgroundColors = weights.map(weight =>
      weight > 0 ? 'rgba(239, 68, 68, 0.8)' : 'rgba(34, 197, 94, 0.8)'
    );
    const borderColors = weights.map(weight =>
      weight > 0 ? 'rgba(239, 68, 68, 1)' : 'rgba(34, 197, 94, 1)'
    );

    return {
      labels,
      datasets: [
        {
          label: 'Feature Weight',
          data: weights,
          backgroundColor: backgroundColors,
          borderColor: borderColors,
          borderWidth: 2,
        },
      ],
    };
  };

  const chartData = prepareChartData();

  const chartOptions = {
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index' as const,
        axis: 'y' as const,
        intersect: false,
        callbacks: {
          label: function (ctx: any) {
            const label = ctx.dataset.label || '';
            const value = ctx.raw;
            return `${label}: ${value >= 0 ? '+' : ''}${value.toFixed(4)}`;
          }
        }
      }
    },
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Contribution Weight'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Feature'
        }
      }
    },
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Unknown';
    }
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div className="text-lg font-medium text-gray-600 mb-1">No Model Data</div>
            <div className="text-sm text-gray-500">
              {error ? 'Failed to load model insights' : 'No model data available'}
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

  const renderTrainingSummary = () => {
    if (loading) {
      return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, index) => (
            <div key={index} className="bg-gray-200 rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-300 rounded mb-2"></div>
              <div className="h-6 bg-gray-300 rounded"></div>
            </div>
          ))}
        </div>
      );
    }

    if (!modelData) {
      return (
        <div className="text-center text-gray-500 py-8">
          No training summary available
        </div>
      );
    }

    const lastTrained = modelData.message.match(/trained: ([^)]+)/)?.[1] || 'Unknown';

    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <div className="text-sm font-medium text-blue-700 mb-1">✅ AUC</div>
          <div className="text-2xl font-bold text-blue-900">
            {modelData.model.auc.toFixed(4)}
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
          <div className="text-sm font-medium text-gray-700 mb-1">✅ Total Samples</div>
          <div className="text-2xl font-bold text-gray-900">
            {modelData.training_info.total_samples.toLocaleString()}
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div className="text-sm font-medium text-green-700 mb-1">✅ Train/Test Split</div>
          <div className="text-lg font-bold text-green-900">
            {modelData.training_info.train_samples.toLocaleString()} / {modelData.training_info.test_samples.toLocaleString()}
          </div>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
          <div className="text-sm font-medium text-purple-700 mb-1">✅ Total Features</div>
          <div className="text-2xl font-bold text-purple-900">
            {modelData.training_info.total_features}
          </div>
        </div>

        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
          <div className="text-sm font-medium text-orange-700 mb-1">✅ Positive Rate</div>
          <div className="text-2xl font-bold text-orange-900">
            {(modelData.training_info.positive_rate * 100).toFixed(2)}%
          </div>
        </div>
      </div>
    );
  };

  const renderModal = () => {
    if (!showModal) return null;

    return (
      <div className="fixed inset-0 bg-black/60 bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md mx-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Are you sure you want to retrain the model?
          </h3>
          <p className="text-sm text-gray-600 mb-6">
            This may take several seconds and will overwrite the current model.
          </p>
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setShowModal(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleRetrainModel}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 cursor-pointer"
            >
              Confirm Retrain
            </button>
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
          <h1 className="text-3xl font-bold text-gray-900">Model Insights</h1>
        </div>

        {/* Chart Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Feature Weights
          </h3>
          <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
        </div>

        {/* Training Summary */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Training Summary</h3>
          {renderTrainingSummary()}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      {/* Title - ALWAYS visible */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Model Insights</h1>
      </div>

      {/* Chart Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Feature Weights
        </h3>
        {renderChartContent()}
      </div>

      {/* Training Summary */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Training Summary</h3>
        {renderTrainingSummary()}
      </div>

      {/* Retrain Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Model Management</h3>
            <p className="text-sm text-gray-600">
              Retrain the model with the latest data to improve predictions.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            disabled={isRetraining}
            className={`px-6 py-3 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 ${isRetraining
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-red-500 hover:bg-red-600 cursor-pointer'
              }`}
          >
            {isRetraining ? 'Retraining...' : 'Retrain Model'}
          </button>
        </div>

      </div>

      {/* Modal */}
      {renderModal()}

      {/* Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
        autoHideDuration={3000}
      />
    </div>
  );
};

export default ModelInsightsPanel;