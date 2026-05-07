'use client';

import { useAdminStats } from '@/hooks/use-admin';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  Activity,
  FileText,
} from 'lucide-react';

const CHART_COLORS = ['#f59e0b', '#3b82f6', '#8b5cf6', '#10b981'];

export default function StatsContent() {
  const { data: stats, isLoading } = useAdminStats();
  const s = stats || {
    industry_distribution: [],
    category_distribution: [],
    search_hotness: [],
    tenant_usage: { total_tenants: 0, active_tenants: 0, total_queries: 0, avg_queries_per_tenant: 0 },
  };

  function getTrendIcon(trend: string) {
    if (trend === 'up') return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="h-4 w-4 text-destructive" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">数据统计</h1>
        <p className="text-muted-foreground">平台知识库使用情况和检索热度分析</p>
      </div>

      {/* Tenant usage cards */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">租户总数</p>
                <p className="text-2xl font-bold">{s.tenant_usage.total_tenants}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">活跃租户</p>
                <p className="text-2xl font-bold">{s.tenant_usage.active_tenants}</p>
              </div>
              <Activity className="h-8 w-8 text-green-500 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">总检索次数</p>
                <p className="text-2xl font-bold">{s.tenant_usage.total_queries.toLocaleString()}</p>
              </div>
              <FileText className="h-8 w-8 text-purple-500 opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">平均检索/租户</p>
                <p className="text-2xl font-bold">{s.tenant_usage.avg_queries_per_tenant}</p>
              </div>
              <Activity className="h-8 w-8 text-amber-500 opacity-80" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Industry distribution bar chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">行业知识库条目分布</CardTitle>
            <CardDescription>各行业知识库条目数量</CardDescription>
          </CardHeader>
          <CardContent>
            {s.industry_distribution.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">暂无数据</p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={s.industry_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Category distribution pie chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">平台知识库分类分布</CardTitle>
            <CardDescription>各类知识库条目占比</CardDescription>
          </CardHeader>
          <CardContent>
            {s.category_distribution.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">暂无数据</p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={s.category_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {s.category_distribution.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend
                    formatter={(value) => <span style={{ color: 'hsl(var(--foreground))', fontSize: '12px' }}>{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Search hotness */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">检索热度 Top 10</CardTitle>
          <CardDescription>租户最常检索的关键词</CardDescription>
        </CardHeader>
        <CardContent>
          {s.search_hotness.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">暂无数据</p>
          ) : (
            <div className="space-y-2">
              {s.search_hotness.map((item, index) => {
                const maxCount = Math.max(...s.search_hotness.map((h) => h.count));
                const widthPercent = (item.count / maxCount) * 100;
                return (
                  <div key={item.keyword} className="flex items-center gap-4">
                    <span className="w-6 text-sm text-muted-foreground text-right">{index + 1}</span>
                    <span className="w-24 text-sm font-medium">{item.keyword}</span>
                    <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500/80 rounded-full transition-all"
                        style={{ width: `${widthPercent}%` }}
                      />
                    </div>
                    <span className="w-16 text-sm text-muted-foreground text-right">{item.count.toLocaleString()}</span>
                    {getTrendIcon(item.trend)}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
