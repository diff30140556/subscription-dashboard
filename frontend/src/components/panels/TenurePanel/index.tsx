'use client';

import React, { useEffect } from 'react';
import { useDashboardStore } from '@/store/dashboardStore';
import LoadingSkeleton from '@/components/LoadingSkeleton';

const TenurePanel: React.FC = () => {
  const { isLoading, setLoading } = useDashboardStore();
  const loading = isLoading.tenure;

  useEffect(() => {
    setLoading('tenure', true);
    const timer = setTimeout(() => setLoading('tenure', false), 700);
    return () => clearTimeout(timer);
  }, [setLoading]);

  if (loading) {
    return <LoadingSkeleton title="Tenure Bins" rows={3} />;
  }

  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Tenure Bins</h1>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <div className="text-lg font-medium text-gray-600 mb-2">Tenure Distribution Analysis</div>
            <div className="text-sm text-gray-500">Histogram showing churn by tenure ranges</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenurePanel;