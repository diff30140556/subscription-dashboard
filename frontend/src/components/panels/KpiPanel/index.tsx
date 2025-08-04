'use client';

import React from 'react';
import { KpiDashboard } from '@/components';

const KpiPanel: React.FC = () => {
  return (
    <div className="space-y-6 opacity-0 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">KPI Overview</h1>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm">
        <KpiDashboard />
      </div>
    </div>
  );
};

export default KpiPanel;