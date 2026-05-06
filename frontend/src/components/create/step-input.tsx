'use client';

import { useCreateStore } from '@/stores/create-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { Sparkles, Lock } from 'lucide-react';

const PLATFORMS = [
  {
    id: 'xiaohongshu' as const,
    name: '小红书',
    desc: '图文笔记，8大标题策略，AI味评分',
    available: true,
  },
  {
    id: 'wechat' as const,
    name: '公众号',
    desc: '深度长文，HTML输出，安全声明',
    available: false,
  },
  {
    id: 'douyin' as const,
    name: '抖音',
    desc: '60秒脚本，时间戳标注，画面建议',
    available: false,
  },
];

const SCENE_OPTIONS = [
  '日常种草', '好物推荐', '使用教程', '测评对比',
  '节日营销', '新品首发', '用户故事', '行业科普',
];

const STYLE_OPTIONS = [
  { value: '口语化', label: '口语化', desc: '像朋友聊天，亲切自然' },
  { value: '专业', label: '专业', desc: '权威可信，数据支撑' },
  { value: '故事型', label: '故事型', desc: '叙事驱动，情感共鸣' },
  { value: '清单型', label: '清单型', desc: '结构清晰，干货满满' },
];

export function StepInput() {
  const {
    platform, brand, product, intent, scene, style,
    setPlatform, setBrand, setProduct, setIntent, setScene, setStyle, nextStep, startCreation,
  } = useCreateStore();

  const canStart = platform && product && scene && style;

  return (
    <div className="space-y-8">
      {/* 平台选择 */}
      <div>
        <Label className="text-base font-medium">选择平台</Label>
        <div className="mt-3 grid grid-cols-3 gap-3">
          {PLATFORMS.map((p) => (
            <button
              key={p.id}
              onClick={() => p.available && setPlatform(p.id)}
              disabled={!p.available}
              className={cn(
                'relative rounded-lg border-2 p-4 text-left transition-all',
                platform === p.id
                  ? 'border-primary bg-primary/5'
                  : p.available
                    ? 'border-border hover:border-primary/50'
                    : 'border-border opacity-50 cursor-not-allowed'
              )}
            >
              {!p.available && (
                <span className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  <Lock className="h-3 w-3" /> 即将上线
                </span>
              )}
              <p className="font-medium">{p.name}</p>
              <p className="mt-1 text-xs text-muted-foreground">{p.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* 品牌/产品 */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="brand">品牌名称</Label>
          <Input
            id="brand"
            placeholder="如：汤臣倍健"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            className="mt-1.5"
          />
        </div>
        <div>
          <Label htmlFor="product">产品名称 *</Label>
          <Input
            id="product"
            placeholder="如：护肝片"
            value={product}
            onChange={(e) => setProduct(e.target.value)}
            className="mt-1.5"
          />
        </div>
      </div>

      {/* 创作意图 */}
      <div>
        <Label htmlFor="intent">创作意图</Label>
        <textarea
          id="intent"
          placeholder="描述你想要创作的内容方向，如：针对经常熬夜加班的年轻白领，推荐护肝片的日常保养功效..."
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          rows={3}
          className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* 场景标签 */}
      <div>
        <Label>场景标签 *</Label>
        <div className="mt-2 flex flex-wrap gap-2">
          {SCENE_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setScene(s)}
              className={cn(
                'rounded-full border px-3 py-1.5 text-sm transition-colors',
                scene === s
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border hover:border-primary/50'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* 风格偏好 */}
      <div>
        <Label>风格偏好 *</Label>
        <div className="mt-2 grid grid-cols-2 gap-3">
          {STYLE_OPTIONS.map((s) => (
            <button
              key={s.value}
              onClick={() => setStyle(s.value)}
              className={cn(
                'rounded-lg border-2 p-3 text-left transition-all',
                style === s.value
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              )}
            >
              <p className="font-medium text-sm">{s.label}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{s.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* 开始创作按钮 */}
      <Button
        onClick={() => { nextStep(); startCreation(); }}
        disabled={!canStart}
        className="w-full"
        size="lg"
      >
        <Sparkles className="mr-2 h-4 w-4" />
        开始创作
      </Button>
    </div>
  );
}
