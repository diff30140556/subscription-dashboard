import { create } from 'zustand';

export type DashboardTab = 
  | 'kpi'
  | 'contract'
  | 'payment'
  | 'tenure'
  | 'monthly'
  | 'features'
  | 'model'
  | 'customers'
  | 'generate'
  | 'ai-insights';

interface DashboardState {
  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;
  isLoading: Record<DashboardTab, boolean>;
  setLoading: (tab: DashboardTab, loading: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  activeTab: 'kpi',
  setActiveTab: (tab) => set({ activeTab: tab }),
  isLoading: {
    kpi: false,
    contract: false,
    payment: false,
    tenure: false,
    monthly: false,
    features: false,
    model: false,
    customers: false,
    generate: false,
    'ai-insights': false,
  },
  setLoading: (tab, loading) =>
    set((state) => ({
      isLoading: {
        ...state.isLoading,
        [tab]: loading,
      },
    })),
}));