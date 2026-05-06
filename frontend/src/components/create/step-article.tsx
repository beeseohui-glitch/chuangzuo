'use client';

import { useCreateStore } from '@/stores/create-store';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { AgentStatus } from '@/components/shared/agent-status';
import { AIScoreRing } from '@/components/shared/ai-score-ring';
import { cn } from '@/lib/utils';
import { RefreshCw, Edit3, ArrowRight, ArrowLeft, Save, X } from 'lucide-react';

const DIMENSIONS = ['去AI味', '口语化', '情感共鸣', '信息密度', '可读性'];

export function StepArticle() {
  const {
    article, aiScore, aiScoreDetails, articleRetries, maxArticleRetries,
    isEditing, isProcessing,
    setArticle, setArticleRetries, setIsEditing,
    nextStep, prevStep,
  } = useCreateStore();

  const canRegenerate = articleRetries < maxArticleRetries;

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <AgentStatus status="running" agentName="正文Agent" label="正在创作正文..." />
        <p className="text-sm text-muted-foreground">运用去AI味策略，生成自然流畅的内容</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI味评分仪表盘 */}
      {aiScore > 0 && (
        <div className="rounded-lg border border-border bg-card p-6">
          <Label className="text-base font-medium">AI味评分</Label>
          <div className="mt-4 flex items-center gap-8">
            <AIScoreRing score={aiScore} size={100} strokeWidth={8} />
            <div className="flex-1">
              {/* 雷达图替代：5维度条形图 */}
              <div className="space-y-2">
                {DIMENSIONS.map((dim) => {
                  const value = aiScoreDetails[dim] || 0;
                  return (
                    <div key={dim} className="flex items-center gap-3">
                      <span className="w-16 text-xs text-muted-foreground">{dim}</span>
                      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all',
                            value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-yellow-500' : 'bg-destructive'
                          )}
                          style={{ width: `${value}%` }}
                        />
                      </div>
                      <span className="w-8 text-xs text-right text-muted-foreground">{value}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 正文预览/编辑 */}
      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <Label className="text-base font-medium">
            {isEditing ? '手动编辑' : '正文预览'}
          </Label>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button variant="ghost" size="sm" onClick={() => setIsEditing(false)}>
                  <X className="mr-1 h-3.5 w-3.5" />
                  取消
                </Button>
                <Button size="sm" onClick={() => setIsEditing(false)}>
                  <Save className="mr-1 h-3.5 w-3.5" />
                  保存
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={!canRegenerate}
                  onClick={() => setArticleRetries(articleRetries + 1)}
                >
                  <RefreshCw className="mr-1 h-3.5 w-3.5" />
                  重新生成
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setIsEditing(true)}>
                  <Edit3 className="mr-1 h-3.5 w-3.5" />
                  手动编辑
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="p-4">
          {isEditing ? (
            <div className="space-y-2">
              <textarea
                value={article}
                onChange={(e) => setArticle(e.target.value)}
                rows={12}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              />
              <div className="flex justify-end">
                <span className="text-xs text-muted-foreground">
                  {article.length} 字
                </span>
              </div>
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {article ? (
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {article}
                </div>
              ) : (
                <p className="text-muted-foreground">暂无正文内容</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={prevStep}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          上一步
        </Button>
        <Button onClick={nextStep} disabled={!article}>
          下一步
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
