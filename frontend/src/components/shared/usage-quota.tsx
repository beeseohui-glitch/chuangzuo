'use client';

import { cn } from '@/lib/utils';

interface UsageQuotaProps {
  used: number;
  total: number;
  label?: string;
  className?: string;
}

export function UsageQuota({ used, total, label, className }: UsageQuotaProps) {
  const percentage = total > 0 ? Math.min((used / total) * 100, 100) : 0;
  const isWarning = percentage >= 80;
  const isCritical = percentage >= 95;

  return (
    <div className={cn('space-y-1.5', className)}>
      {label && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">{label}</span>
          <span
            className={cn(
              'font-medium',
              isCritical && 'text-destructive',
              isWarning && !isCritical && 'text-yellow-500',
              !isWarning && 'text-muted-foreground'
            )}
          >
            {used}/{total}
          </span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-300',
            isCritical && 'bg-destructive',
            isWarning && !isCritical && 'bg-yellow-500',
            !isWarning && 'bg-primary'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
