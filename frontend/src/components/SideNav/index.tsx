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

interface SideNavProps {
  onClose?: () => void;
}

const SideNav: React.FC<SideNavProps> = ({ onClose }) => {
  const { activeTab, setActiveTab } = useDashboardStore();

  const handleTabClick = (tab: DashboardTab) => {
    setActiveTab(tab);
    if (onClose) {
      onClose();
    }
  };

  return (
    <nav className="w-64 bg-white border-r border-gray-200 h-full shadow-lg md:shadow-none">
      <div className="p-6">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-xl font-bold text-gray-900">Apple Music Subscription</h1>
          {/* Close button for mobile */}
          {onClose && (
            <button
              onClick={onClose}
              className="md:hidden flex items-center justify-center w-8 h-8 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Close menu"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = activeTab === item.tab;
            
            return (
              <li key={item.tab}>
                <button
                  onClick={() => handleTabClick(item.tab)}
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