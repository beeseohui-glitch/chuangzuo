'use client';

import { useCreateStore } from '@/stores/create-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AgentStatus } from '@/components/shared/agent-status';
import { Building2, Package, Users, MapPin, ShieldCheck, AlertTriangle, ArrowRight } from 'lucide-react';

export function StepMaterial() {
  const {
    materialPack, materialMissing, isProcessing,
    nextStep, prevStep,
  } = useCreateStore();

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <AgentStatus status="running" agentName="素材检索Agent" label="正在从知识库检索相关素材..." />
        <p className="text-sm text-muted-foreground">正在搜索企业知识库、行业知识库...</p>
      </div>
    );
  }

  if (!materialPack) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <AlertTriangle className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">暂无素材数据，请先完成需求输入</p>
        <Button variant="outline" onClick={prevStep}>返回上一步</Button>
      </div>
    );
  }

  const sections = [
    {
      icon: Building2,
      title: '品牌信息',
      content: (
        <div className="space-y-2">
          <p><span className="text-muted-foreground">品牌名称：</span>{materialPack.brand.name}</p>
          <div>
            <span className="text-muted-foreground">品牌调性：</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {materialPack.brand.tone.map((t) => (
                <Badge key={t} variant="secondary">{t}</Badge>
              ))}
            </div>
          </div>
          {materialPack.brand.taboos.length > 0 && (
            <div>
              <span className="text-muted-foreground">禁忌词：</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {materialPack.brand.taboos.map((t) => (
                  <Badge key={t} variant="destructive">{t}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      icon: Package,
      title: '产品信息',
      content: (
        <div className="space-y-2">
          <p><span className="text-muted-foreground">产品名称：</span>{materialPack.product.name}</p>
          <div>
            <span className="text-muted-foreground">核心卖点：</span>
            <ul className="mt-1 list-inside list-disc space-y-1">
              {materialPack.product.selling_points.map((s) => (
                <li key={s} className="text-sm">{s}</li>
              ))}
            </ul>
          </div>
          {materialPack.product.ingredients.length > 0 && (
            <div>
              <span className="text-muted-foreground">核心成分：</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {materialPack.product.ingredients.map((i) => (
                  <Badge key={i} variant="outline">{i}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      icon: Users,
      title: '人群画像',
      content: (
        <div className="space-y-2">
          <p><span className="text-muted-foreground">目标人群：</span>{materialPack.persona.profile}</p>
          <div>
            <span className="text-muted-foreground">痛点需求：</span>
            <ul className="mt-1 list-inside list-disc space-y-1">
              {materialPack.persona.pain_points.map((p) => (
                <li key={p} className="text-sm">{p}</li>
              ))}
            </ul>
          </div>
          <p><span className="text-muted-foreground">语言风格：</span>{materialPack.persona.language_style}</p>
        </div>
      ),
    },
    {
      icon: MapPin,
      title: '场景信息',
      content: (
        <div className="space-y-2">
          <p><span className="text-muted-foreground">使用场景：</span>{materialPack.scene.description}</p>
          <p><span className="text-muted-foreground">使用方法：</span>{materialPack.scene.usage_method}</p>
        </div>
      ),
    },
    {
      icon: ShieldCheck,
      title: '合规信息',
      content: (
        <div className="space-y-2">
          <div>
            <span className="text-muted-foreground">合规规则：</span>
            <ul className="mt-1 list-inside list-disc space-y-1">
              {materialPack.compliance.rules.map((r) => (
                <li key={r} className="text-sm">{r}</li>
              ))}
            </ul>
          </div>
          {materialPack.compliance.forbidden_groups.length > 0 && (
            <div>
              <span className="text-muted-foreground">禁用人群：</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {materialPack.compliance.forbidden_groups.map((g) => (
                  <Badge key={g} variant="destructive">{g}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* 缺失项提示 */}
      {materialMissing.length > 0 && (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-4">
          <div className="flex items-center gap-2 text-yellow-500">
            <AlertTriangle className="h-4 w-4" />
            <span className="font-medium">以下信息缺失，可能影响创作质量</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {materialMissing.map((m) => (
              <Badge key={m} variant="outline" className="border-yellow-500/30 text-yellow-500">
                {m}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* 素材包卡片 */}
      <div className="grid grid-cols-1 gap-4">
        {sections.map((section) => (
          <Card key={section.title}>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <section.icon className="h-4 w-4 text-muted-foreground" />
                {section.title}
              </CardTitle>
            </CardHeader>
            <CardContent>{section.content}</CardContent>
          </Card>
        ))}
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={prevStep}>
          返回修改需求
        </Button>
        <div className="flex gap-3">
          <Button variant="outline">
            补充素材
          </Button>
          <Button onClick={nextStep}>
            确认继续
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
