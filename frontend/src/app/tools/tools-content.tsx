'use client';

import { useState } from 'react';
import { agentsApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import {
  PenLine, FileText, Tags, ShieldCheck, Search, Lightbulb,
  Database, BarChart3, Calendar, MessageSquare, Video, Bot,
  Loader2, Play,
} from 'lucide-react';

interface ToolDef {
  id: string;
  name: string;
  desc: string;
  icon: React.ComponentType<{ className?: string }>;
  category: '创作' | '审核' | '数据' | '运营';
  fields: { key: string; label: string; placeholder: string; type?: 'input' | 'textarea' }[];
}

const TOOLS: ToolDef[] = [
  {
    id: 'title',
    name: '标题生成',
    desc: '根据主题和素材生成多个标题方案',
    icon: PenLine,
    category: '创作',
    fields: [
      { key: 'topic', label: '主题', placeholder: '如：护肝片' },
      { key: 'material_pack', label: '素材包 (JSON)', placeholder: '{}', type: 'textarea' },
    ],
  },
  {
    id: 'article',
    name: '正文生成',
    desc: '根据标题和素材生成小红书笔记正文',
    icon: FileText,
    category: '创作',
    fields: [
      { key: 'title', label: '标题', placeholder: '输入标题' },
      { key: 'material_pack', label: '素材包 (JSON)', placeholder: '{}', type: 'textarea' },
    ],
  },
  {
    id: 'tag',
    name: '标签生成',
    desc: '根据正文内容生成平台标签',
    icon: Tags,
    category: '创作',
    fields: [
      { key: 'article', label: '正文', placeholder: '输入正文内容', type: 'textarea' },
      { key: 'title', label: '标题', placeholder: '输入标题' },
    ],
  },
  {
    id: 'compliance',
    name: '合规检查',
    desc: '检查内容是否符合平台规范和广告法',
    icon: ShieldCheck,
    category: '审核',
    fields: [
      { key: 'title', label: '标题', placeholder: '输入标题' },
      { key: 'article', label: '正文', placeholder: '输入正文', type: 'textarea' },
      { key: 'tags', label: '标签 (逗号分隔)', placeholder: '标签1, 标签2' },
    ],
  },
  {
    id: 'topic',
    name: '选题推荐',
    desc: '基于品类和产品推荐内容选题',
    icon: Lightbulb,
    category: '创作',
    fields: [
      { key: 'category', label: '品类', placeholder: '如：health_product' },
      { key: 'product', label: '产品', placeholder: '如：护肝片' },
      { key: 'brand_name', label: '品牌 (可选)', placeholder: '如：汤臣倍健' },
    ],
  },
  {
    id: 'material',
    name: '素材检索',
    desc: '从知识库检索相关素材',
    icon: Search,
    category: '数据',
    fields: [
      { key: 'product', label: '产品', placeholder: '如：护肝片' },
      { key: 'scene', label: '场景 (可选)', placeholder: '如：熬夜加班' },
    ],
  },
  {
    id: 'kb',
    name: '知识库搜索',
    desc: '搜索企业知识库',
    icon: Database,
    category: '数据',
    fields: [
      { key: 'query', label: '搜索词', placeholder: '输入关键词' },
      { key: 'category', label: '分类 (可选)', placeholder: '如：product' },
    ],
  },
  {
    id: 'analytics',
    name: '数据分析',
    desc: '生成内容数据分析报告',
    icon: BarChart3,
    category: '数据',
    fields: [
      { key: 'period_start', label: '开始日期', placeholder: '2026-01-01' },
      { key: 'period_end', label: '结束日期', placeholder: '2026-01-31' },
    ],
  },
  {
    id: 'operation',
    name: '运营计划',
    desc: '生成内容发布运营计划',
    icon: Calendar,
    category: '运营',
    fields: [
      { key: 'pending_content', label: '待发内容 (JSON)', placeholder: '{}', type: 'textarea' },
      { key: 'target_platforms', label: '目标平台 (逗号分隔)', placeholder: 'xiaohongshu, douyin' },
    ],
  },
  {
    id: 'wechat',
    name: '公众号文章',
    desc: '生成微信公众号长文',
    icon: MessageSquare,
    category: '创作',
    fields: [
      { key: 'topic', label: '主题', placeholder: '输入主题' },
      { key: 'material_pack', label: '素材包 (JSON)', placeholder: '{}', type: 'textarea' },
    ],
  },
  {
    id: 'douyin',
    name: '抖音脚本',
    desc: '生成抖音短视频脚本',
    icon: Video,
    category: '创作',
    fields: [
      { key: 'topic', label: '主题', placeholder: '输入主题' },
      { key: 'material_pack', label: '素材包 (JSON)', placeholder: '{}', type: 'textarea' },
    ],
  },
  {
    id: 'orchestrator',
    name: '智能路由',
    desc: '识别用户意图并路由到对应 Agent',
    icon: Bot,
    category: '运营',
    fields: [
      { key: 'user_input', label: '用户输入', placeholder: '如：帮我写一篇小红书护肝片笔记', type: 'textarea' },
    ],
  },
];

const CATEGORIES = ['全部', '创作', '审核', '数据', '运营'] as const;

export function ToolsContent() {
  const [category, setCategory] = useState<string>('全部');
  const [selectedTool, setSelectedTool] = useState<ToolDef | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredTools = category === '全部'
    ? TOOLS
    : TOOLS.filter((t) => t.category === category);

  const handleSelectTool = (tool: ToolDef) => {
    setSelectedTool(tool);
    setFormValues({});
    setResult(null);
    setError(null);
  };

  const handleRun = async () => {
    if (!selectedTool) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 构建参数
      const params: Record<string, unknown> = {};
      for (const field of selectedTool.fields) {
        const val = formValues[field.key] || '';
        if (!val) continue;

        // 处理特殊字段
        if (field.key === 'tags' || field.key === 'target_platforms') {
          params[field.key] = val.split(',').map((s) => s.trim()).filter(Boolean);
        } else if (field.key === 'material_pack' || field.key === 'pending_content') {
          try {
            params[field.key] = JSON.parse(val);
          } catch {
            params[field.key] = {};
          }
        } else {
          params[field.key] = val;
        }
      }

      const methodMap: Record<string, string> = {
        title: 'generate',
        article: 'generate',
        tag: 'generate',
        compliance: 'check',
        topic: 'generate',
        material: 'search',
        kb: 'search',
        analytics: 'report',
        operation: 'plan',
        wechat: 'generate',
        douyin: 'generate',
        orchestrator: 'route',
      };

      const res = await agentsApi.run({
        agent_name: selectedTool.id,
        method: methodMap[selectedTool.id] || 'run',
        params,
      });

      if (res.success && res.data) {
        setResult(JSON.stringify(res.data, null, 2));
      } else {
        setError(res.error || '调用失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '网络错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI 工具箱</h1>
        <p className="text-muted-foreground">独立调用各 Agent 能力，快速完成单步任务</p>
      </div>

      {/* 分类筛选 */}
      <div className="flex gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={cn(
              'rounded-full px-3 py-1.5 text-sm transition-colors',
              category === cat
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* 工具列表 */}
        <div className="lg:col-span-1 space-y-2">
          {filteredTools.map((tool) => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.id}
                onClick={() => handleSelectTool(tool)}
                className={cn(
                  'w-full rounded-lg border p-3 text-left transition-all',
                  selectedTool?.id === tool.id
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn(
                    'h-5 w-5 shrink-0',
                    selectedTool?.id === tool.id ? 'text-primary' : 'text-muted-foreground'
                  )} />
                  <div>
                    <p className="font-medium text-sm">{tool.name}</p>
                    <p className="text-xs text-muted-foreground">{tool.desc}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* 工具详情和执行 */}
        <div className="lg:col-span-2">
          {selectedTool ? (
            <div className="rounded-lg border p-6 space-y-4">
              <div className="flex items-center gap-3">
                <selectedTool.icon className="h-6 w-6 text-primary" />
                <div>
                  <h3 className="font-medium">{selectedTool.name}</h3>
                  <p className="text-sm text-muted-foreground">{selectedTool.desc}</p>
                </div>
              </div>

              {/* 参数表单 */}
              <div className="space-y-3">
                {selectedTool.fields.map((field) => (
                  <div key={field.key}>
                    <Label htmlFor={field.key}>{field.label}</Label>
                    {field.type === 'textarea' ? (
                      <textarea
                        id={field.key}
                        placeholder={field.placeholder}
                        value={formValues[field.key] || ''}
                        onChange={(e) => setFormValues({ ...formValues, [field.key]: e.target.value })}
                        rows={3}
                        className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                    ) : (
                      <Input
                        id={field.key}
                        placeholder={field.placeholder}
                        value={formValues[field.key] || ''}
                        onChange={(e) => setFormValues({ ...formValues, [field.key]: e.target.value })}
                        className="mt-1"
                      />
                    )}
                  </div>
                ))}
              </div>

              {/* 执行按钮 */}
              <Button onClick={handleRun} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    执行中...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    执行
                  </>
                )}
              </Button>

              {/* 结果展示 */}
              {error && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {result && (
                <div className="space-y-2">
                  <Label>执行结果</Label>
                  <pre className="max-h-96 overflow-auto rounded-md bg-muted p-4 text-xs">
                    {result}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
              选择左侧工具开始使用
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
