'use client';

import { useCreateStore } from '@/stores/create-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ComplianceBadge } from '@/components/shared/compliance-badge';
import { AgentStatus } from '@/components/shared/agent-status';
import { cn } from '@/lib/utils';
import {
  Check, X, Plus, AlertTriangle, AlertCircle, Info,
  ArrowRight, ArrowLeft, CheckCircle2,
} from 'lucide-react';

export function StepTags() {
  const {
    tags, customTag, complianceReport, complianceOverrides, taskStatus, isProcessing,
    toggleTag, addCustomTag, removeTag, setCustomTag,
    setComplianceOverride, confirmP2Decision, nextStep, prevStep,
  } = useCreateStore();

  const isAwaitingP2Decision = taskStatus === 'awaiting_p2_decision';

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <div className="flex gap-4">
          <AgentStatus status="running" agentName="标签Agent" label="生成标签..." />
          <AgentStatus status="running" agentName="合规Agent" label="合规检查..." />
        </div>
        <p className="text-sm text-muted-foreground">两个Agent并行执行中</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        {/* 左侧：标签 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">标签推荐</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 已选标签 */}
            <div>
              <Label className="text-xs text-muted-foreground">已选标签</Label>
              <div className="mt-2 flex flex-wrap gap-2 min-h-[40px]">
                {tags.length > 0 ? (
                  tags.map((tag) => (
                    <Badge key={tag} variant="default" className="gap-1 pr-1">
                      #{tag}
                      <button
                        onClick={() => removeTag(tag)}
                        className="ml-1 rounded-full p-0.5 hover:bg-primary-foreground/20"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">点击下方标签添加</span>
                )}
              </div>
            </div>

            {/* 推荐标签 */}
            <div>
              <Label className="text-xs text-muted-foreground">推荐标签（点击选择）</Label>
              <div className="mt-2 flex flex-wrap gap-2">
                {getRecommendedTags().map((tag) => (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    className={cn(
                      'rounded-full border px-3 py-1 text-xs transition-colors',
                      tags.includes(tag)
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-border hover:border-primary/50'
                    )}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            </div>

            {/* 自定义标签 */}
            <div>
              <Label className="text-xs text-muted-foreground">自定义标签</Label>
              <div className="mt-1.5 flex gap-2">
                <Input
                  placeholder="输入标签..."
                  value={customTag}
                  onChange={(e) => setCustomTag(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addCustomTag(customTag)}
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => addCustomTag(customTag)}
                  disabled={!customTag.trim()}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 右侧：合规报告 */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">合规报告</CardTitle>
              {complianceReport && (
                <ComplianceBadge status={complianceReport.status} />
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!complianceReport ? (
              <p className="text-sm text-muted-foreground">暂无合规数据</p>
            ) : (
              <div className="space-y-4">
                {/* P0 - 严重问题 */}
                {complianceReport.p0_issues?.length > 0 && (
                  <div className="space-y-3">
                    <IssueSection
                      title="P0 严重问题（必须修改）"
                      icon={<AlertCircle className="h-4 w-4 text-destructive" />}
                      issues={complianceReport.p0_issues}
                      overrides={complianceOverrides}
                      onOverride={setComplianceOverride}
                      variant="destructive"
                    />
                    {/* P0 决策区域 */}
                    {isAwaitingP2Decision && (
                      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                        <p className="text-sm font-medium text-destructive mb-3">
                          检测到严重合规问题，请选择处理方式：
                        </p>
                        <div className="flex gap-3">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => confirmP2Decision(false)}
                            disabled={isProcessing}
                          >
                            <X className="mr-1 h-4 w-4" />
                            拒绝发布
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => confirmP2Decision(true)}
                            disabled={isProcessing}
                          >
                            <Check className="mr-1 h-4 w-4" />
                            忽略问题继续
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* P1 - 重要问题 */}
                {complianceReport.p1_issues?.length > 0 && (
                  <IssueSection
                    title="P1 重要问题（建议修改）"
                    icon={<AlertTriangle className="h-4 w-4 text-yellow-500" />}
                    issues={complianceReport.p1_issues}
                    overrides={complianceOverrides}
                    onOverride={setComplianceOverride}
                    variant="warning"
                  />
                )}

                {/* P2 - 轻微问题 */}
                {complianceReport.p2_issues?.length > 0 && (
                  <IssueSection
                    title="P2 轻微问题"
                    icon={<Info className="h-4 w-4 text-blue-500" />}
                    issues={complianceReport.p2_issues}
                    overrides={complianceOverrides}
                    onOverride={setComplianceOverride}
                    variant="info"
                  />
                )}

                {/* 建议 */}
                {complianceReport.suggestions?.length > 0 && (
                  <div className="rounded-lg bg-muted p-3">
                    <Label className="text-xs text-muted-foreground">优化建议</Label>
                    <ul className="mt-2 space-y-1">
                      {complianceReport.suggestions.map((s, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-500" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 全部通过 */}
                {(complianceReport.p0_issues?.length || 0) === 0 &&
                  (complianceReport.p1_issues?.length || 0) === 0 &&
                  (complianceReport.p2_issues?.length || 0) === 0 && (
                  <div className="flex flex-col items-center py-6 text-green-500">
                    <CheckCircle2 className="h-12 w-12" />
                    <p className="mt-2 font-medium">全部通过</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={prevStep} disabled={isAwaitingP2Decision}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          上一步
        </Button>
        <Button onClick={nextStep} disabled={tags.length === 0 || isAwaitingP2Decision || isProcessing}>
          {isProcessing ? '处理中...' : '下一步'}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function IssueSection({
  title,
  icon,
  issues,
  overrides,
  onOverride,
  variant,
}: {
  title: string;
  icon: React.ReactNode;
  issues: Array<{ type: string; description: string; location?: string }>;
  overrides: Record<string, 'pass' | 'modify' | 'delete'>;
  onOverride: (type: string, action: 'pass' | 'modify' | 'delete') => void;
  variant: 'destructive' | 'warning' | 'info';
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <Label className="text-xs font-medium">{title}</Label>
      </div>
      <div className="space-y-2">
        {issues.map((issue, i) => {
          const override = overrides[issue.type];
          return (
            <div
              key={i}
              className={cn(
                'rounded-lg border p-3 text-sm',
                variant === 'destructive' && 'border-destructive/30 bg-destructive/5',
                variant === 'warning' && 'border-yellow-500/30 bg-yellow-500/5',
                variant === 'info' && 'border-blue-500/30 bg-blue-500/5'
              )}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-medium">{issue.type}</span>
                  <p className="mt-1 text-muted-foreground">{issue.description}</p>
                  {issue.location && (
                    <p className="mt-1 text-xs text-muted-foreground">位置: {issue.location}</p>
                  )}
                </div>
              </div>
              {/* P2 问题支持交互 */}
              {variant === 'info' && (
                <div className="mt-2 flex gap-2">
                  <Button
                    variant={override === 'pass' ? 'default' : 'outline'}
                    size="xs"
                    onClick={() => onOverride(issue.type, 'pass')}
                  >
                    <Check className="mr-1 h-3 w-3" /> 通过
                  </Button>
                  <Button
                    variant={override === 'modify' ? 'default' : 'outline'}
                    size="xs"
                    onClick={() => onOverride(issue.type, 'modify')}
                  >
                    修改
                  </Button>
                  <Button
                    variant={override === 'delete' ? 'destructive' : 'outline'}
                    size="xs"
                    onClick={() => onOverride(issue.type, 'delete')}
                  >
                    删除
                  </Button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function getRecommendedTags(): string[] {
  return [
    '护肝', '养生', '健康生活', '熬夜党', '加班族',
    '好物推荐', '种草', '真实测评', '日常保养', '职场人',
  ];
}
