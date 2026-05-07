'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi, enterpriseApi } from '@/lib/api';
import { Enterprise, PlanType, EnterpriseQuota } from '@/types';

export function useUserProfile() {
  return useQuery({
    queryKey: ['user', 'profile'],
    queryFn: async () => {
      const res = await userApi.getProfile();
      if (res.success && res.data) return res.data;
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
      throw new Error(res.error || '获取企业信息失败');
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useEnterpriseQuota() {
  return useQuery<EnterpriseQuota>({
    queryKey: ['enterprise', 'quota'],
    queryFn: async () => {
      const res = await enterpriseApi.getQuota();
      if (res.success && res.data) return res.data as EnterpriseQuota;
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
