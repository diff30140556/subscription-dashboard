'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Toast from '@/components/Toast';

// Data structure interfaces
interface ChurnByItem {
  key: string;
  churn_rate: number;
  n: number;
}

interface FeatureChurnData {
  [feature: string]: ChurnByItem[];
}

interface DistributionItem {
  range: string;
  count: number;
  pct: number;
}

interface InsightsData {
  overall_churn_rate: number;
  total_customers: number;
  churned_customers: number;
  average_tenure: number;
  average_monthly_charges: number;
  churn_by_contract: ChurnByItem[];
  churn_by_payment: ChurnByItem[];
  churn_by_features: FeatureChurnData;
  tenure_distribution: DistributionItem[];
  monthly_charges_distribution: DistributionItem[];
}

interface AIResponse {
  insights: string;
  recommendations: string[];
  key_findings: string[];
}

const AIInsightsPanel: React.FC = () => {
  const [insightsData, setInsightsData] = useState<InsightsData | null>(null);
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error';
    isVisible: boolean;
  }>({
    message: '',
    type: 'success',
    isVisible: false,
  });

  // Toast helper functions
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

  // Fetch all required data from existing APIs
  const fetchAllData = useCallback(async () => {
    setLoadingData(true);
    setError(null);

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Fetch all required data in parallel
      const [
        kpiResponse,
        contractResponse,
        paymentResponse,
        featuresResponse,
        tenureResponse,
        monthlyResponse
      ] = await Promise.all([
        fetch(`${API_BASE_URL}/api/churn/kpis`),
        fetch(`${API_BASE_URL}/api/churn/contract`),
        fetch(`${API_BASE_URL}/api/churn/payment`),
        fetch(`${API_BASE_URL}/api/features/churn`),
        fetch(`${API_BASE_URL}/api/tenure/bins`),
        fetch(`${API_BASE_URL}/api/monthly/bins`)
      ]);

      // Check if all requests were successful
      if (!kpiResponse.ok || !contractResponse.ok || !paymentResponse.ok || 
          !featuresResponse.ok || !tenureResponse.ok || !monthlyResponse.ok) {
        throw new Error('Failed to fetch one or more data sources');
      }

      // Parse all responses
      const kpiData = await kpiResponse.json();
      const contractData = await contractResponse.json();
      const paymentData = await paymentResponse.json();
      const featuresData = await featuresResponse.json();
      const tenureData = await tenureResponse.json();
      const monthlyData = await monthlyResponse.json();


      // Safely aggregate data into the required format
      const churnRate = kpiData?.kpis?.churn_rate_overall || 0;
      const churnedUsers = kpiData?.kpis?.churned_users || 0;
      const totalCustomers = churnRate > 0 ? Math.round(churnedUsers / churnRate) : 0;

      const aggregatedData: InsightsData = {
        overall_churn_rate: churnRate,
        total_customers: totalCustomers,
        churned_customers: churnedUsers,
        average_tenure: kpiData?.kpis?.avg_tenure || 0,
        average_monthly_charges: kpiData?.kpis?.avg_monthly || 0,
        churn_by_contract: contractData?.churn_rate_by_contract || [],
        churn_by_payment: paymentData?.churn_rate_by_payment || [],
        churn_by_features: featuresData?.churn_rate_by_feature || {},
        tenure_distribution: tenureData?.tenure_ranges || [],
        monthly_charges_distribution: monthlyData?.monthly_charge_ranges || []
      };


      setInsightsData(aggregatedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      console.error('Error fetching insights data:', err);
    } finally {
      setLoadingData(false);
    }
  }, []);

  // Send insights request to AI
  const generateInsights = useCallback(async () => {
    if (!insightsData) {
      showToast('No data available to generate insights', 'error');
      return;
    }

    setLoadingInsights(true);
    setAiResponse(null);

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      
      const response = await fetch(`${API_BASE_URL}/api/insights`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(insightsData),
      });

      if (!response.ok) {
        // Try to get more details about the error
        let errorDetails = `API error! status: ${response.status}`;
        try {
          const errorBody = await response.text();
          console.error('API Error Response:', errorBody);
          errorDetails += ` - ${errorBody}`;
        } catch {
          // If we can't read the error body, just use the status
        }
        throw new Error(errorDetails);
      }

      const aiData: AIResponse = await response.json();
      setAiResponse(aiData);
      showToast('AI insights generated successfully!', 'success');

      // Scroll to insights section
      setTimeout(() => {
        const insightsSection = document.getElementById('ai-insights-section');
        if (insightsSection) {
          insightsSection.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to generate insights';
      showToast(errorMsg, 'error');
      console.error('Error generating insights:', err);
    } finally {
      setLoadingInsights(false);
    }
  }, [insightsData]);

  // Load data on component mount
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  const renderDataSummary = () => {
    if (loadingData) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-4"></div>
              <div className="h-8 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      );
    }

    if (error || !insightsData) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="text-red-800 font-medium">
            {error || 'Failed to load data for insights'}
          </div>
          <button
            onClick={fetchAllData}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Overall Churn Rate</div>
            <div className="text-3xl font-bold text-red-600">
              {(insightsData.overall_churn_rate * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">
              {insightsData.churned_customers.toLocaleString()} of {Math.round(insightsData.total_customers).toLocaleString()} customers
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Total Customers</div>
            <div className="text-3xl font-bold text-blue-600">
              {Math.round(insightsData.total_customers).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">
              Active customer base
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Average Tenure</div>
            <div className="text-3xl font-bold text-green-600">
              {insightsData.average_tenure.toFixed(1)}
            </div>
            <div className="text-sm text-gray-500">months</div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Avg Monthly Charges</div>
            <div className="text-3xl font-bold text-purple-600">
              ${insightsData.average_monthly_charges.toFixed(2)}
            </div>
            <div className="text-sm text-gray-500">per customer</div>
          </div>
        </div>

        {/* Contract & Payment Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Churn by Contract Type</h3>
            <div className="space-y-3">
              {insightsData.churn_by_contract.map((item, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">{item.key}</span>
                  <div className="text-right">
                    <div className="text-sm font-bold text-gray-900">
                      {(item.churn_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.n.toLocaleString()} customers
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Churn by Payment Method</h3>
            <div className="space-y-3">
              {insightsData.churn_by_payment.map((item, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">{item.key}</span>
                  <div className="text-right">
                    <div className="text-sm font-bold text-gray-900">
                      {(item.churn_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.n.toLocaleString()} customers
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Feature Analysis */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Churn by Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(insightsData.churn_by_features).map(([feature, data]) => (
              <div key={feature}>
                <h4 className="text-md font-medium text-gray-800 mb-2">{feature}</h4>
                <div className="space-y-2">
                  {data.map((item, index) => (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <span className="text-gray-600">{item.key}</span>
                      <div className="text-right">
                        <span className="font-semibold text-gray-900">
                          {(item.churn_rate * 100).toFixed(1)}%
                        </span>
                        <span className="text-gray-500 ml-2">
                          ({item.n.toLocaleString()})
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderAIInsights = () => {
    if (!aiResponse) return null;

    return (
      <div id="ai-insights-section" className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">AI Insights</h2>
          <div className="text-sm text-gray-500">
            Generated {new Date().toLocaleString()}
          </div>
        </div>

        {/* Main Insights */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Summary</h3>
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-700 leading-relaxed whitespace-pre-line">
              {aiResponse.insights}
            </p>
          </div>
        </div>

        {/* Key Findings */}
        {aiResponse.key_findings && aiResponse.key_findings.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">🔍 Key Findings</h3>
            <ul className="space-y-2">
              {aiResponse.key_findings.map((finding, index) => (
                <li key={index} className="flex items-start">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                  <span className="text-blue-800">{finding}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {aiResponse.recommendations && aiResponse.recommendations.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-900 mb-4">💡 Recommendations</h3>
            <ul className="space-y-2">
              {aiResponse.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                  <span className="text-green-800">{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">AI Insights</h1>
        <div className="text-sm text-gray-500">
          Comprehensive churn analysis powered by AI
        </div>
      </div>

      {/* Data Summary Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Data Summary</h2>
          <button
            onClick={fetchAllData}
            disabled={loadingData}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 disabled:opacity-50 cursor-pointer"
          >
            Refresh Data
          </button>
        </div>

        {renderDataSummary()}

        {/* Generate Insights Button */}
        {insightsData && (
          <div className="flex justify-center pt-6">
            <button
              onClick={generateInsights}
              disabled={loadingInsights}
              className={`px-8 py-4 text-lg font-medium text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                loadingInsights
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
              }`}
            >
              {loadingInsights ? (
                <div className="flex items-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                  Generating AI Insights...
                </div>
              ) : (
                'Generate AI Insights'
              )}
            </button>
          </div>
        )}
      </div>

      {/* AI Insights Section */}
      {loadingInsights && (
        <div className="bg-white rounded-lg shadow-sm p-8">
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <div className="text-lg font-medium text-gray-700">Analyzing your data...</div>
              <div className="text-sm text-gray-500 mt-1">This may take a few moments</div>
            </div>
          </div>
        </div>
      )}

      {renderAIInsights()}

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

export default AIInsightsPanel;