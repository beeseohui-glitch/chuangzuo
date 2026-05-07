'use client';

import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useEnterpriseQuota } from '@/hooks/use-user';
import { useKnowledgeStats } from '@/hooks/use-knowledge';
import { useAnalyticsOverview } from '@/hooks/use-analytics';
import {
  PenLine, BookOpen, BarChart3, TrendingUp,
  ArrowRight, Sparkles, Clock, CheckCircle2, AlertCircle,
} from 'lucide-react';
import Link from 'next/link';

const QUICK_PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书笔记', icon: '小', color: 'bg-red-100 text-red-600 dark:bg-red-900/20', desc: '图文笔记，8大标题策略', available: true },
  { id: 'wechat', name: '公众号文章', icon: '公', color: 'bg-green-100 text-green-600 dark:bg-green-900/20', desc: '深度长文，HTML输出', available: false },
  { id: 'douyin', name: '抖音脚本', icon: '抖', color: 'bg-purple-100 text-purple-600 dark:bg-purple-900/20', desc: '60秒脚本，画面建议', available: false },
];

export default function DashboardContent() {
  const { data: quota } = useEnterpriseQuota();
  const { data: kbStats } = useKnowledgeStats();
  const { data: analytics } = useAnalyticsOverview();

  const quotaData = quota || { used: 2, monthly_limit: 5, reset_date: '2026-06-01' };
  const kbCount = kbStats?.total_entries || 0;

  const recentCreations = analytics?.recent_notes?.map((note) => ({
    id: note.id,
    title: note.title,
    platform: note.platform,
    aiScore: note.ai_score,
    compliance: note.compliance as 'passed' | 'needs_revision' | 'failed',
    time: note.date,
  })) || [];

  const totalNotes = analytics?.total_notes || quotaData.used;
  const avgAiScore = analytics?.avg_ai_score || 76;

  const complianceBadge = (status: string) => {
    if (status === 'passed') return <Badge variant="default" className="bg-green-500/10 text-green-500 border-green-500/20">通过</Badge>;
    if (status === 'needs_revision') return <Badge variant="outline" className="border-yellow-500/30 text-yellow-500">待修改</Badge>;
    return <Badge variant="destructive">未通过</Badge>;
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Welcome */}
        <div>
          <h1 className="text-2xl font-bold lg:text-3xl">工作台</h1>
          <p className="text-muted-foreground mt-1">开始您的 AI 内容创作之旅</p>
        </div>

        {/* Stats */}
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">本月创作</CardTitle>
              <PenLine className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalNotes}</div>
              <p className="text-xs text-muted-foreground">剩余 {quotaData.monthly_limit - quotaData.used} 篇额度</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">知识库条目</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kbCount}</div>
              <p className="text-xs text-muted-foreground">条企业知识</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">平均 AI 味评分</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgAiScore}</div>
              <p className="text-xs text-muted-foreground"><span className="text-green-500">+3</span> 较上周</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">合规通过率</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">92%</div>
              <p className="text-xs text-muted-foreground"><span className="text-green-500">+5%</span> 较上周</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Quick start */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                快速开始
              </CardTitle>
              <CardDescription>选择平台开始创作</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {QUICK_PLATFORMS.map((p) => (
                <Link
                  key={p.id}
                  href={p.available ? '/create' : '#'}
                  className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
                    p.available ? 'hover:bg-accent/50 cursor-pointer' : 'opacity-50 cursor-not-allowed'
                  }`}
                >
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full ${p.color}`}>
                    <span className="text-lg font-bold">{p.icon}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm">{p.name}</p>
                    <p className="text-xs text-muted-foreground">{p.desc}</p>
                  </div>
                  {p.available ? (
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Badge variant="outline" className="text-xs">即将上线</Badge>
                  )}
                </Link>
              ))}
            </CardContent>
          </Card>

          {/* Recent creations */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-muted-foreground" />
                    最近创作
                  </CardTitle>
                  <CardDescription>您最近的创作记录</CardDescription>
                </div>
                <Link href="/analytics">
                  <Button variant="ghost" size="sm">查看全部 <ArrowRight className="ml-1 h-3.5 w-3.5" /></Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentCreations.slice(0, 4).map((item) => (
                  <Link key={item.id} href={`/notes/${item.id}`} className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/30 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{item.title}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <Badge variant="outline" className="text-xs">{item.platform}</Badge>
                        <span className="text-xs text-muted-foreground">{item.time}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">AI 味</p>
                        <p className="font-bold text-sm">{item.aiScore}</p>
                      </div>
                      {complianceBadge(item.compliance)}
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Bottom cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">本周创作趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-1 h-16">
                {[3, 5, 2, 8, 4, 6, 7].map((v, i) => (
                  <div key={i} className="flex-1 bg-primary/20 rounded-t" style={{ height: `${(v / 8) * 100}%` }} />
                ))}
              </div>
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">知识库状态</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">企业私有库</span>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                  <span className="text-sm font-medium">{kbCount} 条</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">行业知识库</span>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                  <span className="text-sm font-medium">5 条</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">向量索引</span>
                <div className="flex items-center gap-1.5">
                  <AlertCircle className="h-3.5 w-3.5 text-yellow-500" />
                  <span className="text-sm font-medium">需同步</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">额度使用</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>本月已用</span>
                    <span className="font-medium">{quotaData.used}/{quotaData.monthly_limit}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${(quotaData.used / quotaData.monthly_limit) * 100}%` }} />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">额度将于 {quotaData.reset_date} 重置</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
