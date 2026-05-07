'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '@/lib/api';
import { KnowledgeEntry } from '@/types';

// --- Types ---

export interface AdminOverview {
  public_count: number;
  industry_count: number;
  template_count: number;
  compliance_count: number;
  recent_updates: { id: string; title: string; category: string; updated_at: string; updated_by: string }[];
}

export interface AdminTemplate {
  id: string;
  title: string;
  content: string;
  category: string;
  variables: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface AdminComplianceWord {
  id: string;
  word: string;
  level: string;
  category: string;
  description: string;
  created_at: string;
}

export interface AdminStats {
  industry_distribution: { name: string; count: number }[];
  category_distribution: { name: string; value: number }[];
  search_hotness: { keyword: string; count: number; trend: string }[];
  tenant_usage: { total_tenants: number; active_tenants: number; total_queries: number; avg_queries_per_tenant: number };
}

// --- Hooks ---

export function useAdminOverview() {
  return useQuery({
    queryKey: ['admin', 'overview'],
    queryFn: async (): Promise<AdminOverview> => {
      // 并行请求 4 个列表 API 后聚合
      const [publicRes, industryRes, templateRes, complianceRes] = await Promise.all([
        adminApi.getPublicKnowledge(),
        adminApi.getIndustryKnowledge(),
        adminApi.getTemplates(),
        adminApi.getComplianceWords(),
      ]);

      const extractItems = (res: { success: boolean; data: unknown }) => {
        if (!res.success || !res.data) return [];
        const data = res.data as { items?: unknown[] } | unknown[];
        return Array.isArray(data) ? data : (data.items || []);
      };

      const publicItems = extractItems(publicRes) as KnowledgeEntry[];
      const industryItems = extractItems(industryRes) as KnowledgeEntry[];
      const templateItems = extractItems(templateRes) as Record<string, unknown>[];
      const complianceItems = extractItems(complianceRes) as Record<string, unknown>[];

      const recent_updates = [
        ...publicItems.map((k) => ({ id: k.id, title: k.title, category: '公共知识库', updated_at: k.updated_at || k.created_at || '', updated_by: '管理员' })),
        ...industryItems.map((k) => ({ id: k.id, title: k.title, category: '行业知识库', updated_at: k.updated_at || k.created_at || '', updated_by: '管理员' })),
      ].sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || '')).slice(0, 10);

      return {
        public_count: publicItems.length,
        industry_count: industryItems.length,
        template_count: templateItems.length,
        compliance_count: complianceItems.length,
        recent_updates,
      };
    },
    staleTime: 60 * 1000,
  });
}

export function useAdminKnowledge(platformCategory?: string) {
  return useQuery<KnowledgeEntry[]>({
    queryKey: ['admin', 'knowledge', platformCategory],
    queryFn: async () => {
      if (platformCategory === 'public') {
        const res = await adminApi.getPublicKnowledge();
        if (res.success && res.data) {
          const data = res.data as { items?: KnowledgeEntry[] } | KnowledgeEntry[];
          return Array.isArray(data) ? data : (data.items || []);
        }
      } else if (platformCategory === 'industry') {
        const res = await adminApi.getIndustryKnowledge();
        if (res.success && res.data) {
          const data = res.data as { items?: KnowledgeEntry[] } | KnowledgeEntry[];
          return Array.isArray(data) ? data : (data.items || []);
        }
      }
      return [];
    },
    staleTime: 0,
  });
}

export function useCreateAdminKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { title: string; content: string; platform_category: string; category?: string; tags?: string[] }) => {
      if (data.platform_category === 'public') {
        return adminApi.createPublicKnowledge({ title: data.title, content: data.content, category: data.category || 'rule', tags: data.tags });
      }
      return adminApi.createIndustryKnowledge({ title: data.title, content: data.content, category: data.category || 'topic', industry: 'health', tags: data.tags });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}

