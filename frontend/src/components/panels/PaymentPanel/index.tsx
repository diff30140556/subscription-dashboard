'use client';

import React from 'react';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import PaymentChart from '@/components/PaymentChart';
import PaymentComparison from '@/components/PaymentComparison';
import { useDashboardStore } from '@/store/dashboardStore';

const PaymentPanel: React.FC = () => {
  const { isLoading } = useDashboardStore();
  const loading = isLoading.payment;

  if (loading) {
    return (
      <div className="space-y-6 opacity-0 animate-fade-in">
        {/* Title - ALWAYS visible */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Churn by Payment Method</h1>
        </div>
        
        <LoadingSkeleton title="Payment Data" rows={4} />
      </div>
    );
  }

  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      {/* Title - ALWAYS visible */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Churn by Payment Method</h1>
      </div>

      {/* Payment Chart Component */}
      <PaymentChart />

      {/* Payment Comparison Component */}
      <PaymentComparison />
    </div>
  );
};

export default PaymentPanel;