# Components Structure

This directory contains reusable React components for the single-page churn analysis dashboard.

## Directory Structure

```
components/
├── KpiCard/              # Individual KPI card component with Chart.js sparklines
│   └── index.tsx
├── KpiDashboard/         # KPI dashboard layout with 4 metric cards  
│   └── index.tsx
├── SideNav/              # Sidebar navigation with tab switching
│   └── index.tsx
├── LoadingSkeleton/      # Loading skeleton component with pulse animation
│   └── index.tsx
├── panels/               # Dashboard panel components
│   ├── KpiPanel/         # KPI overview panel
│   ├── ContractPanel/    # Churn by Contract analysis
│   ├── PaymentPanel/     # Churn by Payment Method analysis
│   ├── TenurePanel/      # Tenure distribution analysis
│   ├── MonthlyPanel/     # Monthly charges analysis
│   ├── FeaturesPanel/    # Add-ons vs Churn analysis
│   ├── ModelPanel/       # Model coefficients analysis
│   └── CustomersPanel/   # Customer list panel
├── index.ts              # Main export file
└── README.md             # This file
```

## Current Components

### Core Components

**KpiCard** - Individual metric card with sparklines, trend indicators, and loading states

**KpiDashboard** - Grid layout with 4 KPI cards, real-time API data fetching

**SideNav** - Sidebar navigation using Zustand state management for tab switching

**LoadingSkeleton** - Animated loading placeholders with configurable rows and chart areas

### Dashboard Panels

All panels use the single-page app pattern with Zustand for state management:

**KpiPanel** - Uses existing KpiDashboard component  
**ContractPanel** - Mock API integration with churn by contract type analysis  
**PaymentPanel** - Mock API integration with churn by payment method analysis  
**TenurePanel** - Placeholder for tenure distribution charts  
**MonthlyPanel** - Placeholder for monthly charges analysis  
**FeaturesPanel** - Placeholder for add-ons correlation analysis  
**ModelPanel** - Placeholder for model coefficients visualization  
**CustomersPanel** - Placeholder for customer data table

## Usage Patterns

### Individual Component Import
```tsx
import KpiCard from '../components/KpiCard';
import KpiDashboard from '../components/KpiDashboard';
```

### Bulk Import from Index
```tsx
import { KpiCard, KpiDashboard } from '../components';
```

## Adding New Components

1. Create a new folder: `components/NewComponent/`
2. Add your component: `components/NewComponent/index.tsx`
3. Export from main index: `components/index.ts`

Example:
```tsx
// components/ChurnByContract/index.tsx
'use client';

import React from 'react';

interface ChurnByContractProps {
  data: Array<{key: string, churn_rate: number, n: number}>;
}

const ChurnByContract: React.FC<ChurnByContractProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4">Churn by Contract Type</h2>
      {/* Chart implementation */}
    </div>
  );
};

export default ChurnByContract;
```

## Best Practices

1. Each component gets its own folder with `index.tsx`
2. Use TypeScript interfaces for props
3. Include `'use client'` for client-side components
4. Follow naming convention: PascalCase for components
5. Export from main `components/index.ts` for clean imports