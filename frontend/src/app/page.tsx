'use client';

import React, { useState } from 'react';
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
      {/* Mobile backdrop overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        flex-shrink-0 fixed md:relative h-full z-50 transition-transform duration-300 ease-in-out
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <SideNav onClose={() => setIsMobileMenuOpen(false)} />
      </aside>

      {/* Main content area */}
      <main className="flex-1 overflow-auto md:ml-0">
        {/* Mobile hamburger menu */}
        <div className="md:hidden bg-white border-b border-gray-200 p-4">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="flex items-center justify-center w-10 h-10 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Open menu"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        <div className="p-4 md:p-8">
          {renderActivePanel()}
        </div>
      </main>
    </div>
  );
}