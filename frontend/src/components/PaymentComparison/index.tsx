'use client';

import React, { useEffect, useState } from 'react';
import LoadingSkeleton from '@/components/LoadingSkeleton';

interface PaymentMethodAnalysis {
  highest_rate: number;
  lowest_rate: number;
  rate_spread: number;
  method_count: number;
}

interface ContractAnalysis {
  highest_rate: number;
  lowest_rate: number;
  rate_spread: number;
  contract_count: number;
}

interface Comparison {
  higher_spread_segment: string;
  payment_vs_contract_spread_ratio: number;
}

interface ComparisonApiResponse {
  payment_method_analysis: PaymentMethodAnalysis;
  contract_analysis: ContractAnalysis;
  comparison: Comparison;
}

const PaymentComparison: React.FC = () => {
  const [data, setData] = useState<ComparisonApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/churn/payment/compare`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result: ComparisonApiResponse = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        console.error('Failed to fetch comparison data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const RangeBar: React.FC<{
    label: string;
    lowest: number;
    highest: number;
    spread: number;
    count: number;
    isHigher: boolean;
  }> = ({ label, lowest, highest, spread, count, isHigher }) => {
    const maxSpread = Math.max(
      data?.payment_method_analysis.rate_spread || 0,
      data?.contract_analysis.rate_spread || 0
    );
    const barWidth = (spread / maxSpread) * 100;

    return (
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <h4 className="text-lg font-semibold text-gray-900">{label}</h4>
            {isHigher && (
              <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
                Higher Risk Spread
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500">
            {count} {label.toLowerCase()}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Low: {formatPercentage(lowest)}</span>
            <span>High: {formatPercentage(highest)}</span>
          </div>

          <div className="relative h-8 bg-gray-200 rounded-lg overflow-hidden">
            <div
              className={`h-full rounded-lg ${isHigher ? 'bg-red-500' : 'bg-blue-500'}`}
              style={{ width: `${barWidth}%` }}
            />
            <div className="absolute inset-0 flex items-center justify-center text-white text-sm font-medium">
              Spread: {formatPercentage(spread)}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (error || !data) {
      return (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Payment vs Contract Risk Spread Comparison
            </h3>
          </div>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-gray-400 mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="text-lg font-medium text-gray-600 mb-1">No Data Found</div>
              <div className="text-sm text-gray-500">
                {error ? 'Failed to load comparison data' : 'No comparison data available'}
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Payment vs Contract Risk Spread Comparison
            </h3>
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
          </div>
          <div className="space-y-6">
            <div className="h-16 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-16 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-12 bg-gray-200 rounded animate-pulse"></div>
          </div>
        </div>
      );
    }

    const { payment_method_analysis, contract_analysis, comparison } = data;
    const isPaymentHigher = comparison.higher_spread_segment === 'payment';

    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Payment vs Contract Risk Spread Comparison
          </h3>
          <p className="text-gray-600 text-sm">
            Comparing the range of churn rates across payment methods and contract types to identify which segment shows more variability in customer retention risk.
          </p>
        </div>

        <div className="space-y-6">
          <RangeBar
            label="Payment Methods"
            lowest={payment_method_analysis.lowest_rate}
            highest={payment_method_analysis.highest_rate}
            spread={payment_method_analysis.rate_spread}
            count={payment_method_analysis.method_count}
            isHigher={isPaymentHigher}
          />

          <RangeBar
            label="Contract Types"
            lowest={contract_analysis.lowest_rate}
            highest={contract_analysis.highest_rate}
            spread={contract_analysis.rate_spread}
            count={contract_analysis.contract_count}
            isHigher={!isPaymentHigher}
          />

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h5 className="font-medium text-gray-900">Spread Ratio Analysis</h5>
                <p className="text-sm text-gray-600 mt-1">
                  Payment spread is {formatPercentage(comparison.payment_vs_contract_spread_ratio)} of contract spread
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">
                  {(comparison.payment_vs_contract_spread_ratio * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">Relative Ratio</div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              <span className="font-medium capitalize">{comparison.higher_spread_segment}</span> types
              show {isPaymentHigher ? 'higher' : 'lower'} variability in churn risk, suggesting
              {isPaymentHigher ? ' payment method' : ' contract length'} is a stronger differentiator for customer retention.
            </p>
          </div>
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

export default PaymentComparison;