export function useUpdateAdminKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data, platformCategory }: { id: string; data: { title?: string; content?: string; tags?: string[] }; platformCategory?: string }) => {
      if (platformCategory === 'industry') {
        return adminApi.updateIndustryKnowledge(id, data);
      }
      return adminApi.updatePublicKnowledge(id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}

export function useDeleteAdminKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, platformCategory }: { id: string; platformCategory?: string }) => {
      if (platformCategory === 'industry') {
        return adminApi.deleteIndustryKnowledge(id);
      }
      return adminApi.deletePublicKnowledge(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}

export function useAdminTemplates(platform?: string) {
  return useQuery<AdminTemplate[]>({
    queryKey: ['admin', 'templates', platform],
    queryFn: async () => {
      const res = await adminApi.getTemplates(platform ? { platform } : undefined);
      if (res.success && res.data) {
        const data = res.data as { items?: AdminTemplate[] } | AdminTemplate[];
        const items = Array.isArray(data) ? data : (data.items || []);
        return items.map((t) => {
          const raw = t as unknown as Record<string, unknown>;
          return {
            ...t,
            title: t.title || (raw.name as string) || t.title,
            variables: t.variables || [],
          };
        }) as AdminTemplate[];
      }
      return [];
    },
    staleTime: 0,
  });
}

export function useCreateAdminTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { title: string; content: string; category: string; platform?: string }) => {
      return adminApi.createTemplate({ name: data.title, platform: data.platform || 'xiaohongshu', content: data.content, category: data.category });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}

export function useDeleteAdminTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return adminApi.deleteTemplate(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}

export function useAdminComplianceWords(level?: string) {
  return useQuery<AdminComplianceWord[]>({
    queryKey: ['admin', 'compliance', level],
    queryFn: async () => {
      const res = await adminApi.getComplianceWords(level && level !== 'all' ? { category: level } : undefined);
      if (res.success && res.data) {
        const data = res.data as { items?: Record<string, unknown>[] } | Record<string, unknown>[];
        const items = Array.isArray(data) ? data : (data.items || []);
        return items.map((w) => {
          const raw = w as unknown as Record<string, unknown>;
          return {
            ...w,
            level: (raw.severity as string) || w.level,
            description: (raw.suggestion as string) || w.description || '',
          };
        }) as AdminComplianceWord[];
      }
      return [];
    },
    staleTime: 0,
  });
}

export function useCreateAdminComplianceWord() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { word: string; level: string; category?: string; description?: string }) => {
      return adminApi.createComplianceWord({
        word: data.word,
        category: data.category || '',
        severity: data.level,
        suggestion: data.description,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}

export function useDeleteAdminComplianceWord() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return adminApi.deleteComplianceWord(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}

export function useAdminStats() {
  return useQuery<AdminStats>({
    queryKey: ['admin', 'stats'],
    queryFn: async () => {
      // 后端无 stats 接口，从各列表聚合
      const [publicRes, industryRes, templateRes, complianceRes] = await Promise.all([
        adminApi.getPublicKnowledge(),
        adminApi.getIndustryKnowledge(),
        adminApi.getTemplates(),
        adminApi.getComplianceWords(),
      ]);

      const extractItems = (res: { success: boolean; data: unknown }) => {
        if (!res.success || !res.data) return [];
        const data = res.data as { items?: unknown[] } | unknown[];
        return Array.isArray(data) ? data : (data.items || []);
      };

      const publicCount = extractItems(publicRes).length;
      const industryItems = extractItems(industryRes) as KnowledgeEntry[];
      const templateCount = extractItems(templateRes).length;
      const complianceCount = extractItems(complianceRes).length;

      // 按行业分组
      const industryMap: Record<string, number> = {};
      for (const item of industryItems) {
        const meta = (item as Record<string, unknown>).metadata as Record<string, unknown> | undefined;
        const industry = (meta?.industry as string) || '其他';
        industryMap[industry] = (industryMap[industry] || 0) + 1;
      }

      return {
        industry_distribution: Object.entries(industryMap).map(([name, count]) => ({ name, count })),
        category_distribution: [
          { name: '公共知识库', value: publicCount },
          { name: '行业知识库', value: industryItems.length },
          { name: '内置模板', value: templateCount },
          { name: '合规词库', value: complianceCount },
        ],
        search_hotness: [],
        tenant_usage: { total_tenants: 0, active_tenants: 0, total_queries: 0, avg_queries_per_tenant: 0 },
      };
    },
    staleTime: 60 * 1000,
  });
}
