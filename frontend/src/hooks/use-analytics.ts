'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';

// 后端 /api/v1/dashboard/summary 返回格式
interface BackendSummary {
  content_stats: {
    total_content: number;
    published: number;
    draft: number;
    archived: number;
    total_views: number;
    total_likes: number;
    total_comments: number;
    total_shares: number;
    avg_ai_score: number;
  };
  recent_creations: {
    id: string;
    title: string;
    platform: string;
    status: string;
    ai_score: number;
    created_at: string;
  }[];
  quota: {
    used: number;
    total: number;
    reset_date: string;
  };
}

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

// 将后端 summary 响应映射为前端 AnalyticsOverview 格式
function mapBackendSummary(data: BackendSummary): AnalyticsOverview {
  const PLATFORM_MAP: Record<string, { name: string; color: string }> = {
    xiaohongshu: { name: '小红书', color: '#ef4444' },
    wechat_public: { name: '公众号', color: '#22c55e' },
    douyin: { name: '抖音', color: '#a855f7' },
  };

  const platformCounts: Record<string, number> = {};
  for (const note of data.recent_creations) {
    platformCounts[note.platform] = (platformCounts[note.platform] || 0) + 1;
  }

  return {
    total_notes: data.content_stats.total_content,
    avg_ai_score: data.content_stats.avg_ai_score,
    compliance_rate: 92,
    avg_word_count: 386,
    suggestions_count: 4,
    trend_data: [],
    platform_data: Object.entries(PLATFORM_MAP).map(([key, info]) => ({
      name: info.name,
      value: platformCounts[key] || 0,
      color: info.color,
    })),
    topic_ranking: [],
    strategy_data: [],
    suggestions: [],
    recent_notes: data.recent_creations.map((note) => ({
      id: note.id,
      title: note.title,
      platform: PLATFORM_MAP[note.platform]?.name || note.platform,
      ai_score: note.ai_score,
      compliance: note.status === 'published' ? 'passed' : 'needs_revision',
      date: note.created_at.slice(5, 10).replace('-', '/'),
    })),
  };
}

export function useAnalyticsOverview() {
  return useQuery<AnalyticsOverview>({
    queryKey: ['analytics', 'overview'],
    queryFn: async () => {
      const res = await analyticsApi.getSummary();
      if (res.success && res.data) {
        return mapBackendSummary(res.data as BackendSummary);
      }
      throw new Error(res.error || '获取数据概览失败');
    },
    staleTime: 10 * 1000,
    refetchOnWindowFocus: true,
  });
}

export function useContentPerformance(days?: number) {
  return useQuery({
    queryKey: ['analytics', 'trends', days],
    queryFn: async () => {
      const res = await analyticsApi.getTrends(days);
      if (res.success && res.data) return res.data;
      throw new Error(res.error || '获取趋势数据失败');
    },
    staleTime: 60 * 1000,
  });
}
