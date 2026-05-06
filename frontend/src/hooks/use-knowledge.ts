'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '@/lib/api';
import { KnowledgeEntry } from '@/types';

function isDevMode(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('dev_mode') !== 'false';
}

const MOCK_KNOWLEDGE_LIST: KnowledgeEntry[] = [
  { id: 1, data_level: 'tenant', platform_category: null, enterprise_id: 'dev-enterprise-001', category: 'product', title: '护肝片产品知识库', content: '水飞蓟素是护肝片的核心成分，具有保护肝细胞、促进肝细胞再生的作用。适用于经常熬夜、饮酒、工作压力大的人群。', source: '产品手册', source_url: null, tags: ['护肝片', '水飞蓟', '保健品'], metadata: {}, created_by: 'dev-user-001', updated_by: null, created_at: '2026-05-04T10:00:00Z', updated_at: '2026-05-04T10:00:00Z' },
  { id: 2, data_level: 'tenant', platform_category: null, enterprise_id: 'dev-enterprise-001', category: 'industry', title: '睡眠健康行业报告', content: '2024年中国睡眠健康市场规模持续增长，其中褪黑素类产品占据较大市场份额。消费者对天然成分的偏好日益明显。', source: '行业报告', source_url: null, tags: ['睡眠', '褪黑素', '行业'], metadata: {}, created_by: 'dev-user-001', updated_by: null, created_at: '2026-05-03T10:00:00Z', updated_at: '2026-05-03T10:00:00Z' },
  { id: 3, data_level: 'tenant', platform_category: null, enterprise_id: 'dev-enterprise-001', category: 'brand', title: '品牌调性规范', content: '品牌语调应保持专业、亲切、可信。禁止使用"最好"、"第一"等绝对化用语。内容需符合保健品广告法规要求。', source: '品牌手册', source_url: null, tags: ['品牌', '调性', '规范'], metadata: {}, created_by: 'dev-user-001', updated_by: null, created_at: '2026-05-01T10:00:00Z', updated_at: '2026-05-01T10:00:00Z' },
  { id: 4, data_level: 'tenant', platform_category: null, enterprise_id: 'dev-enterprise-001', category: 'template', title: '小红书笔记模板', content: '开头：引入痛点场景，引起共鸣\n中间：产品体验分享，真实感受\n结尾：购买建议+互动引导', source: '运营团队', source_url: null, tags: ['模板', '小红书'], metadata: {}, created_by: 'dev-user-001', updated_by: null, created_at: '2026-04-28T10:00:00Z', updated_at: '2026-04-28T10:00:00Z' },
  { id: 5, data_level: 'tenant', platform_category: null, enterprise_id: 'dev-enterprise-001', category: 'compliance', title: '保健品合规规则', content: 'P0级：禁止暗示治疗效果、禁止使用绝对化用语\nP1级：需标注适宜人群、不适宜人群\nP2级：建议补充使用周期说明', source: '法务部门', source_url: null, tags: ['合规', '保健品', '规则'], metadata: {}, created_by: 'dev-user-001', updated_by: null, created_at: '2026-04-25T10:00:00Z', updated_at: '2026-04-25T10:00:00Z' },
  { id: 6, data_level: 'tenant', platform_category: null, enterprise_id: 'dev-enterprise-001', category: 'product', title: '益生菌产品知识', content: '益生菌是一类对宿主有益的活性微生物，常见菌种包括乳酸杆菌、双歧杆菌。建议饭后服用，避免与抗生素同时使用。', source: '产品手册', source_url: null, tags: ['益生菌', '肠道健康'], metadata: {}, created_by: 'dev-user-001', updated_by: null, created_at: '2026-04-20T10:00:00Z', updated_at: '2026-04-20T10:00:00Z' },
];

const MOCK_STATS = {
  total_entries: 6,
  by_category: { product: 2, industry: 1, brand: 1, template: 1, compliance: 1 },
  recent_updates: MOCK_KNOWLEDGE_LIST.slice(0, 3),
};

export function useKnowledgeList(category?: string) {
  return useQuery({
    queryKey: ['knowledge', 'list', category],
    queryFn: async () => {
      const res = await knowledgeApi.getList({ category: category !== 'all' ? category : undefined });
      if (res.success && res.data) return res.data as KnowledgeEntry[];
      if (isDevMode()) {
        if (!category || category === 'all') return MOCK_KNOWLEDGE_LIST;
        return MOCK_KNOWLEDGE_LIST.filter((k) => k.category === category);
      }
      throw new Error(res.error || '获取知识列表失败');
    },
    staleTime: 60 * 1000,
  });
}

export interface KnowledgeStats {
  total_entries: number;
  by_category: Record<string, number>;
  recent_updates: KnowledgeEntry[];
}

export function useKnowledgeStats() {
  return useQuery<KnowledgeStats>({
    queryKey: ['knowledge', 'stats'],
    queryFn: async () => {
      const res = await knowledgeApi.getStats();
      if (res.success && res.data) return res.data as KnowledgeStats;
      if (isDevMode()) return MOCK_STATS;
      throw new Error(res.error || '获取知识统计失败');
    },
    staleTime: 60 * 1000,
  });
}

export function useCreateKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; content: string; category?: string; tags?: string[] }) =>
      knowledgeApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useDeleteKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => knowledgeApi.delete(id),
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
      if (res.success && res.data) return res.data as KnowledgeEntry[];
      if (isDevMode()) {
        const q = query.toLowerCase();
        return MOCK_KNOWLEDGE_LIST.filter(
          (k) => k.title.toLowerCase().includes(q) || k.tags.some((t) => t.includes(q))
        );
      }
      throw new Error(res.error || '搜索失败');
    },
    enabled: query.length > 0,
    staleTime: 30 * 1000,
  });
}
