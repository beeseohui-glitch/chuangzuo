'use client';

import Link from 'next/link';
import { useAdminOverview } from '@/hooks/use-admin';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Globe,
  Building2,
  FileText,
  ShieldCheck,
  ArrowRight,
  Clock,
} from 'lucide-react';

export default function AdminContent() {
  const { data: overview, isLoading } = useAdminOverview();
  const stats = overview || { public_count: 0, industry_count: 0, template_count: 0, compliance_count: 0, recent_updates: [] };

  const statCards = [
    { title: '公共知识库', value: stats.public_count, icon: Globe, href: '/admin/knowledge/public', color: 'text-blue-500' },
    { title: '行业知识库', value: stats.industry_count, icon: Building2, href: '/admin/knowledge/industry', color: 'text-green-500' },
    { title: '内置模板', value: stats.template_count, icon: FileText, href: '/admin/templates', color: 'text-purple-500' },
    { title: '合规词库', value: stats.compliance_count, icon: ShieldCheck, href: '/admin/compliance', color: 'text-amber-500' },
  ];

  const quickLinks = [
    { title: '管理公共知识库', desc: '平台规则、创作方法论、合规通用规则', href: '/admin/knowledge/public', icon: Globe },
    { title: '管理行业知识库', desc: '保健品、AI行业选题库、用户画像', href: '/admin/knowledge/industry', icon: Building2 },
    { title: '管理内置模板', desc: '品牌模板、产品模板、人群模板', href: '/admin/templates', icon: FileText },
    { title: '管理合规词库', desc: '违禁词库(P0)、敏感词库(P1)', href: '/admin/compliance', icon: ShieldCheck },
    { title: '查看数据统计', desc: '知识库条目分布、检索热度分析', href: '/admin/stats', icon: Clock },
  ];

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
        <h1 className="text-2xl font-bold">平台管理后台</h1>
        <p className="text-muted-foreground">管理公共知识库、行业知识库、内置模板和合规词库</p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Link key={card.title} href={card.href}>
              <Card className="hover:border-amber-500/50 transition-colors cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{card.title}</p>
                      <p className="text-2xl font-bold">{card.value}</p>
                    </div>
                    <Icon className={`h-8 w-8 ${card.color} opacity-80`} />
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent updates */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">最近更新</CardTitle>
            <CardDescription>平台知识库最近变更记录</CardDescription>
          </CardHeader>
          <CardContent>
            {stats.recent_updates.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">暂无更新记录</p>
            ) : (
              <div className="space-y-3">
                {stats.recent_updates.map((item) => (
                  <div key={item.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">{item.title}</p>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-xs">{item.category}</Badge>
                        <span className="text-xs text-muted-foreground">{item.updated_by}</span>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(item.updated_at).toLocaleDateString('zh-CN')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">快捷操作</CardTitle>
            <CardDescription>快速进入各管理模块</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {quickLinks.map((link) => {
                const Icon = link.icon;
                return (
                  <Link key={link.href} href={link.href}>
                    <div className="flex items-center justify-between rounded-md p-3 hover:bg-amber-500/10 transition-colors group cursor-pointer">
                      <div className="flex items-center gap-3">
                        <Icon className="h-5 w-5 text-amber-500" />
                        <div>
                          <p className="text-sm font-medium">{link.title}</p>
                          <p className="text-xs text-muted-foreground">{link.desc}</p>
                        </div>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-amber-500 transition-colors" />
                    </div>
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
