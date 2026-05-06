'use client';

import { useState } from 'react';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useEnterpriseInfo, useEnterpriseQuota, useUpdateProfile } from '@/hooks/use-user';
import { useAuthStore } from '@/stores/auth-store';
import { useUserStore } from '@/stores/user-store';
import {
  User, Building2, Cpu, Info, CheckCircle2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const LLM_MODELS = [
  { id: 'minimax-m2.7', name: 'MiniMax-M2.7', provider: 'MiniMax', desc: '中文创作能力出色，性价比高', speed: '快', quality: '高', cost: '低', recommended: true },
  { id: 'deepseek-v3', name: 'DeepSeek-V3', provider: 'DeepSeek', desc: '推理能力强，适合深度内容', speed: '中', quality: '高', cost: '中', recommended: false },
  { id: 'qwen-max', name: 'Qwen-Max', provider: '阿里云', desc: '多语言支持，企业级稳定', speed: '快', quality: '中', cost: '中', recommended: false },
  { id: 'gpt-4o-mini', name: 'GPT-4o-mini', provider: 'OpenAI', desc: '通用能力均衡，英文优势', speed: '快', quality: '中', cost: '高', recommended: false },
];

export default function SettingsPage() {
  const { user } = useAuthStore();
  const { version } = useUserStore();
  const { data: enterprise } = useEnterpriseInfo();
  const { data: quota } = useEnterpriseQuota();
  const updateProfile = useUpdateProfile();

  const [selectedModel, setSelectedModel] = useState('minimax-m2.7');
  const [name, setName] = useState(user?.name || '');
  const [saved, setSaved] = useState(false);

  const quotaData = quota || { used: 2, monthly_limit: 5, reset_date: '2026-06-01' };

  const handleSave = async () => {
    if (name !== user?.name) {
      await updateProfile.mutateAsync({ name });
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold lg:text-3xl">设置</h1>
          <p className="text-muted-foreground">管理您的账户、企业和模型配置</p>
        </div>

        <Tabs defaultValue="profile" className="space-y-4">
          <TabsList>
            <TabsTrigger value="profile">个人资料</TabsTrigger>
            <TabsTrigger value="enterprise">企业信息</TabsTrigger>
            <TabsTrigger value="llm">模型配置</TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><User className="h-5 w-5" />个人资料</CardTitle>
                <CardDescription>管理您的个人信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary text-xl font-bold">
                    {user?.name?.[0] || 'U'}
                  </div>
                  <div>
                    <p className="font-medium">{user?.name || '用户'}</p>
                    <p className="text-sm text-muted-foreground">{user?.email}</p>
                    <Badge variant="outline" className="mt-1 text-xs">
                      {user?.role === 'tenant_admin' ? '企业管理员' : '企业用户'}
                    </Badge>
                  </div>
                </div>
                <div className="grid gap-4 max-w-md">
                  <div className="space-y-2">
                    <Label htmlFor="name">姓名</Label>
                    <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="您的姓名" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">邮箱</Label>
                    <Input id="email" value={user?.email || ''} disabled className="opacity-60" />
                  </div>
                </div>
                <Button onClick={handleSave}>
                  {saved ? <><CheckCircle2 className="mr-2 h-4 w-4" />已保存</> : '保存修改'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="enterprise">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Building2 className="h-5 w-5" />企业信息</CardTitle>
                <CardDescription>查看企业套餐和额度使用情况</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2 max-w-lg">
                  <div className="space-y-1"><p className="text-sm text-muted-foreground">企业名称</p><p className="font-medium">{enterprise?.name || '未绑定企业'}</p></div>
                  <div className="space-y-1"><p className="text-sm text-muted-foreground">当前套餐</p><p className="font-medium">{enterprise?.plan || '免费版'}</p></div>
                  <div className="space-y-1"><p className="text-sm text-muted-foreground">企业 ID</p><p className="font-mono text-sm">{user?.enterprise_id || '-'}</p></div>
                  <div className="space-y-1"><p className="text-sm text-muted-foreground">系统版本</p><p className="font-medium">{version}</p></div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm"><span>本月额度使用</span><span className="font-medium">{quotaData.used} / {quotaData.monthly_limit} 篇</span></div>
                  <div className="h-3 bg-muted rounded-full overflow-hidden">
                    <div className={cn('h-full rounded-full transition-all', quotaData.used / quotaData.monthly_limit > 0.8 ? 'bg-yellow-500' : 'bg-primary')} style={{ width: `${(quotaData.used / quotaData.monthly_limit) * 100}%` }} />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    额度将于 {quotaData.reset_date} 重置
                    {quotaData.used / quotaData.monthly_limit > 0.8 && ' — 额度即将用完，建议升级套餐'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="llm">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Cpu className="h-5 w-5" />模型配置</CardTitle>
                <CardDescription>选择创作使用的 LLM 模型，不同模型在速度、质量和成本上各有侧重</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  {LLM_MODELS.map((model) => (
                    <button key={model.id} onClick={() => setSelectedModel(model.id)} className={cn('relative rounded-lg border-2 p-4 text-left transition-all', selectedModel === model.id ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50')}>
                      {model.recommended && <span className="absolute right-2 top-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">推荐</span>}
                      <p className="font-medium">{model.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{model.provider}</p>
                      <p className="text-sm mt-2">{model.desc}</p>
                      <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                        <span>速度: <span className="text-foreground">{model.speed}</span></span>
                        <span>质量: <span className="text-foreground">{model.quality}</span></span>
                        <span>成本: <span className="text-foreground">{model.cost}</span></span>
                      </div>
                    </button>
                  ))}
                </div>
                <div className="flex items-start gap-2 rounded-lg bg-muted/50 p-3 text-sm">
                  <Info className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                  <p className="text-muted-foreground">模型切换将在下次创作时生效。当前选中的模型会用于标题生成、正文创作、标签推荐和合规检查等所有 Agent 任务。</p>
                </div>
                <Button onClick={handleSave}>
                  {saved ? <><CheckCircle2 className="mr-2 h-4 w-4" />已保存</> : '保存配置'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
