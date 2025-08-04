'use client';

import React, { useEffect, useState } from 'react';
import { useDashboardStore } from '@/store/dashboardStore';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ContractChart from '@/components/ContractChart';

interface ContractData {
  contract_type: string;
  churn_rate: number;
  total_customers: number;
}

const ContractPanel: React.FC = () => {
  const { isLoading, setLoading } = useDashboardStore();
  const [data, setData] = useState<ContractData[]>([]);
  const loading = isLoading.contract;

  useEffect(() => {
    const fetchData = async () => {
      setLoading('contract', true);

      try {
        // Simulate API call - replace with your actual endpoint
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/churn/contract`);

        if (response.ok) {
          const result = await response.json();
          setData(result.data || []);
        } else {
          setData([]);
        }
      } catch (error) {
        console.error('Failed to fetch contract data:', error);
        setData([]);
      } finally {
        setTimeout(() => setLoading('contract', false), 800);
      }
    };

    fetchData();
  }, [setLoading]);

  if (loading) {
    return (
      <div className="space-y-6 opacity-0 animate-fade-in">
        {/* Title - ALWAYS visible */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Churn by Contract</h1>
        </div>

        <LoadingSkeleton title="Contract Data" rows={3} />
      </div>
    );
  }

  // Note: ContractChart handles its own data fetching and empty states
  // so we don't need an empty state check here for the summary cards

  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      {/* Title - ALWAYS visible */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Churn by Contract</h1>
      </div>

      {/* Summary Cards - only show if we have data */}
      {data && data.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {data.map((item) => (
              <div key={item.contract_type} className="text-center p-4 border rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.contract_type}</h3>
                <div className="text-3xl font-bold text-blue-600 mb-1">
                  {(item.churn_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500">
                  {item.total_customers.toLocaleString()} customers
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts - has its own loading logic */}
      <ContractChart />
    </div>
  );
};

export default ContractPanel;