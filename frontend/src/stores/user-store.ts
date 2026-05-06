import { create } from 'zustand';
import { Enterprise, PlanType } from '@/types';

interface UsageQuota {
  monthly_limit: number;
  used: number;
  reset_date: string;
}

interface UserStore {
  enterprise: Enterprise | null;
  quota: UsageQuota;
  version: string;

  setEnterprise: (enterprise: Enterprise) => void;
  setQuota: (quota: UsageQuota) => void;
  updateQuotaUsed: (used: number) => void;
  getVersion: () => string;
  getPlanLabel: (plan: PlanType) => string;
}

export const useUserStore = create<UserStore>((set, get) => ({
  enterprise: null,
  quota: {
    monthly_limit: 5,
    used: 0,
    reset_date: '',
  },
  version: 'v1.0.0',

  setEnterprise: (enterprise) => set({ enterprise }),

  setQuota: (quota) => set({ quota }),

  updateQuotaUsed: (used) =>
    set((state) => ({
      quota: { ...state.quota, used },
    })),

  getVersion: () => get().version,

  getPlanLabel: (plan) => {
    const labels: Record<PlanType, string> = {
      free: '免费版',
      basic: '基础版',
      professional: '专业版',
      enterprise: '企业版',
    };
    return labels[plan] || plan;
  },
}));
