'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '@/lib/api';
import { extractItems } from '@/lib/api-helpers';
import { KnowledgeEntry, KnowledgeStats } from '@/types';

export function useKnowledgeList(category?: string) {
  return useQuery({
    queryKey: ['knowledge', 'list', category],
    queryFn: async () => {
      const res = await knowledgeApi.getList({ category: category !== 'all' ? category : undefined });
      const items = extractItems<KnowledgeEntry>(res);
      if (items.length > 0 || res.success) return items;
      throw new Error(res.error || '获取知识列表失败');
    },
    staleTime: 60 * 1000,
  });
}

export function useKnowledgeStats() {
  return useQuery<KnowledgeStats>({
    queryKey: ['knowledge', 'stats'],
    queryFn: async () => {
      const res = await knowledgeApi.getList({});
      if (res.success) {
        const items = extractItems<KnowledgeEntry>(res);
        const byCategory: Record<string, number> = {};
        for (const item of items) {
          const cat = item.category || '未分类';
          byCategory[cat] = (byCategory[cat] || 0) + 1;
        }
        return {
          total_entries: items.length,
          by_category: byCategory,
          recent_updates: items.slice(0, 3),
        };
      }
      throw new Error(res.error || '获取知识统计失败');
    },
    staleTime: 60 * 1000,
  });
}

export function useCreateKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; content: string; category: string; tags?: string[] }) =>
      knowledgeApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useUpdateKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; content?: string; category?: string; tags?: string[] } }) =>
      knowledgeApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useDeleteKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => knowledgeApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useUploadKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => knowledgeApi.upload(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useSearchKnowledge(query: string) {
  return useQuery({
    queryKey: ['knowledge', 'search', query],
    queryFn: async () => {
      const res = await knowledgeApi.search(query);
      if (res.success && res.data) {
        const data = res.data as { entries?: KnowledgeEntry[]; items?: KnowledgeEntry[] } | KnowledgeEntry[];
        if (Array.isArray(data)) return data;
        return (data.entries || data.items || []) as KnowledgeEntry[];
      }
      throw new Error(res.error || '搜索失败');
    },
    enabled: query.length > 0,
    staleTime: 30 * 1000,
  });
}

export interface VectorStats {
  total: number;
  synced: number;
  pending: number;
  failed: number;
}

export function useVectorStats() {
  return useQuery<VectorStats>({
    queryKey: ['knowledge', 'vector-stats'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/vector-stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'X-Enterprise-Id': localStorage.getItem('enterprise_id') || '',
        },
      });
      if (!res.ok) throw new Error('获取向量统计失败');
      return res.json();
    },
    staleTime: 30 * 1000,
  });
}

export function useResyncKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => knowledgeApi.resync(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}
