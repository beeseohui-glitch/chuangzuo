'use client';

import { useCreateStore } from '@/stores/create-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AgentStatus } from '@/components/shared/agent-status';
import { cn } from '@/lib/utils';
import { Check, RefreshCw, ArrowRight, ArrowLeft, Pencil } from 'lucide-react';

export function StepTitle() {
  const {
    titleOptions, selectedTitles, customTitle, titleRetries, maxTitleRetries,
    isProcessing, toggleTitle, setCustomTitle, setTitleRetries,
    nextStep, prevStep,
  } = useCreateStore();

  const canRefresh = titleRetries < maxTitleRetries;
  const canProceed = selectedTitles.length > 0 || customTitle.trim().length > 0;

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <AgentStatus status="running" agentName="标题Agent" label="正在生成标题..." />
        <p className="text-sm text-muted-foreground">运用8大标题策略，为你生成吸睛标题</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between">
          <Label className="text-base font-medium">选择标题（最多2个）</Label>
          <span className="text-xs text-muted-foreground">
            已选 {selectedTitles.length}/2 · 换一批次数 {titleRetries}/{maxTitleRetries}
          </span>
        </div>

        <div className="mt-4 space-y-3">
          {titleOptions.map((option, index) => {
            const isSelected = selectedTitles.includes(option.title);
            return (
              <button
                key={index}
                onClick={() => toggleTitle(option.title)}
                className={cn(
                  'w-full rounded-lg border-2 p-4 text-left transition-all',
                  isSelected
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/30'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium">{option.title}</p>
                    <div className="mt-2 flex items-center gap-3">
                      <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                        {option.strategy}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        评分: {option.score}/10
                      </span>
                    </div>
                    <p className="mt-1.5 text-xs text-muted-foreground">{option.reason}</p>
                  </div>
                  <div
                    className={cn(
                      'flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition-colors',
                      isSelected
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-muted-foreground/30'
                    )}
                  >
                    {isSelected && <Check className="h-3.5 w-3.5" />}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* 换一批按钮 */}
        <Button
          variant="outline"
          className="mt-4 w-full"
          disabled={!canRefresh}
          onClick={() => setTitleRetries(titleRetries + 1)}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          {canRefresh ? '换一批' : '已达重试上限'}
        </Button>
      </div>

      {/* 自定义标题 */}
      <div className="border-t border-border pt-6">
        <Label htmlFor="custom-title" className="flex items-center gap-2">
          <Pencil className="h-4 w-4" />
          自定义标题
        </Label>
        <Input
          id="custom-title"
          placeholder="输入你自己的标题..."
          value={customTitle}
          onChange={(e) => setCustomTitle(e.target.value)}
          className="mt-1.5"
        />
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={prevStep}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          上一步
        </Button>
        <Button onClick={nextStep} disabled={!canProceed}>
          下一步
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
