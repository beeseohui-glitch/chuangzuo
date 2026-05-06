'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi, enterpriseApi } from '@/lib/api';
import { Enterprise, PlanType } from '@/types';

function isDevMode(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('dev_mode') !== 'false';
}

const MOCK_ENTERPRISE: Enterprise = {
  id: 'dev-enterprise-001',
  name: '智创科技',
  plan: 'free' as PlanType,
  quota_monthly: 5,
  quota_used: 2,
  status: 'active',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const MOCK_QUOTA = {
  monthly_limit: 5,
  used: 2,
  reset_date: '2026-06-01',
};

export function useUserProfile() {
  return useQuery({
    queryKey: ['user', 'profile'],
    queryFn: async () => {
      const res = await userApi.getProfile();
      if (res.success && res.data) return res.data;
      if (isDevMode()) return null;
      throw new Error(res.error || '获取用户信息失败');
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useEnterpriseInfo() {
  return useQuery({
    queryKey: ['enterprise', 'info'],
    queryFn: async () => {
      const res = await enterpriseApi.getInfo();
      if (res.success && res.data) return res.data as Enterprise;
      if (isDevMode()) return MOCK_ENTERPRISE;
      throw new Error(res.error || '获取企业信息失败');
    },
    staleTime: 5 * 60 * 1000,
  });
}

export interface EnterpriseQuota {
  monthly_limit: number;
  used: number;
  reset_date: string;
}

export function useEnterpriseQuota() {
  return useQuery<EnterpriseQuota>({
    queryKey: ['enterprise', 'quota'],
    queryFn: async () => {
      const res = await enterpriseApi.getQuota();
      if (res.success && res.data) return res.data as EnterpriseQuota;
      if (isDevMode()) return MOCK_QUOTA;
      throw new Error(res.error || '获取额度信息失败');
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name?: string; avatar_url?: string }) => userApi.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });
}
