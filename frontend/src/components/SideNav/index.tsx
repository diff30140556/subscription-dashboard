'use client';

import React from 'react';
import { useDashboardStore, type DashboardTab } from '@/store/dashboardStore';

interface NavItem {
  label: string;
  tab: DashboardTab;
  icon?: string;
}

const navItems: NavItem[] = [
  { label: 'KPI', tab: 'kpi' },
  { label: 'Churn by Contract', tab: 'contract' },
  { label: 'Churn by Payment Method', tab: 'payment' },
  { label: 'Tenure Bins', tab: 'tenure' },
  { label: 'Monthly Charges Bins', tab: 'monthly' },
  { label: 'Add-ons vs Churn', tab: 'features' },
  { label: 'Baseline Model Coefficients', tab: 'model' },
  { label: 'AI Insights', tab: 'ai-insights' },
  { label: 'Customer List', tab: 'customers' },
  { label: 'Generate Customers', tab: 'generate' },
];

const SideNav: React.FC = () => {
  const { activeTab, setActiveTab } = useDashboardStore();

  return (
    <nav className="w-64 bg-white border-r border-gray-200 h-full">
      <div className="p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-8">Apple Music Subscription</h1>
        
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = activeTab === item.tab;
            
            return (
              <li key={item.tab}>
                <button
                  onClick={() => setActiveTab(item.tab)}
                  className={`
                    w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer
                    ${isActive 
                      ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700 shadow-sm' 
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 hover:shadow-sm'
                    }
                  `}
                >
                  {item.label}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
};

export default SideNav;