'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';

function isDevMode(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('dev_mode') !== 'false';
}

const MOCK_OVERVIEW = {
  total_notes: 40,
  avg_ai_score: 76,
  compliance_rate: 92,
  avg_word_count: 386,
  suggestions_count: 4,
  trend_data: [
    { date: '04/01', count: 3, ai_score: 72 },
    { date: '04/05', count: 5, ai_score: 75 },
    { date: '04/10', count: 2, ai_score: 70 },
    { date: '04/15', count: 8, ai_score: 78 },
    { date: '04/20', count: 6, ai_score: 76 },
    { date: '04/25', count: 4, ai_score: 80 },
    { date: '05/01', count: 7, ai_score: 82 },
    { date: '05/06', count: 5, ai_score: 79 },
  ],
  platform_data: [
    { name: '小红书', value: 45, color: '#ef4444' },
    { name: '公众号', value: 0, color: '#22c55e' },
    { name: '抖音', value: 0, color: '#a855f7' },
  ],
  topic_ranking: [
    { topic: '好物推荐', count: 12, engagement: 85 },
    { topic: '使用教程', count: 9, engagement: 78 },
    { topic: '测评对比', count: 7, engagement: 82 },
    { topic: '日常种草', count: 6, engagement: 70 },
    { topic: '节日营销', count: 4, engagement: 88 },
  ],
  strategy_data: [
    { strategy: '痛点', count: 15, avg_score: 82 },
    { strategy: '故事', count: 12, avg_score: 78 },
    { strategy: '测评', count: 10, avg_score: 75 },
    { strategy: '提问', count: 8, avg_score: 72 },
    { strategy: '教程', count: 6, avg_score: 80 },
    { strategy: '清单', count: 5, avg_score: 76 },
  ],
  suggestions: [
    { id: 1, type: '标题优化', desc: '使用"痛点"策略的标题平均 AI 味评分最高（82分），建议优先采用', priority: 'high' },
    { id: 2, type: '内容策略', desc: '测评对比类内容互动率最高，建议增加该类型创作频率', priority: 'medium' },
    { id: 3, type: '合规提醒', desc: '近7天有2篇内容需要修改，主要是缺少产品使用周期说明', priority: 'low' },
    { id: 4, type: '知识库', desc: '建议补充"护肝片"相关的专业知识条目，提升内容专业度', priority: 'medium' },
  ],
  recent_notes: [
    { id: '1', title: '护肝片｜打工人的必备好物', platform: '小红书', ai_score: 82, compliance: 'passed', date: '05/06' },
    { id: '2', title: '用了褪黑素之后，我的睡眠变了', platform: '小红书', ai_score: 75, compliance: 'passed', date: '05/05' },
    { id: '3', title: '维生素C测评｜真实体验分享', platform: '小红书', ai_score: 68, compliance: 'needs_revision', date: '05/03' },
    { id: '4', title: '为什么我推荐益生菌？', platform: '小红书', ai_score: 79, compliance: 'passed', date: '05/01' },
    { id: '5', title: '护肝片使用指南｜新手必看', platform: '小红书', ai_score: 76, compliance: 'passed', date: '04/28' },
  ],
};

export interface AnalyticsOverview {
  total_notes: number;
  avg_ai_score: number;
  compliance_rate: number;
  avg_word_count: number;
  suggestions_count: number;
  trend_data: { date: string; count: number; ai_score: number }[];
  platform_data: { name: string; value: number; color: string }[];
  topic_ranking: { topic: string; count: number; engagement: number }[];
  strategy_data: { strategy: string; count: number; avg_score: number }[];
  suggestions: { id: number; type: string; desc: string; priority: string }[];
  recent_notes: { id: string; title: string; platform: string; ai_score: number; compliance: string; date: string }[];
}

export function useAnalyticsOverview() {
  return useQuery<AnalyticsOverview>({
    queryKey: ['analytics', 'overview'],
    queryFn: async () => {
      const res = await analyticsApi.getOverview();
      if (res.success && res.data) return res.data as AnalyticsOverview;
      if (isDevMode()) return MOCK_OVERVIEW;
      throw new Error(res.error || '获取数据概览失败');
    },
    staleTime: 60 * 1000,
  });
}

export function useContentPerformance(platform?: string, dateRange?: string) {
  return useQuery({
    queryKey: ['analytics', 'performance', platform, dateRange],
    queryFn: async () => {
      const res = await analyticsApi.getContentPerformance({ platform, date_range: dateRange });
      if (res.success && res.data) return res.data;
      if (isDevMode()) return MOCK_OVERVIEW;
      throw new Error(res.error || '获取内容表现失败');
    },
    staleTime: 60 * 1000,
  });
}

export function useRecommendations() {
  return useQuery({
    queryKey: ['analytics', 'recommendations'],
    queryFn: async () => {
      const res = await analyticsApi.getRecommendations();
      if (res.success && res.data) return res.data;
      if (isDevMode()) return MOCK_OVERVIEW.suggestions;
      throw new Error(res.error || '获取优化建议失败');
    },
    staleTime: 5 * 60 * 1000,
  });
}
