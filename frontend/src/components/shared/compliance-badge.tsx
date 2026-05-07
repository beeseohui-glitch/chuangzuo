'use client';

import { cn } from '@/lib/utils';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

export type ComplianceStatusType = 'passed' | 'needs_revision' | 'failed';

interface ComplianceBadgeProps {
  status: ComplianceStatusType;
  className?: string;
  showIcon?: boolean;
  showLabel?: boolean;
}

const statusConfig: Record<
  ComplianceStatusType,
  { icon: typeof CheckCircle2; label: string; className: string }
> = {
  passed: {
    icon: CheckCircle2,
    label: '合规',
    className: 'bg-green-500/10 text-green-500 border-green-500/20',
  },
  needs_revision: {
    icon: AlertTriangle,
    label: '需修改',
    className: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  },
  failed: {
    icon: XCircle,
    label: '不合规',
    className: 'bg-destructive/10 text-destructive border-destructive/20',
  },
};

// 兼容后端中文状态值
const STATUS_MAP: Record<string, ComplianceStatusType> = {
  '通过': 'passed',
  'passed': 'passed',
  '需修改': 'needs_revision',
  'needs_revision': 'needs_revision',
  '不合规': 'failed',
  'failed': 'failed',
};

export function ComplianceBadge({
  status,
  className,
  showIcon = true,
  showLabel = true,
}: ComplianceBadgeProps) {
  const mappedStatus = STATUS_MAP[status] || 'passed';
  const config = statusConfig[mappedStatus];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        config.className,
        className
      )}
    >
      {showIcon && <Icon className="h-3.5 w-3.5" />}
      {showLabel && config.label}
    </span>
  );
}

export function ComplianceSummary({
  passed,
  needsRevision,
  failed,
  className,
}: {
  passed: number;
  needsRevision: number;
  failed: number;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-3', className)}>
      {passed > 0 && (
        <span className="inline-flex items-center gap-1 text-xs text-green-500">
          <CheckCircle2 className="h-3.5 w-3.5" />
          {passed}
        </span>
      )}
      {needsRevision > 0 && (
        <span className="inline-flex items-center gap-1 text-xs text-yellow-500">
          <AlertTriangle className="h-3.5 w-3.5" />
          {needsRevision}
        </span>
      )}
      {failed > 0 && (
        <span className="inline-flex items-center gap-1 text-xs text-destructive">
          <XCircle className="h-3.5 w-3.5" />
          {failed}
        </span>
      )}
    </div>
  );
}
