'use client';

import { useCreateStore } from '@/stores/create-store';
import { Heart, MessageCircle, Star, Share2, MoreHorizontal, Loader2, CheckCircle2, XCircle, Circle } from 'lucide-react';

export function PreviewPanel() {
  const {
    currentStep, selectedTitles, customTitle, article, tags,
    aiScore, brand, product, agents, isProcessing, complianceReport,
  } = useCreateStore();

  const title = customTitle || selectedTitles[0] || (product ? `${product}推荐` : '笔记标题');
  const showPreview = currentStep !== 'input';

  if (!showPreview) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
        <div className="text-6xl mb-4">📝</div>
        <p className="text-sm">填写需求后预览效果</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-border px-4 py-3">
        <h3 className="text-sm font-medium">实时预览</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Agent 状态指示器 */}
        {agents.length > 0 && (
          <div className="rounded-lg border p-3 space-y-2">
            <p className="text-xs font-medium text-muted-foreground mb-2">Agent 状态</p>
            {agents.map((agent) => (
              <div key={agent.name} className="flex items-center gap-2 text-xs">
                {agent.status === 'running' ? (
                  <Loader2 className="h-3 w-3 animate-spin text-primary" />
                ) : agent.status === 'completed' ? (
                  <CheckCircle2 className="h-3 w-3 text-green-500" />
                ) : agent.status === 'failed' ? (
                  <XCircle className="h-3 w-3 text-destructive" />
                ) : (
                  <Circle className="h-3 w-3 text-muted-foreground" />
                )}
                <span className={agent.status === 'running' ? 'text-primary font-medium' : 'text-muted-foreground'}>
                  {agent.name}
                </span>
                {agent.message && (
                  <span className="text-muted-foreground truncate">{agent.message}</span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 处理中指示 */}
        {isProcessing && agents.length === 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-primary/5 p-3 text-sm text-primary">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>AI 正在创作中...</span>
          </div>
        )}

        {/* 合规状态 */}
        {complianceReport && (
          <div className={`rounded-lg p-3 text-sm ${
            complianceReport.status === 'passed'
              ? 'bg-green-500/10 text-green-600 dark:text-green-400'
              : complianceReport.p0_issues?.length > 0
                ? 'bg-destructive/10 text-destructive'
                : 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
          }`}>
            {complianceReport.status === 'passed'
              ? '✓ 合规检查通过'
              : complianceReport.p0_issues?.length > 0
                ? `✗ ${complianceReport.p0_issues.length} 个必须修改项`
                : '⚠ 有建议修改项'}
          </div>
        )}

        {/* 模拟小红书卡片 */}
        <div className="mx-auto max-w-[320px] overflow-hidden rounded-xl bg-card shadow-lg">
          {/* 封面区域 */}
          <div className="relative aspect-[3/4] bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-950/30 dark:to-purple-950/30">
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-2">📸</div>
                <p className="text-sm text-muted-foreground">封面图片</p>
              </div>
            </div>
            {/* AI味评分角标 */}
            {aiScore > 0 && (
              <div className="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-1 text-xs text-white">
                AI {aiScore}分
              </div>
            )}
          </div>

          {/* 内容区域 */}
          <div className="p-3 space-y-3">
            {/* 标题 */}
            <h3 className="font-bold text-base leading-snug line-clamp-2">
              {title}
            </h3>

            {/* 正文预览 */}
            {article && (
              <p className="text-sm text-muted-foreground leading-relaxed line-clamp-4">
                {article}
              </p>
            )}

            {/* 标签 */}
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {tags.slice(0, 5).map((tag) => (
                  <span key={tag} className="text-xs text-blue-500">
                    #{tag}
                  </span>
                ))}
                {tags.length > 5 && (
                  <span className="text-xs text-muted-foreground">
                    +{tags.length - 5}
                  </span>
                )}
              </div>
            )}

            {/* 品牌标识 */}
            {brand && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <div className="h-4 w-4 rounded-full bg-primary/10 flex items-center justify-center text-[10px]">
                  {brand[0]}
                </div>
                <span>{brand}</span>
              </div>
            )}

            {/* 互动栏 */}
            <div className="flex items-center justify-between border-t border-border pt-3">
              <button className="flex items-center gap-1 text-muted-foreground">
                <Heart className="h-4 w-4" />
                <span className="text-xs">0</span>
              </button>
              <button className="flex items-center gap-1 text-muted-foreground">
                <MessageCircle className="h-4 w-4" />
                <span className="text-xs">0</span>
              </button>
              <button className="flex items-center gap-1 text-muted-foreground">
                <Star className="h-4 w-4" />
                <span className="text-xs">0</span>
              </button>
              <button className="flex items-center gap-1 text-muted-foreground">
                <Share2 className="h-4 w-4" />
              </button>
              <button className="text-muted-foreground">
                <MoreHorizontal className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* 步骤提示 */}
        <div className="rounded-lg bg-muted p-3">
          <p className="text-xs text-muted-foreground text-center">
            {getStepHint(currentStep)}
          </p>
        </div>
      </div>
    </div>
  );
}

function getStepHint(step: string): string {
  const hints: Record<string, string> = {
    input: '填写需求后开始预览',
    topic: '选择选题方向后继续',
    material: '素材已加载，继续选择标题',
    title: '选择标题后预览效果',
    article: '正文创作完成，查看AI味评分',
    tags: '标签和合规检查完成',
    output: '笔记创作完成！',
  };
  return hints[step] || '';
}
