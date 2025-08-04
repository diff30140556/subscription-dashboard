'use client';

import React from 'react';
import { useDashboardStore } from '@/store/dashboardStore';
import {
  SideNav,
  KpiPanel,
  ContractPanel,
  PaymentPanel,
  TenurePanel,
  MonthlyPanel,
  FeaturesPanel,
  ModelPanel,
  CustomersPanel,
  AIInsightsPanel,
  GenerateCustomersPanel,
} from '@/components';

export default function DashboardPage() {
  const { activeTab } = useDashboardStore();

  const renderActivePanel = () => {
    switch (activeTab) {
      case 'kpi':
        return <KpiPanel />;
      case 'contract':
        return <ContractPanel />;
      case 'payment':
        return <PaymentPanel />;
      case 'tenure':
        return <TenurePanel />;
      case 'monthly':
        return <MonthlyPanel />;
      case 'features':
        return <FeaturesPanel />;
      case 'model':
        return <ModelPanel />;
      case 'customers':
        return <CustomersPanel />;
      case 'ai-insights':
        return <AIInsightsPanel />;
      case 'generate':
        return <GenerateCustomersPanel />;
      default:
        return <KpiPanel />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="flex-shrink-0">
        <SideNav />
      </aside>

      {/* Main content area */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {renderActivePanel()}
        </div>
      </main>
    </div>
  );
}