'use client';

import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useAnalyticsOverview } from '@/hooks/use-analytics';
import {
  BarChart3, TrendingUp, FileText, Lightbulb,
  ArrowUpRight, ArrowDownRight, Calendar, Filter,
} from 'lucide-react';
import Link from 'next/link';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell,
} from 'recharts';

export default function AnalyticsContent() {
  const { data: overview } = useAnalyticsOverview();

  const trendData = overview?.trend_data || [];
  const topicData = overview?.topic_ranking || [];
  const strategyData = overview?.strategy_data || [];
  const platformData = overview?.platform_data || [];
  const recentNotes = overview?.recent_notes || [];
  const suggestions = overview?.suggestions || [];

  const complianceBadge = (status: string) => {
    if (status === 'passed') return <Badge className="bg-green-500/10 text-green-500 border-green-500/20">通过</Badge>;
    return <Badge variant="outline" className="border-yellow-500/30 text-yellow-500">待修改</Badge>;
  };

  const priorityBadge = (p: string) => {
    if (p === 'high') return <Badge variant="destructive" className="text-xs">高优先</Badge>;
    if (p === 'medium') return <Badge variant="outline" className="border-yellow-500/30 text-yellow-500 text-xs">中优先</Badge>;
    return <Badge variant="secondary" className="text-xs">低优先</Badge>;
  };

  const tooltipStyle = {
    backgroundColor: 'hsl(var(--card))',
    border: '1px solid hsl(var(--border))',
    borderRadius: '8px',
    fontSize: '12px',
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold lg:text-3xl">数据看板</h1>
            <p className="text-muted-foreground">查看内容创作数据和分析洞察</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm"><Calendar className="mr-2 h-4 w-4" />最近30天</Button>
            <Button variant="outline" size="sm"><Filter className="mr-2 h-4 w-4" />筛选</Button>
          </div>
        </div>

        {/* Metric cards */}
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-5">
          <Card><CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2"><CardTitle className="text-sm font-medium">总创作数</CardTitle><FileText className="h-4 w-4 text-muted-foreground" /></CardHeader><CardContent><div className="text-2xl font-bold">{overview?.total_notes || 0}</div><p className="text-xs text-muted-foreground flex items-center gap-1"><ArrowUpRight className="h-3 w-3 text-green-500" /><span className="text-green-500">+12%</span> 较上月</p></CardContent></Card>
          <Card><CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2"><CardTitle className="text-sm font-medium">平均 AI 味评分</CardTitle><BarChart3 className="h-4 w-4 text-muted-foreground" /></CardHeader><CardContent><div className="text-2xl font-bold">{overview?.avg_ai_score || 0}</div><p className="text-xs text-muted-foreground flex items-center gap-1"><ArrowUpRight className="h-3 w-3 text-green-500" /><span className="text-green-500">+3</span> 较上月</p></CardContent></Card>
          <Card><CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2"><CardTitle className="text-sm font-medium">合规通过率</CardTitle><TrendingUp className="h-4 w-4 text-muted-foreground" /></CardHeader><CardContent><div className="text-2xl font-bold">{overview?.compliance_rate || 0}%</div><p className="text-xs text-muted-foreground flex items-center gap-1"><ArrowUpRight className="h-3 w-3 text-green-500" /><span className="text-green-500">+5%</span> 较上月</p></CardContent></Card>
          <Card><CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2"><CardTitle className="text-sm font-medium">平均字数</CardTitle><FileText className="h-4 w-4 text-muted-foreground" /></CardHeader><CardContent><div className="text-2xl font-bold">{overview?.avg_word_count || 0}</div><p className="text-xs text-muted-foreground flex items-center gap-1"><ArrowDownRight className="h-3 w-3 text-yellow-500" /><span className="text-yellow-500">-12</span> 较上月</p></CardContent></Card>
          <Card><CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2"><CardTitle className="text-sm font-medium">优化建议</CardTitle><Lightbulb className="h-4 w-4 text-muted-foreground" /></CardHeader><CardContent><div className="text-2xl font-bold">{suggestions.length}</div><p className="text-xs text-muted-foreground">条待处理</p></CardContent></Card>
        </div>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="topics">选题分析</TabsTrigger>
            <TabsTrigger value="strategies">策略对比</TabsTrigger>
            <TabsTrigger value="suggestions">优化建议</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader><CardTitle>创作趋势</CardTitle><CardDescription>最近 30 天的创作数量和 AI 味评分趋势</CardDescription></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="date" className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                      <YAxis yAxisId="left" className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                      <YAxis yAxisId="right" orientation="right" domain={[60, 100]} className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Line yAxisId="left" type="monotone" dataKey="count" stroke="hsl(var(--primary))" strokeWidth={2} name="创作数" dot={{ fill: 'hsl(var(--primary))' }} />
                      <Line yAxisId="right" type="monotone" dataKey="ai_score" stroke="#22c55e" strokeWidth={2} name="AI味评分" dot={{ fill: '#22c55e' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>平台分布</CardTitle><CardDescription>各平台创作数量占比</CardDescription></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={240}>
                    <PieChart>
                      <Pie data={platformData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={4} dataKey="value">
                        {platformData.map((entry: { color: string }, index: number) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-6 mt-2">
                    {platformData.map((p: { name: string; value: number; color: string }) => (
                      <div key={p.name} className="flex items-center gap-2 text-sm">
                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: p.color }} />
                        <span>{p.name}</span>
                        <span className="text-muted-foreground">{p.value}篇</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader><CardTitle>最近创作笔记</CardTitle><CardDescription>最近 30 天的创作记录</CardDescription></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentNotes.map((note: { id: string; title: string; platform: string; ai_score: number; compliance: string; date: string }) => (
                    <Link key={note.id} href={`/notes/${note.id}`} className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/30 transition-colors">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{note.title}</p>
                        <div className="flex items-center gap-3 mt-1">
                          <Badge variant="outline" className="text-xs">{note.platform}</Badge>
                          <span className="text-xs text-muted-foreground">{note.date}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right"><p className="text-xs text-muted-foreground">AI 味</p><p className="font-bold text-sm">{note.ai_score}</p></div>
                        {complianceBadge(note.compliance)}
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="topics">
            <Card>
              <CardHeader><CardTitle>选题排名</CardTitle><CardDescription>按互动率排序的热门选题方向</CardDescription></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={topicData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis type="number" className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                    <YAxis dataKey="topic" type="category" width={80} className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="engagement" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} name="互动率" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="strategies">
            <Card>
              <CardHeader><CardTitle>标题策略对比</CardTitle><CardDescription>不同标题策略的使用频率和平均 AI 味评分</CardDescription></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={strategyData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="strategy" className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                    <YAxis className="text-xs" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} name="使用次数" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="suggestions">
            <Card>
              <CardHeader><CardTitle>优化建议</CardTitle><CardDescription>基于数据分析的智能优化建议</CardDescription></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {suggestions.map((s: { id: number; type: string; desc: string; priority: string }) => (
                    <div key={s.id} className="flex items-start gap-3 rounded-lg border p-4">
                      <Lightbulb className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium text-sm">{s.type}</p>
                          {priorityBadge(s.priority)}
                        </div>
                        <p className="text-sm text-muted-foreground">{s.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
